import customtkinter as ctk
from tkinter import ttk
from ferramentas.modifica_itens import JanelaModificaItens

class DespesasFrame(ctk.CTkFrame):
    def __init__(self, master, calculadora, menu):
        """
        Classe responsável por calcular despesas extras através de uma lista de itens opcionais.
        :param master: Referência da qual esta janela está inserida.
        :param calculadora: Referência à calculadora geral do sistema.
        :param menu: Referência ao menu principal do sistema.
        """
        super().__init__(
            master,
            width=450,
            height=308,
            fg_color="#131313",
            border_width=2,
            border_color="#c2c2c2"
        )
        # /// Padrões e Personalização /////////////////////////////////////////////////
        self.FONTE_SIMPLES = ('Arial', 14)
        self.FONTE_SIMPLES_REDUZIDA = ('Arial', 13)
        self.FONTE_NEGRITO = ('Segoe UI', 16, 'bold')


        # /// Atributos e Objetos Principais ///////////////////////////////////////////
        self.calculadora_geral = calculadora
        self.menu = menu
        self.custo_total_despesas = '0,00'
        self.janela_modificacao = None # Variável Pública (Para limpar quando janela fechar)
        self.novos_valores = None
        self.dados_capturados = ()

        self.botoes_de_comandos = {}
        self.dados_dos_botoes = [
            ('adicionar', 'Adicionar', self.FONTE_SIMPLES,
             lambda tipo = "adicionar": self._abrir_janela_modificacao(tipo)),
            ('editar', 'Editar', self.FONTE_SIMPLES,
             lambda tipo = "editar": self._abrir_janela_modificacao(tipo)),
            ('deletar', 'Deletar', self.FONTE_SIMPLES, self._deletar),
            ('limpar_tudo', 'Limpar Tudo', self.FONTE_SIMPLES_REDUZIDA, self._limpar),
        ] # chave, texto, fonte, comando

        # /// título geral /////////////////////////////////////////////////////////////
        self.titulo_despesas = ctk.CTkLabel(self, text='Despesas', font=('Arial', 15, 'bold'))
        self.titulo_despesas.place(relx=0.5, y=5, anchor="n")

        # /// criação de frames ////////////////////////////////////////////////////////
        self.frame_tabela = ctk.CTkFrame(self, bg_color="#131313")
        self.frame_tabela.place(relx=0.5, y=35, anchor="n")
        self.frame_botoes = ctk.CTkFrame(self, fg_color="#131313")
        self.frame_botoes.place(relx=0.5, y=265, anchor="n")

        # /// Exibição: Resultado da Fórmula ///////////////////////////////////////////
        self.rotulo_total_despesas = ctk.CTkLabel(self, text=f'Total: {f"R$ {self.custo_total_despesas}":>80}',
                                                  fg_color="#f26522", width=422, font=self.FONTE_NEGRITO)
        self.rotulo_total_despesas.place(relx=0.5, y=235, anchor="n")

        # _______ Chamadas _____________________________________________________________
        self._criar_tabela_despesas()
        self._criar_botoes(self.dados_dos_botoes)

    # /// Métodos de geração ///////////////////////////////////////////////////////////
    def _criar_tabela_despesas(self) -> None:
        """
        Gera uma tabela estilo Treeview baseada em ttk.
        :return: None (Vazio).
        """
        style = ttk.Style()
        style.theme_use("default")

        # Corpo da tabela (branco)
        style.configure("Treeview",
                        background="white",
                        foreground="black",
                        fieldbackground="white",
                        rowheight=18,
                        borderwidth=1,
                        relief="solid")

        # Cabeçalho estilo Excel
        style.configure("Treeview.Heading",
                        background="#f0f0f0",
                        foreground="black",
                        relief="solid",
                        borderwidth=1)

        # Seleção azul claro
        style.map("Treeview",
                  background=[("selected", "#cce5ff")],
                  foreground=[("selected", "black")])

        # Criação da tabela
        self.tabela_despesas = ttk.Treeview(
            self.frame_tabela,
            columns=("c1", "c2", "c3", "c4"),
            show="headings"
        )

        self.tabela_despesas.pack(fill="both", expand=True)

        # Cabeçalhos
        self.tabela_despesas.heading("c1", text="Nome")
        self.tabela_despesas.heading("c2", text="Tipo")
        self.tabela_despesas.heading("c3", text="Qtd")
        self.tabela_despesas.heading("c4", text="Valor")

        # Colunas fixas (melhora visual de grid)
        for col in ("c1", "c2", "c3", "c4"):
            self.tabela_despesas.column(col, anchor="center", width=105, stretch=False)

        # Zebra (simula linhas)
        self.tabela_despesas.tag_configure("odd", background="white")
        self.tabela_despesas.tag_configure("even", background="#f9f9f9")

    def _criar_botoes(self, dados: list) -> None:
        """
        Cria botões baseado em uma lista com parâmetros pré-definidos.
        :param dados: Lista com parâmetros em forma de tuplas.
        :return: None (Vazio).
        """
        for chave, texto, fonte, comando in dados:
            botao = ctk.CTkButton(
                self.frame_botoes,
                text=texto,
                width=100,
                fg_color="#4e3a95",
                hover_color="#696dbd",
                font=fonte,
                border_width=1,
                border_color='white',
                command=comando
            )
            botao.pack(side="left", padx=5, pady=5)
            self.botoes_de_comandos[chave] = botao

    # /// Métodos de ação //////////////////////////////////////////////////////////////
    def adicionar(self, dados: tuple) -> None:
        """
        Método público que adiciona valores à nossa tabela através de uma tupla.
        :param dados: Tupla com 4 valores.
        :return: None (Vazio).
        """
        count = len(self.tabela_despesas.get_children())
        tag = "even" if count % 2 == 0 else "odd"

        self.tabela_despesas.insert("",
                         "end",
                         values=dados,
                         tags=(tag,))

        # Recalcula tudo
        self._recalcular_total()

    def _deletar(self) -> None:
        """
        Deleta itens selecionados na tabela.
        :return: None (Vazio).
        """
        selecionado = self.tabela_despesas.selection()

        for item in selecionado:
            self.tabela_despesas.delete(item)

        self._reorganizar_zebra()

        # Recalcula tudo
        self._recalcular_total()

    def editar(self, dados: tuple) -> None:
        """
        Método público que edita o item selecionado na tabela.
        :param dados: Novos dados a serem inseridos no lugar dos antigos.
        :return: None (Vazio).
        """
        # Pega itens selecionados
        selecionado = self.tabela_despesas.selection()

        # Se nada foi selecionado, cancela operação
        if not selecionado:
            return

        # armazena o PRIMEIRO item selecionado, mesmo que a seleção tenha sido múltipla
        item = selecionado[0]

        # Modifica este item com os dados que definimos
        self.tabela_despesas.item(item, values=dados)

        # Recalcula tudo
        self._recalcular_total()

    def _limpar(self) -> None:
        """
        Limpa completamente a tabela.
        :return: None (Vazio).
        """

        for item in self.tabela_despesas.get_children():
            self.tabela_despesas.delete(item)

        # Recalcula tudo
        self._recalcular_total()

    def _reorganizar_zebra(self) -> None:
        """
        Reorganiza os itens com seus devidos estilos.
        :return: None (Vazio).
        """
        for i, item in enumerate(self.tabela_despesas.get_children()):
            tag = "even" if i % 2 == 0 else "odd"
            self.tabela_despesas.item(item, tags=(tag,))

    # /// Métodos de Ferramentas ///////////////////////////////////////////////////////
    def _abrir_janela_modificacao(self, tipo) -> None:
        """
        Abre uma nova janela onde podemos adicionar ou editar as informações de um item.
        :param tipo: tag que indica à nova janela quais métodos ela deve acionar ao finalizar a operação.
        :return: None (Vazio).
        """
        if self.janela_modificacao is None or not self.janela_modificacao.winfo_exists():

            valores = None

            if tipo == "editar":
                selecionado = self.tabela_despesas.selection()

                if not selecionado:
                    print("Nenhum item selecionado")
                    return

                item = selecionado[0]
                valores = list(self.tabela_despesas.item(item, "values"))
                valores = self._validar_tipos(valores)

            self.janela_modificacao = JanelaModificaItens(self, tipo, valores)

        else:
            self.janela_modificacao.focus()

    # /// Métodos de validação /////////////////////////////////////////////////////////
    @staticmethod
    def _validar_tipos(itens: list) -> list:
        """
        Recebe uma lista de valores de um item e converte valores para realizar possíveis calculos.
        :param itens: Lista com nome, tipo, quantidade e valor.
        :return: list (Valores já formatados)
        """
        nome = itens[0]
        tipo = itens[1]
        quantidade = int(itens[2])
        valor = float(itens[3].replace("R$", "").replace(",", ".").strip())

        return [nome, tipo, quantidade, (valor / quantidade)]

    # //// Métodos de calculo //////////////////////////////////////////////////////////
    def _recalcular_total(self) -> None:
        """
        Obtém todos os valores em dinheiro da tabela e realiza uma soma.
        :return: None (Vazio).
        """
        # Envia alterações para os metadados
        self._exportar_dados_despesas()

        total = 0.0

        for item in self.tabela_despesas.get_children():
            valores = self.tabela_despesas.item(item, "values")

            valor_str = valores[3]  # coluna c4 (Valor)

            # Converter "R$ 14,99" → 14.99
            try:
                valor_float = float(valor_str.replace("R$", "").replace(",", ".").strip())
            except TypeError:
                valor_float = 0

            total += valor_float

        # Atualiza Objeto
        self._atualizar_rotulo_total_gasto_em_despesas(f"{total:.2f}")

        # Envia as informações para fora, requisitando nova atualização da soma geral
        self.calculadora_geral.set_valor("despesas", total)
        self.calculadora_geral.atualizar_total()

    # /// Métodos de atualização ///////////////////////////////////////////////////////
    def _atualizar_rotulo_total_gasto_em_despesas(self, valor: str) -> None:
        """
        Apenas atualiza label de total do objeto, junto com a variável para possíveis alterações futuras.
        :param valor: Valor em texto já formatado.
        :return: None (Vazio).
        """
        self.custo_total_despesas = str(valor).replace('.', ',')
        self.rotulo_total_despesas.configure(
            text=f'Total: {f"R$ {self.custo_total_despesas}":>80}',
        )

    # /// Métodos de Importação e Exportação ///////////////////////////////////////////
    def _exportar_dados_despesas(self) -> None:
        """
        Envia os dados inseridos na tabela para o sistema de Menu Principal que poderá salvá-los caso necessário.
        :return: None (Vazio).
        """
        self.menu.ativar_alteracao()

        itens_tabela = []

        for item in self.tabela_despesas.get_children():
            valores = self.tabela_despesas.item(item, "values")
            itens_tabela.append(valores)

        chave = "despesas"
        itens = {"tabela": itens_tabela}

        self.menu.receber_alteracao((chave, itens))

    def importar_dados_despesas(self, tabela: list) -> None:
        """
        Recebe os dados da tabela quando um arquivo é aberto pelo Menu Principal.
        :param tabela: Lista contendo todos os itens da tabela.
        :return: None (Vazio).
        """
        self._limpar()

        for dados in tabela:
            self.adicionar(tuple(dados))

    def limpar_dados_despesas(self) -> None:
        """
        Limpa completamente a tabela sempre que um novo arquivo é criado no Menu Principal.
        :return: None (Vazio).
        """
        self._limpar()
        self._atualizar_rotulo_total_gasto_em_despesas("0,00")