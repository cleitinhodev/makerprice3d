import customtkinter as ctk

class JanelaModificaItens(ctk.CTkToplevel):
    def __init__(self, master=None, tipo="", valores=[]):
        """
        Janela Responsável por adicionar ou editar itens na tabela de despesas.
        :param master: Referência da qual esta janela está inserida.
        :param tipo: tag de identificação para orientar esta janela sobre quias métodos chamar. (adicinar/editar)
        :param valores: Valores trazidos do item selecionado para preencher as caixas a serem editadas.
        """
        super().__init__(master)

        # /// Configurações Padrão /////////////////////////////////////////////////////
        self.master = master
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.title("Adicionar/Editar")
        self.geometry("420x220")
        self.resizable(False, False)
        self.configure(fg_color="#131313") #1a1a1a
        self._centralizar()
        self.grab_set()

        # /// Variáveis de Controle ////////////////////////////////////////////////////
        self.tipo = tipo # Permite dois modos, "editar" e "adicionar"
        self.dados_capturados = valores

        self.var_nome = ctk.StringVar(value=self.dados_capturados[0] if self.dados_capturados else "")
        self.var_tipo = ctk.StringVar(value=self.dados_capturados[1] if self.dados_capturados else "")
        self.var_quantidade = ctk.StringVar(value=self.dados_capturados[2]if self.dados_capturados else "")
        self.var_valor = ctk.StringVar(value=self.dados_capturados[3] if self.dados_capturados else "")

        # /// Geração de Frame /////////////////////////////////////////////////////////
        self.frame_titulos = ctk.CTkFrame(self, fg_color="#202020")
        self.frame_titulos.grid(column=0, row=0, padx=5, pady=5)
        self.frame_campos = ctk.CTkFrame(self, fg_color="#202020")
        self.frame_campos.grid(column=1, row=0, padx=5, pady=5)
        self.frame_botoes = ctk.CTkFrame(self, fg_color="#202020")
        self.frame_botoes.grid(columnspan=2, row=1, sticky="ew", pady=5, padx=5)

        # /// Geração de Títulos ///////////////////////////////////////////////////////
        self.titulos_colunas = {}
        self.dados_titulos = [
            ('titulo_nome', 'Nome:'),
            ('titulo_tipo', 'Tipo:'),
            ('titulo_quantidade', 'Quantidade:'),
            ('titulo_valor', 'Valor (R$):'),
        ] # chave, texto, linha, coluna

        for chave, texto in self.dados_titulos:
            label = ctk.CTkLabel(self.frame_titulos, text=texto, width=90, anchor=ctk.CENTER)
            label.pack(padx=0, pady=5)
            self.titulos_colunas[chave] = label

        # /// Geração de campos ////////////////////////////////////////////////////////
        self.campos_colunas = {}
        self.dados_campos = [
            ('campo_nome', self.var_nome),
            ('campo_tipo', self.var_tipo),
            ('campo_quantidade', self.var_quantidade),
            ('campo_valor', self.var_valor),
        ]  # chave, variavel de controle, linha, coluna

        for chave, variavel in self.dados_campos:
            caixa = ctk.CTkEntry(self.frame_campos, textvariable=variavel, width=300)
            caixa.pack(padx=5, pady=5)
            self.campos_colunas[chave] = caixa

        # /// Geração de botões ////////////////////////////////////////////////////////
        self.botao_confirmar = ctk.CTkButton(
            self.frame_botoes,
            text="Confirmar",
            fg_color="#4e3a95",
            hover_color="#696dbd",
            border_width=1,
            border_color="white",
            command=self._confirmar,
        )
        self.botao_confirmar.pack(pady=10)

    # /// Métodos de Janela ////////////////////////////////////////////////////////////
    def _centralizar(self) -> None:
        """
        Centraliza a janela
        :return: None (Vazio).
        """
        self.update_idletasks()

        largura = self.winfo_width()
        altura = self.winfo_height()

        largura_tela = self.winfo_screenwidth()
        altura_tela = self.winfo_screenheight()

        x = (largura_tela // 2) - (largura // 2)
        y = (altura_tela // 2) - (altura // 2)

        self.geometry(f"{largura}x{altura}+{x}+{y}")

    def _ao_fechar(self) -> None:
        """
        Esvazia o atributo da área de despesas para garantir que a janela não existe mais após ser fechada.
        :return: None (Vazio).
        """
        self.master.focus()
        self.withdraw()  # esconde imediatamente
        self.update_idletasks()  # força atualização visual
        self.master.janela_modificacao = None
        self.destroy()

    # /// Métodos ação /////////////////////////////////////////////////////////////////
    def _confirmar(self) -> None:
        """
        Com base na tag escolhida (adicionar ou editar), chamará métodos diferentes para enviar os dados.
        :return: None (Vazio).
        """
        nome, tipo, quantidade, valor = self._obter_dados_das_caixas()
        # dados_brutos = (nome, tipo, quantidade, (valor * quantidade))
        dados_formatados = (f'{nome}', f'{tipo}', f'{quantidade}', f'R$ {(valor * quantidade):.2f}')

        if self.tipo == "adicionar":
            self.master.adicionar(dados_formatados)
        elif self.tipo == "editar":
            self.master.editar(dados_formatados)

    def _obter_dados_das_caixas(self) -> tuple:
        """
        Obtém os dados nas caixas de texto e converte para retorná-los já validados.
        :return: tuple (Tupla com nome, tipo, quantidade, valor)
        """
        nome = self.var_nome.get()
        tipo = self.var_tipo.get()
        quantidade = self.converter_int(self.var_quantidade.get())
        valor = self.converter_float(self.var_valor.get())
        return nome, tipo, quantidade, valor

    # /// Métodos de Validação /////////////////////////////////////////////////////////
    @staticmethod
    def converter_float(valor: str) -> float:
        """
        Pega o valor na caixa de entrada e tenta converter para ponto flutuante (float)
        :param valor: Somente valores numéricos, evitando letras ou símbolos que não sejam '.' ou ','
        :return: Retorna o número já convertido para float, em caso de erro retorna 0.0
        """
        valor = valor.strip().replace(',', '.')

        if not valor:
            return 0.0

        try:
            return abs(float(valor))
        except ValueError:
            return 0.0

    @staticmethod
    def converter_int(valor: str) -> int:
        """
        Pega o valor na caixa de entrada e tenta converter para inteiro (int)
        :param valor: Somente valores numéricos, evitando letras ou símbolos.
        :return: Retorna o número já convertido para inteiro, em caso de erro retorna 0
        """
        if not valor:
            return int(1)

        try:
            return abs(int(valor))
        except ValueError:
            return int(1)