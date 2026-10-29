# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Vendas: orçamentos (PDF, WhatsApp, conversão em pedido) e fila de produção."""

from __future__ import annotations

import webbrowser
from collections.abc import Callable
from decimal import Decimal

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from makerprice3d.core import gestao
from makerprice3d.core.numeros import formatar_moeda, formatar_numero, para_decimal, texto_valido
from makerprice3d.services import negocio
from makerprice3d.services.exportacao import html_orcamento
from makerprice3d.ui.cadastro import Acao, Campo, Especificacao, PaginaCadastro, Registro
from makerprice3d.ui.contexto import Contexto
from makerprice3d.ui.pdf import html_para_pdf
from makerprice3d.ui.widgets import CampoNumerico

STATUS_ORCAMENTO = (
    ("rascunho", "Rascunho"),
    ("enviado", "Enviado"),
    ("aprovado", "Aprovado"),
    ("recusado", "Recusado"),
    ("convertido", "Virou pedido"),
)
CORES_STATUS = {
    "aguardando": "#9aa3b2",
    "imprimindo": "#7c5cff",
    "lavando": "#00c2ff",
    "curando": "#ffbe0b",
    "acabamento": "#ff7afc",
    "pronto": "#3ddc84",
    "entregue": "#4cff9d",
}


def _validade_dias(registro: Registro) -> int:
    return int(para_decimal(registro.get("validade_dias"), Decimal(7)))


def _vencido(registro: Registro) -> bool:
    return registro.get("status") in ("rascunho", "enviado") and gestao.orcamento_vencido(
        negocio.data_do_registro(registro), _validade_dias(registro)
    )


class DialogoOrcamento(QDialog):
    """Editor de orçamento: itens, desconto, frete, validade, prazo e pagamento."""

    def __init__(
        self,
        contexto: Contexto,
        registro: Registro | None = None,
        itens_iniciais: list[gestao.ItemOrcamento] | None = None,
        item_da_calculadora: Callable[[], gestao.ItemOrcamento | None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.contexto = contexto
        self.registro = registro or {}
        self._item_calc = item_da_calculadora
        self.setWindowTitle(f"Orçamento nº {registro['id']}" if registro else "Novo orçamento")
        self.setMinimumSize(760, 600)
        banco = contexto.banco
        self.itens: list[gestao.ItemOrcamento] = (
            negocio.itens_do_registro(self.registro) if registro else list(itens_iniciais or [])
        )
        layout = QVBoxLayout(self)
        topo = QFormLayout()
        self.cliente = QComboBox()
        self.cliente.addItem("— sem cliente —", None)
        for cliente in banco.listar("clientes"):
            self.cliente.addItem(cliente["nome"], cliente["id"])
        self.cliente.setCurrentIndex(max(0, self.cliente.findData(self.registro.get("cliente_id"))))
        self.data = QDateEdit()
        self.data.setCalendarPopup(True)
        self.data.setDisplayFormat("dd/MM/yyyy")
        data = QDate.fromString(str(self.registro.get("data", ""))[:10], "yyyy-MM-dd")
        self.data.setDate(data if data.isValid() else QDate.currentDate())
        self.validade = QSpinBox()
        self.validade.setRange(0, 365)
        self.validade.setSuffix(" dias")
        self.validade.setValue(
            int(para_decimal(self.registro.get("validade_dias") or banco.config("validade_orcamento_dias"), Decimal(7)))
        )
        self.prazo = QLineEdit(self.registro.get("prazo_entrega", "") or "")
        self.prazo.setPlaceholderText("Ex.: 7 dias úteis após aprovação")
        self.pagamento = QLineEdit(self.registro.get("pagamento", "") or "")
        self.pagamento.setPlaceholderText("Ex.: 50% na aprovação + 50% na entrega (Pix)")
        self.desconto = CampoNumerico("desconto", "Desconto em % sobre os itens.")
        self.desconto.definir_texto(self.registro.get("desconto_percentual", "") or "")
        self.frete = CampoNumerico("frete", "Frete cobrado do cliente.")
        self.frete.definir_texto(self.registro.get("frete", "") or "")
        self.status = QComboBox()
        for valor, rotulo in STATUS_ORCAMENTO:
            self.status.addItem(rotulo, valor)
        self.status.setCurrentIndex(max(0, self.status.findData(self.registro.get("status", "rascunho"))))
        linha1 = QHBoxLayout()
        linha1.addWidget(self.cliente, 2)
        linha1.addWidget(QLabel("Emissão"))
        linha1.addWidget(self.data)
        linha1.addWidget(QLabel("Validade"))
        linha1.addWidget(self.validade)
        topo.addRow("Cliente", linha1)
        topo.addRow("Prazo de entrega", self.prazo)
        topo.addRow("Pagamento", self.pagamento)
        linha2 = QHBoxLayout()
        linha2.addWidget(QLabel("Desconto (%)"))
        linha2.addWidget(self.desconto)
        linha2.addWidget(QLabel("Frete (R$)"))
        linha2.addWidget(self.frete)
        linha2.addWidget(QLabel("Status"))
        linha2.addWidget(self.status)
        topo.addRow("", linha2)
        layout.addLayout(topo)

        barra = QHBoxLayout()
        adicionar = QPushButton("Adicionar item")
        menu = QMenu(adicionar)
        menu.addAction("Peça da calculadora", self._add_calculadora)
        menu.addAction("Produto do catálogo…", self._add_produto)
        menu.addAction("Kit/combo…", self._add_kit)
        menu.addAction("Item avulso", self._add_avulso)
        adicionar.setMenu(menu)
        remover = QPushButton("Remover item")
        remover.clicked.connect(self._remover)
        barra.addWidget(adicionar)
        barra.addWidget(remover)
        barra.addStretch(1)
        layout.addLayout(barra)
        self.tabela = QTableWidget(0, 5)
        self.tabela.setHorizontalHeaderLabels(["Descrição", "Qtd", "Preço unit. (R$)", "Custo unit. (R$)", "Total"])
        self.tabela.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.itemChanged.connect(self._celula_editada)
        layout.addWidget(self.tabela, 1)
        self.observacoes = QPlainTextEdit(self.registro.get("observacoes", "") or "")
        self.observacoes.setPlaceholderText("Observações para o cliente")
        self.observacoes.setFixedHeight(60)
        layout.addWidget(self.observacoes)
        self.totais = QLabel()
        self.totais.setObjectName("metricaValor")
        self.totais.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.totais)
        self.desconto.textChanged.connect(self._mostrar_totais)
        self.frete.textChanged.connect(self._mostrar_totais)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        botoes.button(QDialogButtonBox.StandardButton.Save).setText("Salvar")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botoes.accepted.connect(self._validar)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)
        self._mostrar()

    # itens
    def _add_calculadora(self) -> None:
        item = self._item_calc() if self._item_calc else None
        if item:
            self.itens.append(item)
            self._mostrar()

    def _escolher(self, tabela: str, titulo: str) -> Registro | None:
        registros = self.contexto.banco.listar(tabela)
        if not registros:
            QMessageBox.information(self, titulo, "Nada cadastrado ainda.")
            return None
        dialogo = QDialog(self)
        dialogo.setWindowTitle(titulo)
        formulario = QFormLayout(dialogo)
        combo = QComboBox()
        for r in registros:
            combo.addItem(r["nome"], r["id"])
        formulario.addRow(titulo, combo)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botoes.accepted.connect(dialogo.accept)
        botoes.rejected.connect(dialogo.reject)
        formulario.addRow(botoes)
        if dialogo.exec():
            return self.contexto.banco.obter(tabela, combo.currentData())
        return None

    def _add_produto(self) -> None:
        produto = self._escolher("produtos", "Produto")
        if produto:
            self.itens.append(negocio.item_de_produto(produto))
            self._mostrar()

    def _add_kit(self) -> None:
        kit = self._escolher("kits", "Kit")
        if kit:
            self.itens.extend(negocio.itens_de_kit(self.contexto.banco, kit))
            self._mostrar()

    def _add_avulso(self) -> None:
        self.itens.append(gestao.ItemOrcamento("Item avulso", 1, Decimal(0)))
        self._mostrar()

    def _remover(self) -> None:
        linha = self.tabela.currentRow()
        if 0 <= linha < len(self.itens):
            del self.itens[linha]
            self._mostrar()

    def _mostrar(self) -> None:
        self.tabela.blockSignals(True)
        self.tabela.setRowCount(len(self.itens))
        for linha, item in enumerate(self.itens):
            valores = (
                item.descricao,
                str(item.quantidade),
                formatar_numero(item.preco_unitario),
                formatar_numero(item.custo_unitario),
                formatar_moeda(item.total),
            )
            for coluna, texto in enumerate(valores):
                celula = QTableWidgetItem(texto)
                if coluna == 4:
                    celula.setFlags(celula.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if coluna:
                    celula.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tabela.setItem(linha, coluna, celula)
        self.tabela.blockSignals(False)
        self._mostrar_totais()

    def _celula_editada(self, celula: QTableWidgetItem) -> None:
        linha, coluna = celula.row(), celula.column()
        if not 0 <= linha < len(self.itens):
            return
        item = self.itens[linha]
        texto = celula.text()
        dados = gestao.item_para_dict(item)
        if coluna == 0:
            dados["descricao"] = texto
        elif coluna == 1:
            dados["quantidade"] = max(1, int(para_decimal(texto, Decimal(1))))
        elif coluna in (2, 3) and texto_valido(texto):
            dados["preco_unitario" if coluna == 2 else "custo_unitario"] = str(para_decimal(texto))
        self.itens[linha] = gestao.item_de_dict(dados)
        self._mostrar()

    def _totais(self) -> gestao.TotaisOrcamento:
        return gestao.totais_orcamento(self.itens, para_decimal(self.desconto.text()), para_decimal(self.frete.text()))

    def _mostrar_totais(self) -> None:
        t = self._totais()
        partes = [f"Subtotal {formatar_moeda(t.subtotal)}"]
        if t.desconto:
            partes.append(f"Desconto −{formatar_moeda(t.desconto)}")
        if t.frete:
            partes.append(f"Frete {formatar_moeda(t.frete)}")
        partes.append(f"Total {formatar_moeda(t.total)}")
        cor = "#3ddc84" if t.lucro >= 0 else "#ff5c6c"
        self.totais.setText(
            "  ·  ".join(partes)
            + f"<br><span style='font-size:10pt;color:{cor}'>Lucro estimado {formatar_moeda(t.lucro)}</span>"
        )

    def _validar(self) -> None:
        if not self.itens:
            QMessageBox.information(self, "Orçamento", "Adicione pelo menos um item.")
            return
        if not (self.desconto.valido and self.frete.valido):
            return
        self.accept()

    def dados(self) -> Registro:
        """Registro pronto para o banco."""
        return {
            "cliente_id": self.cliente.currentData(),
            "data": self.data.date().toString("yyyy-MM-dd"),
            "validade_dias": str(self.validade.value()),
            "prazo_entrega": self.prazo.text().strip(),
            "pagamento": self.pagamento.text().strip(),
            "desconto_percentual": self.desconto.text().strip(),
            "frete": self.frete.text().strip(),
            "itens": [gestao.item_para_dict(i) for i in self.itens],
            "status": self.status.currentData(),
            "observacoes": self.observacoes.toPlainText().strip(),
        }


class PaginaOrcamentos(PaginaCadastro):
    """Lista de orçamentos com PDF, WhatsApp e conversão em pedido."""

    def __init__(
        self,
        contexto: Contexto,
        item_da_calculadora: Callable[[], gestao.ItemOrcamento | None],
        parent: QWidget | None = None,
    ) -> None:
        self._item_calc = item_da_calculadora
        spec = Especificacao(
            "orcamentos",
            "Orçamentos",
            "Monte orçamentos com validade, prazo e pagamento; "
            "exporte em PDF, envie pelo WhatsApp e converta em pedido.",
            [
                Campo("id", "Nº", calcular=lambda r: str(r["id"])),
                Campo("cliente_id", "Cliente", "ref:clientes"),
                Campo("data", "Emissão", "data"),
                Campo(
                    "validade",
                    "Válido até",
                    calcular=lambda r: (
                        gestao.validade(negocio.data_do_registro(r), _validade_dias(r)).strftime("%d/%m/%Y")
                        + (" (vencido)" if _vencido(r) else "")
                    ),
                ),
                Campo("total", "Total", calcular=lambda r: formatar_moeda(negocio.totais_do_orcamento(r).total)),
                Campo("status", "Status", "escolha", opcoes=STATUS_ORCAMENTO),
                Campo("prazo_entrega", "Prazo"),
            ],
            acoes=[
                Acao("PDF", self.exportar_pdf),
                Acao("WhatsApp", self.whatsapp),
                Acao("Converter em pedido", self.converter, primario=True),
            ],
            destacar=lambda r: "#ff5c6c" if _vencido(r) else None,
        )
        super().__init__(contexto, spec, parent)

    def novo(self, itens: list[gestao.ItemOrcamento] | None = None) -> None:
        dialogo = DialogoOrcamento(self.contexto, None, itens or [], self._item_calc, self)
        if dialogo.exec():
            self.contexto.banco.inserir("orcamentos", dialogo.dados())
            self.contexto.avisar("orcamentos")

    def editar(self) -> None:
        registro = self.selecionado()
        if not registro:
            return
        dialogo = DialogoOrcamento(self.contexto, registro, None, self._item_calc, self)
        if dialogo.exec():
            self.contexto.banco.atualizar("orcamentos", registro["id"], dialogo.dados())
            self.contexto.avisar("orcamentos")

    def _cliente(self, registro: Registro) -> Registro:
        ident = registro.get("cliente_id")
        return (self.contexto.banco.obter("clientes", ident) if ident else None) or {}

    def html(self, registro: Registro) -> str:
        """HTML do orçamento (usado no PDF)."""
        emissao = negocio.data_do_registro(registro)
        return html_orcamento(
            numero=registro["id"],
            loja=self.contexto.banco.config("loja_nome") or "Maker Price 3D",
            cliente=self._cliente(registro).get("nome", ""),
            itens=negocio.itens_do_registro(registro),
            totais=negocio.totais_do_orcamento(registro),
            emissao=emissao,
            validade_ate=gestao.validade(emissao, _validade_dias(registro)),
            prazo_entrega=registro.get("prazo_entrega", ""),
            pagamento=registro.get("pagamento", ""),
            observacoes=registro.get("observacoes", ""),
            contato_loja=self.contexto.banco.config("loja_telefone"),
        )

    def exportar_pdf(self, registro: Registro | None) -> None:
        if not registro:
            return
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", f"orcamento-{registro['id']}.pdf", "PDF (*.pdf)")
        if caminho:
            destino = html_para_pdf(self.html(registro), caminho)
            QMessageBox.information(self, "PDF", f"Orçamento salvo em:\n{destino}")

    def whatsapp(self, registro: Registro | None) -> None:
        if not registro:
            return
        cliente = self._cliente(registro)
        emissao = negocio.data_do_registro(registro)
        texto = gestao.texto_orcamento(
            registro["id"],
            cliente.get("nome", ""),
            negocio.itens_do_registro(registro),
            negocio.totais_do_orcamento(registro),
            gestao.validade(emissao, _validade_dias(registro)),
            registro.get("prazo_entrega", ""),
            registro.get("pagamento", ""),
            self.contexto.banco.config("loja_nome") or "Maker Price 3D",
        )
        webbrowser.open(gestao.link_whatsapp(cliente.get("telefone", ""), texto))
        if registro.get("status") == "rascunho":
            self.contexto.banco.atualizar("orcamentos", registro["id"], {"status": "enviado"})
            self.contexto.avisar("orcamentos")

    def converter(self, registro: Registro | None) -> None:
        if not registro:
            return
        if registro.get("pedido_id"):
            QMessageBox.information(self, "Pedido", f"Este orçamento já é o pedido nº {registro['pedido_id']}.")
            return
        pedido = negocio.converter_em_pedido(self.contexto.banco, registro["id"])
        self.contexto.avisar("")
        QMessageBox.information(self, "Pedido", f"Pedido nº {pedido} criado e colocado na fila (Aguardando).")


class PaginaProducao(PaginaCadastro):
    """Fila de produção dos pedidos."""

    def __init__(self, contexto: Contexto, parent: QWidget | None = None) -> None:
        status = [(s, gestao.ROTULOS_STATUS[s]) for s in gestao.STATUS_PRODUCAO]
        spec = Especificacao(
            "pedidos",
            "Pedidos e produção",
            "Fila: Aguardando → Imprimindo → Lavando → Curando → Acabamento → Pronto → Entregue. "
            "Ao entrar em Imprimindo o estoque é baixado (uma vez).",
            [
                Campo("id", "Nº", calcular=lambda r: str(r["id"]), no_formulario=False),
                Campo("cliente_id", "Cliente", "ref:clientes"),
                Campo("data", "Data", "data"),
                Campo(
                    "itens_txt",
                    "Itens",
                    no_formulario=False,
                    calcular=lambda r: ", ".join(
                        f"{i.quantidade}× {i.descricao}" for i in negocio.itens_do_registro(r)
                    ),
                ),
                Campo("status", "Status", "escolha", opcoes=status, padrao="aguardando", no_formulario=False),
                Campo("total", "Total (R$)", "moeda"),
                Campo("custo", "Custo (R$)", "moeda"),
                Campo("impressora_id", "Impressora", "ref:impressoras", "Usada no payback por impressora."),
                Campo("prazo_entrega", "Prazo"),
                Campo("pagamento", "Pagamento", na_lista=False),
                Campo("observacoes", "Observações", "multilinha", na_lista=False),
            ],
            acoes=[Acao("Avançar status ▶", self.avancar, primario=True), Acao("Definir status…", self.definir)],
            destacar=lambda r: CORES_STATUS.get(str(r.get("status"))),
        )
        super().__init__(contexto, spec, parent)
        self.contagem = QLabel()
        self.contagem.setObjectName("suave")
        self.extra.addWidget(self.contagem)
        self.atualizar()

    def atualizar(self) -> None:
        super().atualizar()
        if hasattr(self, "contagem"):
            partes = []
            for s in gestao.STATUS_PRODUCAO:
                n = sum(1 for r in self.registros if r.get("status") == s)
                partes.append(f"<span style='color:{CORES_STATUS[s]}'>●</span> {gestao.ROTULOS_STATUS[s]}: <b>{n}</b>")
            self.contagem.setText("   ".join(partes))

    def _salvar(self, dados: Registro, ident: int | None) -> int:
        if ident is None:
            dados = {**dados, "status": "aguardando"}
        return super()._salvar(dados, ident)

    def _mudar(self, registro: Registro, status: str) -> None:
        consumo = negocio.mudar_status_pedido(self.contexto.banco, registro["id"], status)
        self.contexto.avisar("")
        if consumo:
            baixos = gestao.estoque_baixo(self.contexto.banco.listar("estoque"))
            if baixos:
                QMessageBox.warning(
                    self, "Estoque baixo", "Estoque baixado. Abaixo do mínimo: " + ", ".join(b["nome"] for b in baixos)
                )

    def avancar(self, registro: Registro | None) -> None:
        if registro:
            self._mudar(registro, gestao.proximo_status(str(registro.get("status") or "aguardando")))

    def definir(self, registro: Registro | None) -> None:
        if not registro:
            return
        menu = QMenu(self)
        for s in gestao.STATUS_PRODUCAO:
            acao = menu.addAction(gestao.ROTULOS_STATUS[s])
            acao.setData(s)
        escolhida = menu.exec(self.cursor().pos())
        if escolhida:
            self._mudar(registro, escolhida.data())
