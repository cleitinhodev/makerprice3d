import customtkinter as ctk
import json
import os
from tkinter import filedialog, messagebox
from ferramentas.cotacao import JanelaConversorMoedas
from ferramentas.sobre import JanelaSobre
import webbrowser

class MenuPrincipal(ctk.CTkFrame):
    """
    Classe responsável por gerenciar o menu superior da aplicação.

    Contém lógica de criação de botões, exibição de submenus,
    controle de arquivos (novo, abrir, salvar) e integração com
    outras funcionalidades da aplicação.
    """
    def __init__(self, master, app):
        """
        Inicializa o menu principal.

        :param master: Janela principal (CTk).
        :param app: Instância da aplicação principal.
        """
        super().__init__(master,
                         fg_color="#2a2a2b",
                         height=30)

        # /// Atributos e Objetos Principais ///////////////////////////////////////////
        self.master = master  # janela (CTk)
        self.app = app  # JanelaPrincipal

        self.janela_cotacao = None
        self.janela_sobre = None
        self.lista_de_botoes = []
        self.menu_aberto = None
        self.caminho_arquivo = None
        self.alterado = False
        self.dados_do_arquivo = None
        self._resetar_dados()


        # /// Widgets e Submenu ////////////////////////////////////////////////////////
        self.submenu = ctk.CTkFrame(
            self.master,
            fg_color="#2f2f2f",
            corner_radius=5
        )
        self.submenu.place_forget()

        # /// Eventos //////////////////////////////////////////////////////////////////
        self._criar_botoes()
        self.winfo_toplevel().bind("<Button-1>", self._clique_global)

    # /// Geração de elementos /////////////////////////////////////////////////////////
    def _criar_botoes(self) -> None:
        """
        Cria os botões principais do menu superior (Arquivo, Ferramentas, Ajuda).
        """
        menus = [
            ("Arquivo", 80),
            ("Ferramentas", 110),
            ("Ajuda", 60)
        ]

        for nome, tamanho in menus:
            botao = ctk.CTkButton(
                self,
                text=nome,
                width=tamanho,
                fg_color="transparent",
                hover_color="#636363",
                corner_radius=0
            )

            botao.configure(
                command=lambda b=botao, n=nome: self._abrir_menu(b, n)
            )

            botao.pack(side="left", padx=2, pady=2)
            self.lista_de_botoes.append(botao)

    # /// Métodos de controle de menu //////////////////////////////////////////////////
    def _abrir_menu(self, botao, nome) -> None:
        """
        Abre ou fecha um submenu com base no botão clicado.

        :param botao: Botão que disparou o evento.
        :param nome: Nome do menu a ser aberto.
        """
        # Se clicou no mesmo → fecha
        if self.menu_aberto == nome:
            self._fechar_submenu()
            return

        self.menu_aberto = nome

        # Limpa conteúdo antigo (SEM destruir frame)
        for widget in self.submenu.winfo_children():
            widget.destroy()

        # Define posição
        x = botao.winfo_rootx() - self.master.winfo_rootx()
        y = botao.winfo_rooty() - self.master.winfo_rooty() + botao.winfo_height()

        # Limpa conteúdo antigo
        for widget in self.submenu.winfo_children():
            widget.destroy()

        # Preenche conteúdo PRIMEIRO
        if nome == "Arquivo":
            self.menu_arquivo()
        elif nome == "Ferramentas":
            self.menu_ferramentas()
        elif nome == "Ajuda":
            self.menu_ajuda()

        # Força o cálculo do tamanho real
        self.submenu.update_idletasks()

        # Calcula posição
        x = botao.winfo_rootx() - self.master.winfo_rootx()
        y = botao.winfo_rooty() - self.master.winfo_rooty() + botao.winfo_height()

        # Agora sim mostra
        self.submenu.place(x=x, y=y)
        self.submenu.lift()

    def _fechar_submenu(self) -> None:
        """
        Fecha o submenu atualmente aberto.
        """
        self.submenu.place_forget()
        self.menu_aberto = None

    # /// Clique fora do campo /////////////////////////////////////////////////////////
    def _clique_global(self, event) -> None:
        """
        Detecta cliques globais para fechar o submenu quando necessário.

        :param event: Evento de clique.
        """
        if not self.menu_aberto:
            return

        self.after_idle(lambda: self._verificar_clique(event))

    def _verificar_clique(self, event) -> None:
        """
        Verifica se o clique ocorreu fora do menu e submenu.

        :param event: Evento de clique.
        """
        widget = event.widget

        for botao in self.lista_de_botoes:
            if self._pertence(widget, botao):
                return

        if self._pertence(widget, self.submenu):
            return

        self._fechar_submenu()

    @staticmethod
    def _pertence(widget, alvo) -> bool:
        """
        Verifica se um widget pertence a outro (hierarquia).

        :param widget: Widget de origem.
        :param alvo: Widget alvo.
        :return: True se pertence, False caso contrário.
        """
        while widget:
            if widget == alvo:
                return True
            widget = widget.master
        return False

    # /// Conteúdos dos Menus //////////////////////////////////////////////////////////
    def _criar_item(self, texto, comando) -> None:
        """
        Cria um item (botão) dentro do submenu.

        :param texto: Texto exibido no item.
        :param comando: Função executada ao clicar.
        """
        ctk.CTkButton(
            self.submenu,
            text=texto,
            fg_color="transparent",
            hover_color="#636363",
            corner_radius=0,
            anchor="w",
            command=comando
        ).pack(fill="x")

    def menu_arquivo(self) -> None:
        """
        Define os itens do menu 'Arquivo'.
        """
        self._criar_item("     Novo", self.novo)
        self._criar_item("     Abrir", self.abrir)
        self._criar_item("     Salvar", self.salvar)

    def menu_ferramentas(self) -> None:
        """
        Define os itens do menu 'Ferramentas'.
        """
        self._criar_item("   Cotação", self.cotacao)
        # self.criar_item("   Calculadora", self.calculadora)
        # self.criar_item("   Outro", self.outros)

    def menu_ajuda(self) -> None:
        """
        Define os itens do menu 'Ajuda'.
        """
        self._criar_item("  Tutorial", self.tutorial)
        self._criar_item("  Sobre", self.sobre)

    # /// Métodos de controle de fluxo /////////////////////////////////////////////////
    def ativar_alteracao(self) -> None:
        """
        Marca que houve alteração nos dados atuais.
        """
        self.alterado = True

    def receber_alteracao(self, alteracoes: tuple) -> None:
        """
        Recebe alterações vindas da aplicação e atualiza os dados internos.

        :param alteracoes: Tupla contendo chave principal e valores atualizados.
        """
        chave_principal = alteracoes[0]
        itens_totais = alteracoes[1]

        self.dados_do_arquivo[chave_principal] = itens_totais

    def _confirmar_salvar(self) -> bool:
        """
        Verifica se existem alterações pendentes e pergunta ao usuário
        se deseja salvar antes de continuar.

        :return: True se pode continuar, False se a operação foi cancelada.
        """
        if not self.alterado:
            return True

        resposta = messagebox.askyesnocancel(
            "Salvar",
            "Deseja salvar as alterações?"
        )

        if resposta is None:
            self._fechar_submenu()
            return False  # resposta: cancelar (Fecha e não limpa)
        elif resposta:
            self.salvar()
            return True  # resposta sim: salvar, e limpar
        else:
            return True  # resposta não: não salvar, e limpar

    def _limpar_todas_as_caixas(self) -> None:
        """
        Solicita à aplicação principal a limpeza de todos os campos.
        """
        self.app.limpar_todas_as_caixas()

    def _aplicar_dados(self, nome, dados) -> bool:
        """
        Aplica dados carregados do arquivo na interface.

        :param nome: Nome do arquivo.
        :param dados: Dados carregados.
        :return: True se aplicado com sucesso, False caso contrário.
        """
        if self.app.reescrever_todas_as_caixas(dados):
            self.app.renomear_titulo(nome)
            return True
        return False

    def resetar_atributos(self) -> None:
        """
        Reseta completamente o estado da aplicação para um novo arquivo.
        """
        # Limpar todas os campos do sistema
        self._limpar_todas_as_caixas()

        # Deixando atributos no estado padrão
        self.caminho_arquivo = None
        self.alterado = False
        self._resetar_dados()
        self.app.renomear_titulo("Sem Título")

    def _resetar_dados(self) -> None:
        """
        Inicializa ou reseta a estrutura padrão de dados do sistema.
        """
        self.dados_do_arquivo = {
            "material": {
                "resina": "",
                "suporte": "",
                "peso": "",
                "custo_fixo": ""
            },
            "energia": {
                "impressao": "",
                "lixa_retificadora": "",
                "lavagem_cura": "",
                "pintura": ""
            },
            "desgaste": {
                "preco_lcd": "",
                "vida_util": "",
                "tempo_total": "",
                "preco_fep": "",
                "durabilidade": "",
                "porcentagem_area": "",
                "manutencao_fixa_extra": ""
            },
            "acabamento": {
                "lavagem": {
                    "custo_solvente": "",
                    "lavagens_por_peca": "",
                    "litros_usados": ""
                },
                "lixa": {
                    "custo_de_ponta": "",
                    "vida_util_ponta": "",
                    "pontas_usadas": ""
                },
                "pintura": {
                    "custo_unidade_tinta": "",
                    "ml_por_unidade": "",
                    "uso_de_tinta_medio": ""
                }
            },
            "despesas": {
                "tabela": []
            },
            "logistica": {
                "embrulho": "",
                "descontos": "",
                "impostos": "",
                "frete": ""
            },
            "mao_de_obra": {
                "ganho_por_hora": "",
                "horas_trabalhadas": ""
            },
            "lucro": {
                "estado": 0
            }
        }

    # /// Métodos de Ação //////////////////////////////////////////////////////////////
    def novo(self) -> None:
        """
        Cria um novo arquivo, limpando os dados atuais.
        """
        self._fechar_submenu()

        if not self._confirmar_salvar():
            return

        self.resetar_atributos()

    def abrir(self) -> None:
        """
        Abre um arquivo JSON e carrega seus dados na aplicação.
        """
        self._fechar_submenu()

        if not self._confirmar_salvar():
            return

        try:
            caminho = filedialog.askopenfilename(
                filetypes=[("JSON", "*.json")]
            )

            if not caminho:
                return

            with open(caminho, "r", encoding="utf-8") as f:
                dados = json.load(f)

            nome_arquivo = os.path.basename(caminho)

            sucesso = self._aplicar_dados(nome_arquivo, dados)

            if sucesso:
                self.caminho_arquivo = caminho
                self.alterado = False
            else:
                self.caminho_arquivo = None  # ESSENCIAL

        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado:\n{e}")
            self.caminho_arquivo = None

        except TypeError:
            messagebox.showerror("Erro", "Formato de arquivo inválido.")
            self.caminho_arquivo = None
            return

        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado:\n{e}")
            self.caminho_arquivo = None
            return

    def salvar(self) -> None:
        """
        Salva os dados atuais em um arquivo JSON.
        """
        self._fechar_submenu()

        if not self.caminho_arquivo:
            caminho = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON", "*.json")]
            )
            if not caminho:
                return

            self.caminho_arquivo = caminho

        nome_arquivo = os.path.basename(self.caminho_arquivo)

        dados = self.dados_do_arquivo
        self.app.renomear_titulo(nome_arquivo)

        with open(self.caminho_arquivo, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)

        self.alterado = False

    def cotacao(self) -> None:
        """
        Abre uma nova janela de Cotação para auxiliar usuário na definição de preço..
        """
        total_absoluto = self.app.solicitar_total_absoluto()


        if (
                self.janela_cotacao is None
                or not self.janela_cotacao.winfo_exists()
        ):
            self.janela_cotacao = JanelaConversorMoedas(self, total_absoluto=total_absoluto)
        else:
            self.janela_cotacao.focus()
        self._fechar_submenu()

    def calculadora(self):
        ####### Em Desenvolvimento #######
        return

    def outros(self):
        ####### Em Desenvolvimento #######
        return

    def tutorial(self):
        """
        Abre o tutorial no navegador padrão.
        """
        self._fechar_submenu()
        webbrowser.open("https://www.bugzinho.com/makerprice3d")

    def sobre(self):
        """
        Abre uma nova janela de Calculadora de Energia Kwh para auxiliar usuário na definição de gastos.
        :return: None (Vazio).
        """
        self._fechar_submenu()
        if (
                self.janela_sobre is None
                or not self.janela_sobre.winfo_exists()
        ):
            self.janela_sobre = JanelaSobre(self)
            self.focus_force()
        else:
            self.janela_sobre.focus()


