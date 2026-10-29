# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Telas de cadastro: perfis (impressoras, resinas, canais), clientes, estoque, catálogo e equipamentos."""

from __future__ import annotations

import webbrowser
from collections.abc import Callable
from datetime import date
from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from makerprice3d.core import gestao
from makerprice3d.core.numeros import formatar_moeda, formatar_numero, formatar_percentual, para_decimal
from makerprice3d.services import negocio
from makerprice3d.services.banco import agora
from makerprice3d.ui.cadastro import Acao, Campo, Especificacao, PaginaCadastro, Registro
from makerprice3d.ui.contexto import Contexto
from makerprice3d.ui.widgets import CampoNumerico

COR_ALERTA = "#ff5c6c"


# --- Perfis ------------------------------------------------------------------------------
def spec_impressoras() -> Especificacao:
    return Especificacao(
        "impressoras",
        "Impressoras",
        "Perfis de impressora: escolha na calculadora para preencher LCD, FEP, depreciação e energia.",
        [
            Campo("nome", "Nome", obrigatorio=True, dica="Ex.: Saturn 3 Ultra"),
            Campo("potencia_w", "Potência (W)", "numero", "Consumo médio imprimindo."),
            Campo("preco", "Preço (R$)", "moeda", "Valor pago na impressora (depreciação e payback)."),
            Campo("vida_util_h", "Vida útil (h)", "numero", "Horas estimadas de uso da impressora."),
            Campo("preco_lcd", "Preço LCD (R$)", "moeda"),
            Campo("vida_lcd_h", "Vida LCD (h)", "numero", "Usado no alerta de troca."),
            Campo("preco_fep", "Preço FEP (R$)", "moeda"),
            Campo("durabilidade_fep", "Durabilidade FEP (impressões)", "numero", "Usado no alerta de troca."),
            Campo("preco_mesa", "Preço plataforma (R$)", "moeda", na_lista=False),
            Campo("vida_mesa_h", "Vida plataforma (h)", "numero", na_lista=False),
            Campo("data_compra", "Data da compra", "data", "Para o cálculo de payback."),
            Campo("observacoes", "Observações", "multilinha", na_lista=False),
        ],
    )


def spec_resinas() -> Especificacao:
    return Especificacao(
        "resinas",
        "Resinas",
        "Biblioteca de resinas. O preço por kg é calculado pelo preço do litro e a densidade.",
        [
            Campo("nome", "Nome", obrigatorio=True),
            Campo("marca", "Marca"),
            Campo("tipo", "Tipo", dica="Ex.: Standard, ABS-like, Water washable, 8K"),
            Campo("cor", "Cor"),
            Campo("preco_litro", "Preço por litro/frasco 1L (R$)", "moeda"),
            Campo("densidade", "Densidade (g/ml)", "numero", "Vazio = 1,1 g/ml (valor típico).", padrao="1,1"),
            Campo(
                "preco_kg",
                "Preço por kg",
                no_formulario=False,
                calcular=lambda r: formatar_moeda(
                    para_decimal(r.get("preco_litro"))
                    / (para_decimal(r.get("densidade"), Decimal("1.1")) or Decimal("1.1"))
                ),
            ),
            Campo("observacoes", "Observações", "multilinha", na_lista=False),
        ],
    )


def spec_canais() -> Especificacao:
    return Especificacao(
        "canais",
        "Canais de venda",
        "Taxas marcadas com “(exemplo)” são apenas pontos de partida: confira as taxas atuais de cada canal.",
        [
            Campo("nome", "Nome", obrigatorio=True),
            Campo("taxa_percentual", "Taxa (%)", "numero"),
            Campo("taxa_fixa", "Taxa fixa (R$)", "moeda"),
            Campo("observacoes", "Observações", "multilinha"),
        ],
    )


class PaginaPerfis(QWidget):
    """Abas com impressoras, resinas e canais."""

    def __init__(self, contexto: Contexto, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        abas = QTabWidget()
        for spec in (spec_impressoras(), spec_resinas(), spec_canais()):
            abas.addTab(PaginaCadastro(contexto, spec), spec.titulo)
        layout.addWidget(abas)


# --- Clientes ------------------------------------------------------------------------------
class PaginaClientes(PaginaCadastro):
    """Clientes com atalho para o WhatsApp."""

    def __init__(self, contexto: Contexto, parent: QWidget | None = None) -> None:
        spec = Especificacao(
            "clientes",
            "Clientes",
            "Cadastro de clientes para orçamentos e pedidos.",
            [
                Campo("nome", "Nome", obrigatorio=True),
                Campo("telefone", "WhatsApp/Telefone", dica="Com DDD. Ex.: (11) 91234-5678"),
                Campo("email", "E-mail"),
                Campo("cidade", "Cidade"),
                Campo("observacoes", "Observações", "multilinha"),
            ],
            acoes=[Acao("Abrir WhatsApp", self._whatsapp)],
        )
        super().__init__(contexto, spec, parent)

    def _whatsapp(self, registro: Registro | None) -> None:
        if not registro or not registro.get("telefone"):
            QMessageBox.information(self, "WhatsApp", "Cadastre o telefone do cliente.")
            return
        webbrowser.open(gestao.link_whatsapp(registro["telefone"], f"Olá, {registro['nome']}!"))


# --- Estoque -------------------------------------------------------------------------------
class DialogoMovimento(QDialog):
    """Entrada ou saída manual no estoque."""

    def __init__(self, item: Registro, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Movimentar — {item['nome']}")
        formulario = QFormLayout(self)
        self.tipo = QComboBox()
        self.tipo.addItem("Entrada (compra)", 1)
        self.tipo.addItem("Saída (uso/perda)", -1)
        self.quantidade = CampoNumerico("quantidade", f"Quantidade em {item.get('unidade') or 'unidades'}")
        self.motivo = QLineEdit()
        self.motivo.setPlaceholderText("Ex.: compra, perda, ajuste de inventário")
        formulario.addRow("Tipo", self.tipo)
        formulario.addRow(f"Quantidade ({item.get('unidade') or 'un'})", self.quantidade)
        formulario.addRow("Motivo", self.motivo)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botoes.accepted.connect(lambda: self.accept() if self.quantidade.valido and self.quantidade.text() else None)
        botoes.rejected.connect(self.reject)
        formulario.addRow(botoes)

    def valor(self) -> Decimal:
        """Quantidade com sinal."""
        return abs(para_decimal(self.quantidade.text())) * self.tipo.currentData()


def _estoque_baixo(registro: Registro) -> bool:
    minimo = str(registro.get("minimo") or "").strip()
    return bool(minimo) and para_decimal(registro.get("quantidade")) <= para_decimal(minimo)


class PaginaEstoque(PaginaCadastro):
    """Estoque com baixa automática pelos pedidos e alerta de mínimo."""

    def __init__(self, contexto: Contexto, parent: QWidget | None = None) -> None:
        categorias = [(c, c.upper() if c in ("ipa",) else c.capitalize()) for c in gestao.CATEGORIAS_ESTOQUE]
        spec = Especificacao(
            "estoque",
            "Estoque",
            "Resina, IPA, luvas, filtros e embalagens. A baixa é automática quando o pedido entra em “Imprimindo”.",
            [
                Campo("nome", "Item", obrigatorio=True),
                Campo("categoria", "Categoria", "escolha", opcoes=categorias, padrao="resina"),
                Campo("unidade", "Unidade", dica="Para resina use g (o consumo vem do peso das peças).", padrao="un"),
                Campo("quantidade", "Quantidade", "numero"),
                Campo("minimo", "Mínimo (alerta)", "numero"),
                Campo("custo_unitario", "Custo unitário (R$)", "moeda"),
                Campo(
                    "consumo_por_peca",
                    "Consumo por peça",
                    "numero",
                    "Itens que não são resina: quanto sai por peça (ex.: 0,5 luva).",
                ),
                Campo("resina_id", "Resina (perfil)", "ref:resinas", "Liga o estoque à resina usada nos produtos."),
            ],
            acoes=[Acao("Entrada/Saída", self._movimentar, primario=False)],
            destacar=lambda r: COR_ALERTA if _estoque_baixo(r) else None,
        )
        super().__init__(contexto, spec, parent)
        self.alerta = QLabel("")
        self.alerta.setObjectName("alerta")
        self.alerta.setWordWrap(True)
        self.extra.addWidget(self.alerta)
        self.atualizar()

    def atualizar(self) -> None:
        super().atualizar()
        if hasattr(self, "alerta"):
            baixos = gestao.estoque_baixo(self.registros)
            self.alerta.setVisible(bool(baixos))
            self.alerta.setText("Estoque baixo: " + ", ".join(r["nome"] for r in baixos))

    def _movimentar(self, registro: Registro | None) -> None:
        if not registro:
            return
        dialogo = DialogoMovimento(registro, self)
        if dialogo.exec():
            negocio.ajustar_estoque(
                self.contexto.banco, registro["id"], dialogo.valor(), dialogo.motivo.text() or "Manual"
            )
            self.contexto.avisar("estoque")


# --- Catálogo e kits ---------------------------------------------------------------------
class DialogoItensKit(QDialog):
    """Escolhe os produtos e quantidades de um kit."""

    def __init__(self, contexto: Contexto, kit: Registro, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.contexto = contexto
        self.setWindowTitle(f"Itens do kit — {kit['nome']}")
        self.setMinimumSize(520, 380)
        self.itens: list[dict] = [dict(i) for i in (kit.get("itens") or [])]
        self.desconto = para_decimal(kit.get("desconto_percentual"))
        layout = QVBoxLayout(self)
        linha = QHBoxLayout()
        self.produto = QComboBox()
        for produto in contexto.banco.listar("produtos"):
            self.produto.addItem(
                f"{produto['nome']} — {formatar_moeda(para_decimal(produto.get('preco')))}", produto["id"]
            )
        self.qtd = QSpinBox()
        self.qtd.setRange(1, 999)
        adicionar = QPushButton("Adicionar")
        adicionar.clicked.connect(self._adicionar)
        remover = QPushButton("Remover")
        remover.clicked.connect(self._remover)
        linha.addWidget(self.produto, 1)
        linha.addWidget(self.qtd)
        linha.addWidget(adicionar)
        linha.addWidget(remover)
        layout.addLayout(linha)
        self.tabela = QTableWidget(0, 3)
        self.tabela.setHorizontalHeaderLabels(["Produto", "Qtd", "Preço"])
        self.tabela.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tabela, 1)
        self.total = QLabel()
        self.total.setObjectName("metricaValor")
        layout.addWidget(self.total)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)
        self._mostrar()

    def _adicionar(self) -> None:
        ident = self.produto.currentData()
        if ident is None:
            return
        for item in self.itens:
            if item["produto_id"] == ident:
                item["quantidade"] = int(item["quantidade"]) + self.qtd.value()
                break
        else:
            self.itens.append({"produto_id": ident, "quantidade": self.qtd.value()})
        self._mostrar()

    def _remover(self) -> None:
        linha = self.tabela.currentRow()
        if 0 <= linha < len(self.itens):
            del self.itens[linha]
            self._mostrar()

    def _mostrar(self) -> None:
        self.tabela.setRowCount(len(self.itens))
        for linha, item in enumerate(self.itens):
            produto = self.contexto.banco.obter("produtos", item["produto_id"]) or {}
            self.tabela.setItem(linha, 0, QTableWidgetItem(produto.get("nome", "(removido)")))
            self.tabela.setItem(linha, 1, QTableWidgetItem(str(item["quantidade"])))
            self.tabela.setItem(linha, 2, QTableWidgetItem(formatar_moeda(para_decimal(produto.get("preco")))))
        cheio, final = negocio.preco_do_kit(
            self.contexto.banco, {"itens": self.itens, "desconto_percentual": str(self.desconto)}
        )
        self.total.setText(f"Avulso: {formatar_moeda(cheio)}  →  Kit: {formatar_moeda(final)}")


class PaginaCatalogo(QWidget):
    """Produtos salvos (com foto, escala e preço) e kits/combos com desconto."""

    def __init__(
        self,
        contexto: Contexto,
        abrir_projeto: Callable[[Registro], None],
        orcar: Callable[[list], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.contexto = contexto
        self._abrir_projeto = abrir_projeto
        self._orcar = orcar
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        abas = QTabWidget()
        produtos = Especificacao(
            "produtos",
            "Catálogo de produtos",
            "Use “Salvar no catálogo” na calculadora para guardar a peça com preço, custo e o projeto completo.",
            [
                Campo("foto", "Foto", "foto"),
                Campo("nome", "Nome", obrigatorio=True),
                Campo("escala", "Escala", "escolha", opcoes=[(e, e) for e in ("", *gestao.ESCALAS)]),
                Campo("preco", "Preço (R$)", "moeda"),
                Campo("custo", "Custo (R$)", "moeda"),
                Campo("peso_g", "Peso (g)", "numero"),
                Campo("tempo_h", "Tempo (h)", "numero"),
                Campo("resina_id", "Resina", "ref:resinas"),
                Campo("impressora_id", "Impressora", "ref:impressoras", na_lista=False),
                Campo("observacoes", "Observações", "multilinha", na_lista=False),
            ],
            acoes=[
                Acao("Abrir na calculadora", self._abrir),
                Acao("Orçar", lambda r: r and self._orcar([negocio.item_de_produto(r)]), primario=True),
            ],
        )
        self.pagina_produtos = PaginaCadastro(contexto, produtos)
        self.pagina_produtos.tabela.setIconSize(self.pagina_produtos.tabela.iconSize() * 2)
        abas.addTab(self.pagina_produtos, "Produtos")
        kits = Especificacao(
            "kits",
            "Kits e combos",
            "Agrupe produtos com desconto (ex.: esquadrão de 5 miniaturas).",
            [
                Campo("nome", "Nome", obrigatorio=True),
                Campo("desconto_percentual", "Desconto (%)", "numero"),
                Campo(
                    "qtd_itens",
                    "Peças",
                    no_formulario=False,
                    calcular=lambda r: str(sum(int(i.get("quantidade", 0)) for i in (r.get("itens") or []))),
                ),
                Campo(
                    "preco_kit",
                    "Preço do kit",
                    no_formulario=False,
                    calcular=lambda r: formatar_moeda(negocio.preco_do_kit(contexto.banco, r)[1]),
                ),
                Campo("observacoes", "Observações", "multilinha"),
            ],
            acoes=[
                Acao("Itens do kit…", self._itens_kit),
                Acao(
                    "Orçar",
                    lambda r: r and self._orcar(negocio.itens_de_kit(contexto.banco, r)),
                    primario=True,
                ),
            ],
        )
        self.pagina_kits = PaginaCadastro(contexto, kits)
        abas.addTab(self.pagina_kits, "Kits/Combos")
        layout.addWidget(abas)
        contexto.dados_alterados.connect(lambda t: t == "produtos" and self.pagina_kits.atualizar())

    def _abrir(self, registro: Registro | None) -> None:
        if registro and registro.get("projeto"):
            self._abrir_projeto(registro)
        elif registro:
            QMessageBox.information(self, "Catálogo", "Este produto não tem projeto salvo.")

    def _itens_kit(self, registro: Registro | None) -> None:
        if not registro:
            return
        dialogo = DialogoItensKit(self.contexto, registro, self)
        if dialogo.exec():
            self.contexto.banco.atualizar("kits", registro["id"], {"itens": dialogo.itens})
            self.contexto.avisar("kits")


# --- Equipamentos ------------------------------------------------------------------------
class PaginaEquipamentos(QWidget):
    """Contadores de LCD/FEP, histórico de manutenção e registro de falhas."""

    def __init__(self, contexto: Contexto, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.contexto = contexto
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        abas = QTabWidget()
        abas.addTab(self._aba_uso(), "Uso e alertas")
        motivos = [("", "—")] + [(m, m.capitalize() if m != "FEP" else m) for m in gestao.MOTIVOS_FALHA]
        impressoes = Especificacao(
            "impressoes",
            "Impressões e falhas",
            "Registre cada impressão (sucesso ou falha). "
            "Isso alimenta os contadores do LCD/FEP e a taxa de falha real.",
            [
                Campo("data", "Data", "data"),
                Campo("impressora_id", "Impressora", "ref:impressoras", obrigatorio=True),
                Campo("resina_id", "Resina", "ref:resinas"),
                Campo("horas", "Horas", "numero"),
                Campo("camadas", "Camadas", "numero"),
                Campo("sucesso", "Sucesso", "booleano", padrao="1"),
                Campo("motivo_falha", "Motivo da falha", "escolha", opcoes=motivos),
                Campo("observacoes", "Observações", "multilinha"),
            ],
            destacar=lambda r: COR_ALERTA if not r.get("sucesso") else None,
        )
        self.pagina_impressoes = PaginaCadastro(contexto, impressoes)
        self.resumo_falhas = QLabel()
        self.resumo_falhas.setObjectName("suave")
        self.resumo_falhas.setWordWrap(True)
        self.pagina_impressoes.extra.addWidget(self.resumo_falhas)
        abas.addTab(self.pagina_impressoes, "Impressões e falhas")
        manutencoes = Especificacao(
            "manutencoes",
            "Manutenções",
            "Histórico de manutenção. Uma “troca” de LCD/FEP zera o contador dessa peça.",
            [
                Campo("data", "Data", "data"),
                Campo("impressora_id", "Impressora", "ref:impressoras", obrigatorio=True),
                Campo(
                    "tipo",
                    "Tipo",
                    "escolha",
                    opcoes=[
                        ("troca", "Troca de peça"),
                        ("limpeza", "Limpeza"),
                        ("ajuste", "Ajuste/calibração"),
                        ("outro", "Outro"),
                    ],
                    padrao="troca",
                ),
                Campo(
                    "peca", "Peça", "escolha", opcoes=[("lcd", "LCD"), ("fep", "FEP"), ("outra", "Outra")], padrao="fep"
                ),
                Campo("custo", "Custo (R$)", "moeda"),
                Campo("observacoes", "Observações", "multilinha"),
            ],
        )
        abas.addTab(PaginaCadastro(contexto, manutencoes), "Manutenções")
        layout.addWidget(abas)
        contexto.dados_alterados.connect(lambda _: self.atualizar())
        self.atualizar()

    def _aba_uso(self) -> QWidget:
        pagina = QWidget()
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(18, 16, 18, 16)
        titulo = QLabel("Uso desde a última troca")
        titulo.setObjectName("tituloCard")
        layout.addWidget(titulo)
        sub = QLabel("LCD em horas e FEP em impressões (mesmas unidades da v1.x). Alerta a partir de 90% da vida útil.")
        sub.setObjectName("suave")
        layout.addWidget(sub)
        self.alertas = QLabel()
        self.alertas.setObjectName("alerta")
        self.alertas.setWordWrap(True)
        layout.addWidget(self.alertas)
        self.tabela_uso = QTableWidget(0, 7)
        self.tabela_uso.setHorizontalHeaderLabels(
            ["Impressora", "LCD (h)", "LCD %", "FEP (impressões)", "FEP %", "Camadas", "Taxa de falha"]
        )
        self.tabela_uso.horizontalHeader().setStretchLastSection(True)
        self.tabela_uso.verticalHeader().setVisible(False)
        layout.addWidget(self.tabela_uso, 1)
        linha = QHBoxLayout()
        for peca in ("lcd", "fep"):
            botao = QPushButton(f"Registrar troca de {peca.upper()}")
            botao.clicked.connect(lambda _=False, p=peca: self._registrar_troca(p))
            linha.addWidget(botao)
        linha.addStretch(1)
        layout.addLayout(linha)
        return pagina

    def _registrar_troca(self, peca: str) -> None:
        linha = self.tabela_uso.currentRow()
        if linha < 0:
            QMessageBox.information(self, "Troca", "Selecione a impressora na tabela.")
            return
        ident = self.tabela_uso.item(linha, 0).data(Qt.ItemDataRole.UserRole)
        self.contexto.banco.inserir(
            "manutencoes", {"impressora_id": ident, "data": agora(), "tipo": "troca", "peca": peca}
        )
        self.contexto.avisar("manutencoes")

    def atualizar(self) -> None:
        """Recalcula contadores e alertas."""
        banco = self.contexto.banco
        impressoras = banco.listar("impressoras")
        impressoes = banco.listar("impressoes")
        self.tabela_uso.setRowCount(len(impressoras))
        for linha, imp in enumerate(impressoras):
            uso = negocio.uso_da_impressora(banco, imp["id"])
            taxa = gestao.taxa_falha_medida(impressoes, imp["id"])
            valores = (
                imp["nome"],
                formatar_numero(uso["lcd"].horas, 1),
                formatar_percentual(uso["lcd"].percentual, 0) if uso["lcd"].limite else "—",
                str(uso["fep"].impressoes),
                formatar_percentual(uso["fep"].percentual, 0) if uso["fep"].limite else "—",
                str(uso["lcd"].camadas),
                f"{formatar_percentual(taxa.percentual, 1)} ({taxa.falhas}/{taxa.total})" if taxa.total else "—",
            )
            for coluna, texto in enumerate(valores):
                item = QTableWidgetItem(texto)
                item.setData(Qt.ItemDataRole.UserRole, imp["id"])
                peca = "lcd" if coluna in (1, 2) else "fep" if coluna in (3, 4) else ""
                if peca and uso[peca].alerta:
                    item.setForeground(Qt.GlobalColor.red)
                self.tabela_uso.setItem(linha, coluna, item)
        self.tabela_uso.resizeColumnsToContents()
        alertas = negocio.alertas_de_troca(banco)
        self.alertas.setVisible(bool(alertas))
        self.alertas.setText("\n".join(alertas))
        geral = gestao.taxa_falha_medida(impressoes)
        if geral.total:
            motivos = ", ".join(f"{m}: {q}" for m, q in geral.motivos.items()) or "—"
            self.resumo_falhas.setText(
                f"Taxa de falha geral: {formatar_percentual(geral.percentual, 1)} "
                f"({geral.falhas} de {geral.total}). Motivos: {motivos}"
            )
        else:
            self.resumo_falhas.setText("Nenhuma impressão registrada ainda.")


def hoje_iso() -> str:
    """Data de hoje em ISO."""
    return date.today().isoformat()
