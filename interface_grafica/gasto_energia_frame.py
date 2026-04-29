import customtkinter as ctk
from ferramentas.calculadora_de_energia import JanelaConsumoEnergia


class GastoEnergiaFrame(ctk.CTkFrame):
    def __init__(self, master, calculadora, menu):
        """
        Classe responsável por receber e somar os parâmetros relacionados ao gasto em energia durante o processo de
        impressão, acabamento, lavagem e pintura. Fazendo apenas a soma dos valores já calculados.

        Observação: os valores devem ser obtidos através de uma das calculadoras disponíveis em ferramentas.
        :param master: Referência da qual esta janela está inserida.
        :param calculadora: Referência à calculadora geral do sistema.
        :param menu: Referência ao menu principal do sistema.
        """
        super().__init__(
            master,
            width=390,
            height=170,
            fg_color="#131313",
            border_width=2,
            border_color="#c2c2c2"
        )
        # /// Atributos e Objetos Principais ///////////////////////////////////////////
        self.calculadora_geral = calculadora
        self.menu = menu
        self.janela_calculadora_energetica = None
        self.custo_total_gasto_energia = '0,00'

        # /// Variáveis de Controle ////////////////////////////////////////////////////
        self.var_impressao = ctk.StringVar()  # Custo total de energia no uso da impressora 3D
        self.var_lixa_retificadora = ctk.StringVar()  # Custo total de energia no uso de lixa para acabamento
        self.var_lavagem_cura = ctk.StringVar()  # Custo total de energia no uso total da 'Wash and Cure'
        self.var_pintura = ctk.StringVar()  # Custo total de energia na pintura (compressor de ar, aerógrafo)

        # /// Padrões e Personalização /////////////////////////////////////////////////
        self.FONTE_SIMPLES = ('Arial', 12)
        self.FONTE_NEGRITO = ('Segoe UI', 15, 'bold')

        # /// Rótulos com textos indicativos ///////////////////////////////////////////
        self.titulos_indicativos = {}
        self.dados_dos_titulos = [
            ('gasto_energia', 'Gasto em Energia', 130, 5, True),
            ('impressao', 'Impressão', 35, 30, False),
            ('lixa_retificadora', 'Lixa (Retificadora)', 146, 30, False),
            ('lavagem_cura', 'Lavagem/CuraUV', 17, 90, False),
            ('pintura', 'Pintura(Aerógrafo)', 146, 90, False),
            ('custo_total', 'Custo Total', 290, 30, False),
        ]  # chave, texto, x, y, destaque

        for chave, texto, x, y, destaque in self.dados_dos_titulos:
            titulo = ctk.CTkLabel(
                self,
                text=texto,
                font=self.FONTE_NEGRITO if destaque else self.FONTE_SIMPLES,
            )
            titulo.place(x=x, y=y)
            self.titulos_indicativos[chave] = titulo

        # /// Caixas de Entrada Vazias /////////////////////////////////////////////////
        self.caixas_de_entrada = {}
        self.dados_das_caixas_de_entrada = [
            ('impressao', self.var_impressao, 100, 15, 55),
            ('lixa_retificadora', self.var_lixa_retificadora, 100, 145, 55),
            ('lavagem_cura', self.var_lavagem_cura, 100, 15, 115),
            ('pintura', self.var_pintura, 100, 145, 115),
        ]  # chave, variavel de controle, tamanho(largura), x, y

        for chave, var, largura, x, y in self.dados_das_caixas_de_entrada:
            caixa = ctk.CTkEntry(
                self,
                width=largura,
                textvariable=var,
            )
            caixa.place(x=x, y=y)
            self.caixas_de_entrada[chave] = caixa

        # /// Exibição: Resultado da Fórmula ///////////////////////////////////////////
        self.rotulo_total_gasto_em_energia = ctk.CTkLabel(
            self,
            text=f'R$ {self.custo_total_gasto_energia:>7}',
            text_color="black",
            font=self.FONTE_NEGRITO,
            bg_color="#4cff4c",
            width=100,
            height=40,
        )
        self.rotulo_total_gasto_em_energia.place(x=270, y=55)

        # /// Botão de Calculadora de Energia //////////////////////////////////////////
        self.calculadora_energia = ctk.CTkButton(
            self,
            text='Calcular KWh',
            width=50,
            height=35,
            fg_color="#4e3a95",
            hover_color="#696dbd",
            border_width=1,
            border_color="white",
            command=self._abrir_janela_consumo_energia
        )
        self.calculadora_energia.place(x=274, y=110)

        # /// Eventos Automáticos //////////////////////////////////////////////////////
        for var in [self.var_impressao, self.var_lixa_retificadora, self.var_lavagem_cura, self.var_pintura]:
            var.trace_add("write", self._recalcular_total)

    # /// Métodos de Ferramentas ///////////////////////////////////////////////////////
    def _abrir_janela_consumo_energia(self) -> None:
        """
        Abre uma nova janela de Calculadora de Energia Kwh para auxiliar usuário na definição de gastos.
        :return: None (Vazio).
        """
        if (
                self.janela_calculadora_energetica is None
                or not self.janela_calculadora_energetica.winfo_exists()
        ):
            self.janela_calculadora_energetica = JanelaConsumoEnergia(self)
        else:
            self.janela_calculadora_energetica.focus()

    # /// Métodos de cálculo ///////////////////////////////////////////////////////////
    def _obter_valores(self) -> tuple:
        """
        Recolhe os valores inseridos nas caixas de texto e envia para conversão.
        :return: Retorna uma tupla com valores já convertidos que serão armazenados nas respectivas variáveis.
        """
        return (
            self.converter_float(self.var_impressao.get()),
            self.converter_float(self.var_lixa_retificadora.get()),
            self.converter_float(self.var_lavagem_cura.get()),
            self.converter_float(self.var_pintura.get())
        )

    def _recalcular_total(self, *args) -> None:
        """
        Realiza o processo de chamada de métodos, desde obter valores, realizar calculo e por fim atualizar os dados.
        :return: None (Vazio).
        """
        # Envia alterações para os metadados
        self._exportar_dados_energia()

        # Obtém, valída e calcula
        impressao, lixa_retificadora, lavagem_cura, pintura = self._obter_valores()
        custo = self.calculo_gasto_em_energia(impressao, lixa_retificadora, lavagem_cura, pintura)

        valor_numerico = custo
        valor_formatado = f"{custo:.2f}".replace('.', ',')

        # Formata e atualiza objeto
        self._atualizar_rotulo_total_gasto_em_energia(valor=valor_formatado)

        # Envia as informações para fora, requisitando nova atualização da soma geral
        self.calculadora_geral.set_valor("energia", valor_numerico)
        self.calculadora_geral.atualizar_total()

    @staticmethod
    def calculo_gasto_em_energia(
            impressao: float,
            lixa_retificadora: float,
            lavagem_cura: float,
            pintura: float) -> float:
        """
        Aplica uma simples soma para descobrir quanto em energia foi gasto durante o processo inteiro:
        :param impressao: Custo total em R$ do consumo de energia com base no tempo de impressão.
        :param lixa_retificadora: Custo total em R$ do consumo de energia com base no acabamento (lixa, perfurações...).
        :param lavagem_cura: Custo total em R$ do consumo de energia com base na lavagem e cura UV da peça.
        :param pintura: Custo total em R$ do consumo de energia com base na pintura com aerógrafo (compressor de ar).
        :return: Resultado da Soma (impressão + lixa retificadora + + lavagem e cura UV + pintura)

        Obs: Para descobrir o consumo, use a calculadora disponível em ferramentas, a fórmula Kwh está nela.
        """
        resultado = impressao + lixa_retificadora + lavagem_cura + pintura
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

    def _atualizar_rotulo_total_gasto_em_energia(self, valor: str) -> None:
        """
        Apenas atualiza label de total do objeto, junto com a variável para possíveis alterações futuras.
        :param valor: Valor em texto já formatado.
        :return: None (Vazio).
        """
        self.custo_total_gasto_energia = valor
        self.rotulo_total_gasto_em_energia.configure(
            text=f'R$ {self.custo_total_gasto_energia:>7}',
        )


    # /// Métodos de Importação e Exportação ///////////////////////////////////////////
    def _exportar_dados_energia(self) -> None:
        """
        Envia os dados inseridos nas caixas para o sistema de Menu Principal que poderá salvá-los caso necessário.
        Obs: A chave é importante para saber onde exatamente as informações devem ser armazenadas.
        :return: None (Vazio).
        """
        self.menu.ativar_alteracao()

        impressao = self.var_impressao.get()
        lixa_retificadora = self.var_lixa_retificadora.get()
        lavagem_cura = self.var_lavagem_cura.get()
        pintura = self.var_pintura.get()

        chave = "energia"
        itens = {
            "impressao": impressao,
            "lixa_retificadora": lixa_retificadora,
            "lavagem_cura": lavagem_cura,
            "pintura": pintura
        }

        self.menu.receber_alteracao((chave, itens))

    def importar_dados_energia(
            self,
            impressao: str,
            lixa_retificadora: str,
            lavagem_cura: str,
            pintura: str
    ) -> None:
        """
        Recebe um conjunto de valores correspondentes às caixas quando um arquivo é aberto pelo Menu Principal.
        :param impressao: Insere dados na caixa -> var_impressao
        :param lixa_retificadora: Insere dados na caixa -> var_lixa_retificadora
        :param lavagem_cura: Insere dados na caixa -> var_lavagem_cura
        :param pintura: Insere dados na caixa -> var_pintura
        :return: None (Vazio).
        """
        self.var_impressao.set(impressao)
        self.var_lixa_retificadora.set(lixa_retificadora)
        self.var_lavagem_cura.set(lavagem_cura)
        self.var_pintura.set(pintura)

    def limpar_dados_energia(self) -> None:
        """
        Limpa os dados nas caixas sempre que um novo arquivo é criado no Menu Principal.
        :return: None (Vazio).
        """
        for var in [
            self.var_impressao,
            self.var_lixa_retificadora,
            self.var_lavagem_cura,
            self.var_pintura
        ]:
            var.set("")

        self._atualizar_rotulo_total_gasto_em_energia("0,00")