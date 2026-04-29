import customtkinter as ctk

class LogisticaFrame(ctk.CTkFrame):
    def __init__(self, master, calculadora, menu):
        """
        Classe responsável por calcular gastos relacionados a logística, desde embrulho, até taxas e envio ao cliente.
        :param master: Referência da qual esta janela está inserida.
        :param calculadora: Referência à calculadora geral do sistema.
        :param menu: Referência ao menu principal do sistema.
        """
        super().__init__(
            master,
            width=400,
            height=170,
            fg_color="#131313",
            border_width=2,
            border_color="#c2c2c2"
        )

        # /// Atributos e Objetos Principais ///////////////////////////////////////////
        self.calculadora_geral = calculadora
        self.menu = menu
        self.custo_total_logistica = '0,00'

        # /// Variáveis de Controle ////////////////////////////////////////////////////
        self.var_embrulho = ctk.StringVar()  # Custo médio gasto em caixas, plásticos, fitas adesivas.
        self.var_descontos = ctk.StringVar()  # Possíveis descontos aplicados por promoções.
        self.var_impostos = ctk.StringVar()  # Impostos para possíveis vendas em lojas online.
        self.var_frete = ctk.StringVar()  # Frete para enviar o produto via correio.

        # /// Padrões e Personalização /////////////////////////////////////////////////
        self.FONTE_SIMPLES = ('Arial', 12)
        self.FONTE_NEGRITO = ('Segoe UI', 15, 'bold')

        # /// Rótulos com textos indicativos ///////////////////////////////////////////
        self.texto_titulo = ctk.CTkLabel(self, text='Logística', font=('Arial', 15, 'bold'))
        self.texto_titulo.place(relx=0.5, y=5, anchor="n")

        self.titulos_indicativos = {}
        self.dados_dos_titulos = [
            ('embrulho', 'Embrulho (R$)', 25, 30),
            ('descontos', 'Descontos (R$)', 152, 30),
            ('impostos', 'Impostos (R$)', 25, 90),
            ('frete', 'Frete (R$)', 168, 90),
            ('custo_total', 'Custo Total', 290, 50)
        ]  # chave, texto, x, y

        for chave, texto, x, y in self.dados_dos_titulos:
            titulo = ctk.CTkLabel(self, text=texto)
            titulo.place(x=x, y=y)
            self.titulos_indicativos[chave] = titulo

        # /// Caixas de Entrada Vazias /////////////////////////////////////////////////
        self.caixas_de_entrada = {}
        self.dados_das_caixas_de_entrada = [
            ('embrulho', self.var_embrulho, 100, 15, 55),
            ('descontos', self.var_descontos, 100, 145, 55),
            ('impostos', self.var_impostos, 100, 15, 115),
            ('frete', self.var_frete, 100, 145, 115),
        ]  # chave, variavel de controle, tamanho(largura), x, y

        for chave, var, largura, x, y in self.dados_das_caixas_de_entrada:
            caixa = ctk.CTkEntry(self, textvariable=var, width=largura)
            caixa.place(x=x, y=y)
            self.caixas_de_entrada[chave] = caixa

        # /// Exibição: Resultado da Fórmula ///////////////////////////////////////////
        self.rotulo_custo_total = ctk.CTkLabel(
            self,
            text=f'R$ {self.custo_total_logistica:>7}',
            font=self.FONTE_NEGRITO,
            bg_color="#9d4cff",
            width=100,
            height=40,
        )
        self.rotulo_custo_total.place(x=270, y=75)

        # /// Eventos Automáticos //////////////////////////////////////////////////////
        for var in [self.var_embrulho, self.var_descontos, self.var_impostos, self.var_frete]:
            var.trace_add("write", self._recalcular_total)

    # /// Métodos de cálculo ///////////////////////////////////////////////////////////
    def _obter_valores(self) -> tuple:
        """
        Recolhe os valores inseridos nas caixas de texto e envia para conversão.
        :return: Retorna uma tupla com valores já convertidos que serão armazenados nas respectivas variáveis.
        """
        return (
            self.converter_float(self.var_embrulho.get()),
            self.converter_float(self.var_descontos.get()),
            self.converter_float(self.var_impostos.get()),
            self.converter_float(self.var_frete.get())
        )

    def _recalcular_total(self, *args) -> None:
        """
        Realiza o processo de chamada de métodos, desde obter valores, realizar calculo e por fim atualizar os dados.
        :return: None (Vazio).
        """
        # Envia alterações para os metadados
        self._exportar_dados_logistica()

        # Obtém, valída e calcula
        embrulho, descontos, impostos, frete = self._obter_valores()
        custo = self.calculo_logistica(embrulho, descontos, impostos, frete)

        valor_numerico = custo
        valor_formatado = f"{custo:.2f}".replace('.', ',')

        # Formata e atualiza objeto
        self._atualizar_rotulo_logistica(valor=valor_formatado)

        # Envia as informações para fora, requisitando nova atualização da soma geral
        self.calculadora_geral.set_valor("logistica", valor_numerico)
        self.calculadora_geral.atualizar_total()

    @staticmethod
    def calculo_logistica(
            embrulho: float,
            descontos: float,
            impostos: float,
            frete: float,
    ) -> float:
        """
        Aplica uma fórmula que reúne o total em gastos com logística, desde embrulho, até envio por correio.
        :param embrulho: Gasto médio com caixa, fitas, plástico, etc.
        :param descontos: Possíveis descontos, aplicados por promoções, etc. (Valor subtraído)
        :param impostos: Impostos cobrados por lojas online, leis, taxas gerais.
        :param frete: Valor cobrado pelo envio por correio ou outro meio de transporte que reflita gastos.
        :return: Resultado da Fórmula (embrulho + impostos + frete) - descontos
        """
        resultado = (embrulho + impostos + frete) - abs(descontos)
        limite_maximo = 9999.99
        resultado = max(-9999.99, min(resultado, limite_maximo))
        return resultado

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
            return float(valor)
        except ValueError:
            return 0.0

    # /// Métodos de atualização ///////////////////////////////////////////////////////
    def _atualizar_rotulo_logistica(self, valor: str) -> None:
        """
        Apenas atualiza label de total do objeto, junto com a variável para possíveis alterações futuras.
        :param valor: Valor em texto já formatado.
        :return: None (Vazio).
        """
        self.custo_total_logistica = valor
        self.rotulo_custo_total.configure(
            text=f'R$ {self.custo_total_logistica:>7}',
        )

    # /// Métodos de Importação e Exportação ///////////////////////////////////////////
    def _exportar_dados_logistica(self) -> None:
        """
        Envia os dados inseridos nas caixas para o sistema de Menu Principal que poderá salvá-los caso necessário.
        :return: None (Vazio).
        """
        self.menu.ativar_alteracao()

        embrulho = self.var_embrulho.get()
        descontos = self.var_descontos.get()
        impostos = self.var_impostos.get()
        frete = self.var_frete.get()

        chave = "logistica"
        itens = {
            "embrulho": embrulho,
            "descontos": descontos,
            "impostos": impostos,
            "frete": frete
        }

        self.menu.receber_alteracao((chave, itens))

    def importar_dados_logistica(
            self,
            embrulho: str,
            descontos: str,
            impostos: str,
            frete: str
    ) -> None:
        """
        Recebe um conjunto de valores correspondentes às caixas quando um arquivo é aberto pelo Menu Principal.
        :return: None (Vazio).
        """
        self.var_embrulho.set(embrulho)
        self.var_descontos.set(descontos)
        self.var_impostos.set(impostos)
        self.var_frete.set(frete)

    def limpar_dados_logistica(self) -> None:
        """
        Limpa os dados nas caixas sempre que um novo arquivo é criado no Menu Principal.
        :return: None (Vazio).
        """
        for var in [
            self.var_embrulho,
            self.var_descontos,
            self.var_impostos,
            self.var_frete
        ]:
            var.set("")

        self._atualizar_rotulo_logistica("0,00")