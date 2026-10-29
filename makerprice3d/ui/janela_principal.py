# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Janela principal: navegação lateral, menus, atalhos, salvar/abrir, autosave e backup."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from PySide6.QtCore import QLocale, QSize, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QColor, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from makerprice3d import __app_name__, __version__
from makerprice3d.core import gestao
from makerprice3d.core.numeros import arredondar, para_decimal
from makerprice3d.core.projeto import ProjetoInvalidoError, migrar, obter_valor, projeto_vazio
from makerprice3d.services import arquivos, backup, caminhos, negocio
from makerprice3d.services.exportacao import exportar_resultado_csv, linhas_resultado
from makerprice3d.ui import tema
from makerprice3d.ui.contexto import Contexto
from makerprice3d.ui.dialogos import (
    DialogoCalculadoraEnergia,
    DialogoConfiguracoes,
    DialogoCotacao,
    DialogoSimulacao,
    DialogoSobre,
)
from makerprice3d.ui.pagina_calculadora import PaginaCalculadora
from makerprice3d.ui.paginas import (
    PaginaCatalogo,
    PaginaClientes,
    PaginaEquipamentos,
    PaginaEstoque,
    PaginaPerfis,
)
from makerprice3d.ui.painel import PaginaPainel
from makerprice3d.ui.pdf import html_para_pdf
from makerprice3d.ui.vendas import PaginaOrcamentos, PaginaProducao

FILTRO_ABRIR = "Projetos Maker Price 3D (*.mp3d *.json);;Projeto v2 (*.mp3d);;Projeto antigo v1.x (*.json)"
FILTRO_SALVAR = "Projeto Maker Price 3D (*.mp3d)"

#: Configuração global -> campo do projeto novo.
PADROES_DO_PROJETO = {
    "valor_hora": "mao_de_obra.ganho_por_hora",
    "margem_padrao": "lucro.estado",
    "acrescimo_premium": "venda.acrescimo_premium",
    "impostos_percentual": "venda.impostos_percentual",
    "regime_tributario": "tributos.regime",
    "das_mensal": "tributos.das_mensal",
    "vendas_mes": "tributos.vendas_mes",
    "custo_fixo_mensal": "custos_fixos.mensal",
    "horas_maquina_mes": "custos_fixos.horas_maquina_mes",
    "tarifa_kwh": "extras.tarifa_kwh",
}


class DialogoCatalogo(QDialog):
    """Pergunta nome, escala e foto antes de salvar no catálogo."""

    def __init__(self, nome: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Salvar no catálogo")
        self.setMinimumWidth(420)
        formulario = QFormLayout(self)
        self.nome = QLineEdit(nome)
        self.escala = QComboBox()
        self.escala.addItems(["", *gestao.ESCALAS])
        self.foto = QLineEdit()
        self.foto.setReadOnly(True)
        escolher = QPushButton("Escolher foto…")
        escolher.clicked.connect(self._escolher)
        linha = QHBoxLayout()
        linha.addWidget(self.foto, 1)
        linha.addWidget(escolher)
        formulario.addRow("Nome", self.nome)
        formulario.addRow("Escala", self.escala)
        formulario.addRow("Foto", linha)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        botoes.accepted.connect(lambda: self.accept() if self.nome.text().strip() else None)
        botoes.rejected.connect(self.reject)
        formulario.addRow(botoes)

    def _escolher(self) -> None:
        arquivo, _ = QFileDialog.getOpenFileName(self, "Foto", "", "Imagens (*.png *.jpg *.jpeg *.webp *.bmp)")
        if arquivo:
            self.foto.setText(arquivo)


class JanelaPrincipal(QMainWindow):
    """Janela do Maker Price 3D."""

    PAGINAS = (
        ("calculadora", "Calculadora"),
        ("orcamentos", "Orçamentos"),
        ("producao", "Pedidos e produção"),
        ("catalogo", "Catálogo e kits"),
        ("clientes", "Clientes"),
        ("estoque", "Estoque"),
        ("equipamentos", "Equipamentos"),
        ("perfis", "Impressoras, resinas e canais"),
        ("painel", "Painel"),
    )

    def __init__(self, contexto: Contexto | None = None, recuperar_autosave: bool = True) -> None:
        super().__init__()
        QLocale.setDefault(QLocale(QLocale.Language.Portuguese, QLocale.Country.Brazil))
        self.contexto = contexto or Contexto()
        self.caminho: Path | None = None
        self.autosave = arquivos.Autosave(self.contexto.pasta_autosave)
        self.setWindowTitle(__app_name__)
        icone = caminhos.pasta_assets() / "favicon.ico"
        if not icone.exists():
            icone = caminhos.pasta_assets() / "icon.png"
        if icone.exists():
            self.setWindowIcon(QIcon(str(icone)))
        self.resize(1440, 900)
        self.setMinimumSize(QSize(980, 620))
        self._montar()
        self._menus()
        self.aplicar_tema(self.contexto.tema)
        self.novo_projeto(perguntar=False)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._autosalvar)
        self._configurar_autosave()
        self.contexto.dados_alterados.connect(self._ao_mudar_dados)
        self._backup_diario()
        if recuperar_autosave:
            QTimer.singleShot(300, self._oferecer_recuperacao)

    # ------------------------------------------------------------------ montagem
    def _montar(self) -> None:
        central = QWidget()
        central.setObjectName("fundo")
        raiz = QHBoxLayout(central)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)
        lateral = QWidget()
        lateral.setObjectName("barraLateral")
        lateral.setFixedWidth(250)
        coluna = QVBoxLayout(lateral)
        coluna.setContentsMargins(12, 18, 12, 12)
        coluna.setSpacing(4)
        marca = QLabel("Maker Price 3D")
        marca.setObjectName("marca")
        coluna.addWidget(marca)
        versao = QLabel(f"v{__version__} · resina")
        versao.setObjectName("suave")
        coluna.addWidget(versao)
        coluna.addSpacing(14)
        self.pilha = QStackedWidget()
        self.grupo_nav = QButtonGroup(self)
        self.grupo_nav.setExclusive(True)
        self.calculadora = PaginaCalculadora(self.contexto)
        self.calculadora.projeto_alterado.connect(lambda: self.setWindowModified(True))
        self.calculadora.pedir_catalogo.connect(self.salvar_no_catalogo)
        self.calculadora.pedir_orcamento.connect(self.orcar_peca_atual)
        self.calculadora.pedir_simulacao.connect(self.abrir_simulacao)
        self.calculadora.pedir_cotacao.connect(self.abrir_cotacao)
        self.orcamentos = PaginaOrcamentos(self.contexto, self.item_da_calculadora)
        self.paginas: dict[str, QWidget] = {
            "calculadora": self.calculadora,
            "orcamentos": self.orcamentos,
            "producao": PaginaProducao(self.contexto),
            "catalogo": PaginaCatalogo(self.contexto, self.abrir_produto, self._orcar_itens),
            "clientes": PaginaClientes(self.contexto),
            "estoque": PaginaEstoque(self.contexto),
            "equipamentos": PaginaEquipamentos(self.contexto),
            "perfis": PaginaPerfis(self.contexto),
            "painel": PaginaPainel(self.contexto),
        }
        self.botoes_nav: dict[str, QPushButton] = {}
        for indice, (chave, rotulo) in enumerate(self.PAGINAS):
            botao = QPushButton(rotulo)
            botao.setObjectName("navegacao")
            botao.setCheckable(True)
            botao.clicked.connect(lambda _=False, i=indice: self.pilha.setCurrentIndex(i))
            self.grupo_nav.addButton(botao, indice)
            coluna.addWidget(botao)
            self.pilha.addWidget(self.paginas[chave])
            self.botoes_nav[chave] = botao
        self.botoes_nav["calculadora"].setChecked(True)
        coluna.addStretch(1)
        self.botao_tema = QPushButton("Alternar tema")
        self.botao_tema.setObjectName("navegacao")
        self.botao_tema.clicked.connect(self.alternar_tema)
        coluna.addWidget(self.botao_tema)
        raiz.addWidget(lateral)
        raiz.addWidget(self.pilha, 1)
        self.setCentralWidget(central)
        self.statusBar().showMessage("Pronto.")

    def ir_para(self, chave: str) -> None:
        """Mostra uma página."""
        indice = [c for c, _ in self.PAGINAS].index(chave)
        self.pilha.setCurrentIndex(indice)
        self.botoes_nav[chave].setChecked(True)

    def _acao(self, menu, texto: str, funcao, atalho: QKeySequence | str | None = None) -> QAction:
        acao = QAction(texto, self)
        if atalho:
            acao.setShortcut(QKeySequence(atalho))
        acao.triggered.connect(funcao)
        menu.addAction(acao)
        return acao

    def _menus(self) -> None:
        barra = self.menuBar()
        arquivo = barra.addMenu("&Arquivo")
        self._acao(arquivo, "Novo projeto", lambda: self.novo_projeto(), QKeySequence.StandardKey.New)
        self._acao(arquivo, "Abrir…", lambda: self.abrir(), QKeySequence.StandardKey.Open)
        self.menu_recentes = arquivo.addMenu("Abrir recente")
        self.menu_recentes.aboutToShow.connect(self._montar_recentes)
        arquivo.addSeparator()
        self._acao(arquivo, "Salvar", lambda: self.salvar(), QKeySequence.StandardKey.Save)
        self._acao(arquivo, "Salvar como…", lambda: self.salvar_como(), "Ctrl+Shift+S")
        arquivo.addSeparator()
        self._acao(arquivo, "Exportar cálculo (CSV)…", self.exportar_csv)
        self._acao(arquivo, "Exportar cálculo (PDF)…", self.exportar_pdf_calculo)
        self._acao(arquivo, "Exportar todos os dados (.zip)…", self.exportar_tudo)
        self._acao(arquivo, "Fazer backup agora", self.backup_agora)
        arquivo.addSeparator()
        self._acao(arquivo, "Sair", self.close, QKeySequence.StandardKey.Quit)

        ferramentas = barra.addMenu("&Ferramentas")
        self._acao(ferramentas, "Calculadora de kWh", self.abrir_kwh)
        self._acao(ferramentas, "Cotação em outras moedas", self.abrir_cotacao)
        self._acao(ferramentas, "Simulação de cenários", self.abrir_simulacao)
        ferramentas.addSeparator()
        self._acao(ferramentas, "Configurações…", self.abrir_configuracoes, "Ctrl+,")

        exibir = barra.addMenu("&Exibir")
        self._acao(exibir, "Alternar tema claro/escuro", self.alternar_tema, "Ctrl+T")
        for indice, (chave, rotulo) in enumerate(self.PAGINAS):
            self._acao(exibir, rotulo, lambda _=False, c=chave: self.ir_para(c), f"Ctrl+{indice + 1}")

        ajuda = barra.addMenu("Aj&uda")
        self._acao(ajuda, "Sobre o Maker Price 3D", lambda: DialogoSobre(self).exec())

    def _montar_recentes(self) -> None:
        self.menu_recentes.clear()
        recentes = self.contexto.banco.recentes()
        if not recentes:
            acao = self.menu_recentes.addAction("(vazio)")
            acao.setEnabled(False)
            return
        for caminho in recentes:
            self.menu_recentes.addAction(caminho, lambda c=caminho: self.abrir(c))
        self.menu_recentes.addSeparator()
        self.menu_recentes.addAction("Limpar lista", self._limpar_recentes)

    def _limpar_recentes(self) -> None:
        for caminho in self.contexto.banco.recentes():
            self.contexto.banco.remover_recente(caminho)

    # ------------------------------------------------------------------ tema
    def aplicar_tema(self, nome: str) -> None:
        """Aplica o tema claro ou escuro."""
        paleta = tema.paleta(nome)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(tema.folha_de_estilo(paleta))
        self.calculadora.grafico.cor_vazio = QColor(paleta.borda)
        self.calculadora.grafico.update()

    def alternar_tema(self) -> None:
        """Troca entre claro e escuro e lembra a escolha."""
        novo = "claro" if self.contexto.tema == "escuro" else "escuro"
        self.contexto.banco.definir_config("tema", novo)
        self.aplicar_tema(novo)
        self.contexto.tema_alterado.emit(novo)

    # ------------------------------------------------------------------ projeto
    def _padroes(self) -> dict[str, Any]:
        padroes = {}
        for chave, caminho in PADROES_DO_PROJETO.items():
            valor = self.contexto.banco.config(chave)
            if valor not in (None, ""):
                padroes[caminho] = valor
        return padroes

    def _atualizar_titulo(self) -> None:
        nome = self.caminho.name if self.caminho else "Sem Título"
        self.setWindowTitle(f"{nome}[*] — {__app_name__}")

    def _confirmar_descartar(self) -> bool:
        """Pergunta o que fazer com alterações não salvas. ``False`` = cancelar."""
        if not self.isWindowModified():
            return True
        resposta = QMessageBox.question(
            self,
            "Alterações não salvas",
            "O projeto tem alterações não salvas. Deseja salvar antes?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if resposta == QMessageBox.StandardButton.Save:
            return self.salvar()
        return resposta == QMessageBox.StandardButton.Discard

    def _carregar(self, projeto: dict, caminho: Path | None, modificado: bool = False) -> None:
        self.caminho = caminho
        self.calculadora.carregar(projeto)
        self.setWindowModified(modificado)
        self._atualizar_titulo()
        self.ir_para("calculadora")

    def novo_projeto(self, perguntar: bool = True) -> None:
        """Ctrl+N: começa um projeto em branco com os padrões das Configurações."""
        if perguntar and not self._confirmar_descartar():
            return
        self._carregar(projeto_vazio(self._padroes()), None)
        self.statusBar().showMessage("Novo projeto.", 4000)

    def abrir(self, caminho: str | Path | None = None) -> None:
        """Ctrl+O: abre um .mp3d (ou um .json antigo, que é migrado)."""
        if not self._confirmar_descartar():
            return
        if not caminho:
            caminho, _ = QFileDialog.getOpenFileName(self, "Abrir projeto", "", FILTRO_ABRIR)
            if not caminho:
                return
        try:
            carregado = arquivos.abrir_projeto(caminho)
        except FileNotFoundError:
            self.contexto.banco.remover_recente(caminho)
            QMessageBox.warning(self, "Abrir", f"Arquivo não encontrado:\n{caminho}")
            return
        except (ProjetoInvalidoError, ValueError, OSError) as erro:
            QMessageBox.critical(self, "Abrir", f"Não foi possível abrir o projeto:\n{erro}")
            return
        if carregado.sugerir_salvar_como:
            self._carregar(carregado.projeto, None, modificado=True)
            self.statusBar().showMessage(
                "Projeto da versão 1.x convertido. Use Salvar para gravar no novo formato .mp3d.", 10000
            )
        else:
            self._carregar(carregado.projeto, carregado.caminho)
            self.contexto.banco.adicionar_recente(carregado.caminho)
            self.statusBar().showMessage(f"Aberto: {carregado.caminho}", 5000)

    def salvar(self) -> bool:
        """Ctrl+S."""
        if self.caminho is None:
            return self.salvar_como()
        return self._gravar(self.caminho)

    def salvar_como(self) -> bool:
        """Ctrl+Shift+S."""
        nome = obter_valor(self.calculadora.projeto, "meta.nome", "") or "projeto"
        sugestao = str(self.caminho or Path.home() / f"{nome}{arquivos.EXTENSAO}")
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar projeto", sugestao, FILTRO_SALVAR)
        if not caminho:
            return False
        return self._gravar(Path(caminho))

    def _gravar(self, caminho: Path) -> bool:
        invalidos = self.calculadora.campos_invalidos()
        if invalidos:
            resposta = QMessageBox.question(
                self,
                "Campos inválidos",
                f"{len(invalidos)} campo(s) têm valores inválidos (contados como zero). Salvar mesmo assim?",
            )
            if resposta != QMessageBox.StandardButton.Yes:
                return False
        try:
            destino = arquivos.salvar_projeto(self.calculadora.projeto, caminho)
        except OSError as erro:
            QMessageBox.critical(self, "Salvar", f"Não foi possível salvar:\n{erro}")
            return False
        self.caminho = destino
        self.setWindowModified(False)
        self._atualizar_titulo()
        self.autosave.limpar()
        self.contexto.banco.adicionar_recente(destino)
        self.statusBar().showMessage(f"Salvo em {destino}", 5000)
        return True

    # ------------------------------------------------------------------ autosave e backup
    def _configurar_autosave(self) -> None:
        segundos = int(para_decimal(self.contexto.banco.config("autosave_segundos"), para_decimal("60")))
        self._timer.stop()
        if segundos > 0:
            self._timer.start(max(10, segundos) * 1000)

    def _autosalvar(self) -> None:
        if self.isWindowModified():
            try:
                self.autosave.gravar(self.calculadora.projeto, self.caminho)
                self.statusBar().showMessage("Salvamento automático feito.", 2500)
            except OSError:
                self.statusBar().showMessage("Falha no salvamento automático.", 5000)

    def _oferecer_recuperacao(self) -> None:
        pendentes = self.autosave.pendentes()
        if not pendentes:
            return
        mais_novo = pendentes[0]
        resposta = QMessageBox.question(
            self,
            "Recuperar trabalho",
            "Encontramos um projeto que não foi salvo (o programa fechou inesperadamente). Deseja recuperá-lo?",
        )
        if resposta == QMessageBox.StandardButton.Yes:
            try:
                projeto, original = arquivos.Autosave.ler(mais_novo)
            except (OSError, ValueError, ProjetoInvalidoError):
                QMessageBox.warning(self, "Recuperar", "O arquivo de recuperação está corrompido.")
            else:
                self._carregar(projeto, Path(original) if original else None, modificado=True)
        for arquivo in pendentes:
            arquivos.Autosave.descartar(arquivo)

    def _backup_diario(self) -> None:
        try:
            destino = backup.backup_automatico(self.contexto.banco, self.contexto.pasta_backups)
        except OSError:
            return
        if destino:
            self.statusBar().showMessage(f"Backup automático: {destino.name}", 4000)

    def backup_agora(self) -> None:
        """Backup manual do banco de dados."""
        manter = int(para_decimal(self.contexto.banco.config("backups_manter"), para_decimal("10")))
        destino = backup.fazer_backup(self.contexto.banco, self.contexto.pasta_backups, manter)
        QMessageBox.information(self, "Backup", f"Backup criado em:\n{destino}")

    def exportar_tudo(self) -> None:
        """Exporta banco + JSON + fotos num .zip."""
        caminho, _ = QFileDialog.getSaveFileName(self, "Exportar dados", "makerprice3d-dados.zip", "ZIP (*.zip)")
        if caminho:
            destino = backup.exportar_tudo(self.contexto.banco, Path(caminho), self.contexto.pasta_fotos)
            QMessageBox.information(self, "Exportar", f"Dados exportados em:\n{destino}")

    # ------------------------------------------------------------------ exportação
    def exportar_csv(self) -> None:
        """Composição do preço em CSV."""
        caminho, _ = QFileDialog.getSaveFileName(self, "Exportar CSV", "calculo.csv", "CSV (*.csv)")
        if caminho and self.calculadora.resultado:
            exportar_resultado_csv(caminho, self.calculadora.projeto, self.calculadora.resultado)
            self.statusBar().showMessage(f"CSV salvo em {caminho}", 5000)

    def html_calculo(self) -> str:
        """Resumo do cálculo em HTML."""
        linhas = linhas_resultado(self.calculadora.projeto, self.calculadora.resultado)
        corpo = "".join(
            f"<tr><td>{html.escape(a)}</td><td align='right'>{html.escape(b)}</td></tr>" for a, b in linhas[2:]
        )
        return (
            "<html><body style='font-family:Arial'>"
            f"<h2>{html.escape(linhas[0][1])}</h2><p>Maker Price 3D v{__version__}</p>"
            "<table width='100%' cellspacing='0' cellpadding='4' border='1' style='border-collapse:collapse'>"
            f"<tr><th align='left'>Item</th><th align='right'>Valor (R$)</th></tr>{corpo}</table>"
            "</body></html>"
        )

    def exportar_pdf_calculo(self) -> None:
        """Composição do preço em PDF."""
        caminho, _ = QFileDialog.getSaveFileName(self, "Exportar PDF", "calculo.pdf", "PDF (*.pdf)")
        if caminho and self.calculadora.resultado:
            destino = html_para_pdf(self.html_calculo(), caminho)
            self.statusBar().showMessage(f"PDF salvo em {destino}", 5000)

    # ------------------------------------------------------------------ integrações
    def item_da_calculadora(self) -> gestao.ItemOrcamento | None:
        """A peça da calculadora como item de orçamento (preço sugerido)."""
        r = self.calculadora.resultado
        if r is None:
            return None
        projeto = self.calculadora.projeto
        resina = obter_valor(projeto, "perfil.resina_id", None)
        return gestao.ItemOrcamento(
            descricao=obter_valor(projeto, "meta.nome", "") or "Peça personalizada",
            quantidade=r.quantidade,
            preco_unitario=arredondar(r.preco_sugerido),
            custo_unitario=arredondar(r.total_gasto),
            peso_g=para_decimal(obter_valor(projeto, "material.peso", "")),
            resina_id=int(resina) if resina not in (None, "") else None,
        )

    def _orcar_itens(self, itens: list[gestao.ItemOrcamento]) -> None:
        self.ir_para("orcamentos")
        self.orcamentos.novo(itens)

    def orcar_peca_atual(self) -> None:
        """Cria um orçamento com a peça da calculadora."""
        item = self.item_da_calculadora()
        if item:
            self._orcar_itens([item])

    def salvar_no_catalogo(self) -> None:
        """Guarda a peça atual no catálogo."""
        nome = obter_valor(self.calculadora.projeto, "meta.nome", "")
        dialogo = DialogoCatalogo(nome, self)
        if dialogo.exec():
            negocio.salvar_no_catalogo(
                self.contexto.banco,
                self.calculadora.projeto,
                dialogo.nome.text().strip(),
                dialogo.escala.currentText(),
                dialogo.foto.text(),
                self.contexto.pasta_fotos,
            )
            self.contexto.avisar("produtos")
            self.statusBar().showMessage("Peça salva no catálogo.", 4000)

    def abrir_produto(self, produto: dict) -> None:
        """Abre o projeto de um produto do catálogo na calculadora."""
        if not self._confirmar_descartar():
            return
        try:
            projeto, _ = migrar(produto["projeto"])
        except (ProjetoInvalidoError, ValueError):
            QMessageBox.warning(self, "Catálogo", "O projeto salvo neste produto está inválido.")
            return
        self._carregar(projeto, None)

    def abrir_kwh(self) -> None:
        DialogoCalculadoraEnergia(self, self.contexto.banco.config("tarifa_kwh")).exec()

    def abrir_cotacao(self) -> None:
        r = self.calculadora.resultado
        DialogoCotacao(self, r.preco_sugerido if r else para_decimal("0"), self.contexto.cache_cotacao).exec()

    def abrir_simulacao(self) -> None:
        DialogoSimulacao(self.calculadora.projeto, self).exec()

    def abrir_configuracoes(self) -> None:
        if DialogoConfiguracoes(self.contexto.banco, self).exec():
            self._configurar_autosave()
            self.contexto.avisar("")

    def _ao_mudar_dados(self, tabela: str) -> None:
        if tabela in ("", "impressoras", "resinas", "canais"):
            self.calculadora.atualizar_listas()

    # ------------------------------------------------------------------ fechar
    def closeEvent(self, evento: QCloseEvent) -> None:  # noqa: N802 - API do Qt
        if self._confirmar_descartar():
            self.autosave.limpar()
            self.contexto.banco.fechar()
            evento.accept()
        else:
            evento.ignore()
