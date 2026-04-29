import customtkinter as ctk

class MaoDeObraFrame(ctk.CTkFrame):
    def __init__(self, master, calculadora, menu):
        """
        Classe responsável por calcular a mão de obra em uma peça, recolhendo valores individuais que vão depender de
        cada usuário como por exemplo ganho por hora, e também total de horas trabalhadas.

        :param master: Referência da qual esta janela está inserida.
        :param calculadora: Referência à calculadora geral do sistema.
        :param menu: Referência ao menu principal do sistema.
        """
        super().__init__(
            master,
            width=400,
            height=120,
            fg_color="#131313",
            border_width=2,
            border_color="#c2c2c2"
        )

        # /// Atributos e Objetos Principais ///////////////////////////////////////////
        self.calculadora_geral = calculadora
        self.menu = menu
        self.custo_total_mao_de_obra = '0,00'

        # /// Variáveis de Controle ////////////////////////////////////////////////////
        self.var_ganho_por_hora = ctk.StringVar()  # Valor em R$ de ganho por hora trabalhada.
        self.var_horas_trabalhadas = ctk.StringVar()  # Total de horas trabalhadas na peça atual.

        # /// Padrões e Personalização /////////////////////////////////////////////////
        self.FONTE_SIMPLES = ('Arial', 12)
        self.FONTE_NEGRITO = ('Segoe UI', 15, 'bold')

        # /// Rótulos com textos indicativos ///////////////////////////////////////////
        self.texto_titulo = ctk.CTkLabel(self, text='Mão de Obra', font=self.FONTE_NEGRITO)
        self.texto_titulo.place(relx=0.5, y=5, anchor="n")

        self.titulos_indicativos = {}
        self.dados_dos_titulos = [
            ('ganho_por_hora', 'Ganho por Hora', 20, 30),
            ('horas_trabalhadas', 'Horas Trabalhadas', 142, 30),
            ('custo_total', 'Custo Total', 290, 25),
        ]  # chave, texto, x, y

        for chave, texto, x, y in self.dados_dos_titulos:
            titulo = ctk.CTkLabel(self, text=texto)
            titulo.place(x=x, y=y)
            self.titulos_indicativos[chave] = titulo

        # /// Caixas de Entrada Vazias /////////////////////////////////////////////////
        self.caixas_de_entrada = {}
        self.dados_das_caixas_de_entrada = [
            ('ganho_por_hora', self.var_ganho_por_hora, 100, 15, 55),
            ('horas_trabalhadas', self.var_horas_trabalhadas, 100, 145, 55),
        ]  # chave, variavel de controle, tamanho(largura), x, y

        for chave, var, largura, x, y in self.dados_das_caixas_de_entrada:
            caixa = ctk.CTkEntry(self, textvariable=var, width=largura)
            caixa.place(x=x, y=y)
            self.caixas_de_entrada[chave] = caixa

        # /// Exibição: Resultado da Fórmula ///////////////////////////////////////////
        self.rotulo_custo_total = ctk.CTkLabel(
            self,
            text=f'R$ {self.custo_total_mao_de_obra:>7}',
            font=self.FONTE_NEGRITO,
            bg_color="#4cff9d",
            text_color='black',
            width=100,
            height=40
        )
        self.rotulo_custo_total.place(x=270, y=50)

        # /// Eventos Automáticos //////////////////////////////////////////////////////
        for var in [self.var_horas_trabalhadas, self.var_ganho_por_hora]:
            var.trace_add("write", self._recalcular_total)

    # /// Métodos de cálculo ///////////////////////////////////////////////////////////
    def _obter_valores(self) -> tuple:
        """
        Recolhe os valores inseridos nas caixas de texto e envia para conversão.
        :return: Retorna uma tupla com valores já convertidos que serão armazenados nas respectivas variáveis.
        """
        return (
            self.converter_float(self.var_ganho_por_hora.get()),
            self.converter_float(self.var_horas_trabalhadas.get())
        )

    def _recalcular_total(self, *args) -> None:
        """
        Realiza o processo de chamada de métodos, desde obter valores, realizar calculo e por fim atualizar os dados.
        :return: None (Vazio).
        """
        # Envia alterações para os metadados
        self._exportar_dados_mao_de_obra()

        # Obtém, valída e calcula
        ganho_por_hora, horas_trabalhadas = self._obter_valores()
        custo = self.calculo_mao_de_obra(ganho_por_hora, horas_trabalhadas)

        valor_numerico = custo
        valor_formatado = f"{custo:.2f}".replace('.', ',')

        # Formata e atualiza objeto
        self._atualizar_rotulo_mao_de_obra(valor=valor_formatado)

        # Envia as informações para fora, requisitando nova atualização da soma geral
        self.calculadora_geral.set_valor("mao_de_obra", valor_numerico)
        self.calculadora_geral.atualizar_total()

    @staticmethod
    def calculo_mao_de_obra(
            ganho_por_hora: float,
            horas_trabalhadas: float,
    ) -> float:
        """
        Aplica uma multiplicação simples para ter uma média de ganho pelas horas trabalhadas na peça.
        :param ganho_por_hora: Quantidade em (R$) que o usuário deseja cobrar em 1 hora trabalhada.
        :param horas_trabalhadas: Total de horas trabalhadas na peça atual. (ex: 8,5 = 8 horas e meia)
        :return: Resultado da Fórmula (ganho_por_hora * horas_trabalhadas)
        """
        resultado = ganho_por_hora * horas_trabalhadas
        limite_maximo = 9999.99
        resultado = max(0, min(resultado, limite_maximo))
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
    def _atualizar_rotulo_mao_de_obra(self, valor: str) -> None:
        """
        Apenas atualiza label de total do objeto, junto com a variável para possíveis alterações futuras.
        :param valor: Valor em texto já formatado.
        :return: None (Vazio).
        """
        self.custo_total_mao_de_obra = valor
        self.rotulo_custo_total.configure(
            text=f'R$ {self.custo_total_mao_de_obra:>7}',
        )

    # /// Métodos de Importação e Exportação ///////////////////////////////////////////
    def _exportar_dados_mao_de_obra(self) -> None:
        """
        Envia os dados inseridos nas caixas para o sistema de Menu Principal que poderá salvá-los caso necessário.
        :return: None (Vazio).
        """
        self.menu.ativar_alteracao()

        ganho_por_hora = self.var_ganho_por_hora.get()
        horas_trabalhadas = self.var_horas_trabalhadas.get()

        chave = "mao_de_obra"
        itens = {
            "ganho_por_hora": ganho_por_hora,
            "horas_trabalhadas": horas_trabalhadas
        }

        self.menu.receber_alteracao((chave, itens))

    def importar_dados_mao_de_obra(
            self,
            ganho_por_hora: str,
            horas_trabalhadas: str
    ) -> None:
        """
        Recebe um conjunto de valores correspondentes às caixas quando um arquivo é aberto pelo Menu Principal.
        :return: None (Vazio).
        """
        self.var_ganho_por_hora.set(ganho_por_hora)
        self.var_horas_trabalhadas.set(horas_trabalhadas)

    def limpar_dados_mao_de_obra(self) -> None:
        """
        Limpa os dados nas caixas sempre que um novo arquivo é criado no Menu Principal.
        :return: None (Vazio).
        """
        for var in [
            self.var_ganho_por_hora,
            self.var_horas_trabalhadas
        ]:
            var.set("")

        self._atualizar_rotulo_mao_de_obra("0,00")