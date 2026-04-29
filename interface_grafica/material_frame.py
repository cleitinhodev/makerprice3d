import customtkinter as ctk


class MaterialFrame(ctk.CTkFrame):
    def __init__(self, master, calculadora, menu):
        """
        Classe responsável por receber e calcular os parâmetros relacionados ao material utilizado no dimensionamento
        da impressão 3D.
        Ela coleta valores como custo da resina, quantidade utilizada e volume de suportes, auxiliando o usuário a
        estimar o custo total da impressão.

        Observação: os valores devem ser obtidos diretamente do fatiador.

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
        self.custo_total_material = '0,00'

        # /// Variáveis de Controle ////////////////////////////////////////////////////
        self.var_resina = ctk.StringVar() # Custo de Resina por 1kg
        self.var_suporte = ctk.StringVar() # % de Suportes ultizados na peça (Pode variar conforme o modelo)
        self.var_peso = ctk.StringVar() # Peso da peça em (g)
        self.var_fixo = ctk.StringVar() # Valor fixo da peça, seria como um "preço mínimo" independente do restante.

        # /// Padrões e Personalização /////////////////////////////////////////////////
        self.FONTE_SIMPLES = ('Arial', 12)
        self.FONTE_NEGRITO = ('Segoe UI', 15, 'bold')

        # /// Rótulos com textos indicativos ///////////////////////////////////////////
        self.titulos_indicativos = {}
        self.dados_dos_titulos = [
            ('material', 'Material', 165, 5, True),
            ('resina', 'Resina 1Kg (R$)', 20, 30, False),
            ('suportes', 'Suportes (%)', 160, 30, False),
            ('peso', 'Peso da Peça (g)', 17, 90, False),
            ('custo_fixo', 'Custo Fixo', 167, 90, False),
            ('custo_total', 'Custo Total', 290, 50, False),
        ]  # chave, texto, x, y, destaque

        for chave, texto, x, y, destaque in self.dados_dos_titulos:
            titulo = ctk.CTkLabel(
                self,
                text=texto,
                font=self.FONTE_NEGRITO if destaque else self.FONTE_SIMPLES
            )
            titulo.place(x=x, y=y)
            self.titulos_indicativos[chave] = titulo

        # /// Caixas de Entrada Vazias /////////////////////////////////////////////////
        self.caixas_de_entrada = {}
        self.dados_das_caixas_de_entrada = [
            ('resina', self.var_resina, 100, 15, 55),
            ('suportes', self.var_suporte, 100, 145, 55),
            ('peso', self.var_peso, 100, 15, 115),
            ('custo_fixo', self.var_fixo, 100, 145, 115),
        ] # chave, variavel de controle, tamanho(largura), x, y

        for chave, var, largura, x, y in self.dados_das_caixas_de_entrada:
            caixa = ctk.CTkEntry(
                self,
                textvariable=var,
                width=largura,
            )
            caixa.place(x=x, y=y)
            self.caixas_de_entrada[chave] = caixa

        # /// Exibição: Resultado da Fórmula ///////////////////////////////////////////
        self.rotulo_custo_total_material = ctk.CTkLabel(
            self,
            text=f'R$ {self.custo_total_material:>7}',
            text_color="white",
            font=self.FONTE_NEGRITO,
            bg_color="#ff4c4c",
            width=100,
            height=40,
        )
        self.rotulo_custo_total_material.place(x=270, y=75)

        # /// Eventos Automáticos //////////////////////////////////////////////////////
        for var in [self.var_resina, self.var_suporte, self.var_peso, self.var_fixo]:
            var.trace_add("write", self._recalcular_total)

    # /// Métodos de cálculo ///////////////////////////////////////////////////////////
    def _obter_valores(self) -> tuple:
        """
        Recolhe os valores inseridos nas caixas de texto e envia para conversão.
        :return: Retorna uma tupla com valores já convertidos que serão armazenados nas respectivas variáveis.
        """
        return (
            self.converter_float(self.var_resina.get()),
            self.converter_float(self.var_suporte.get()),
            self.converter_float(self.var_peso.get()),
            self.converter_float(self.var_fixo.get())
        )

    def _recalcular_total(self, *args) -> None:
        """
        Realiza o processo de chamada de métodos, desde obter valores, realizar calculo e por fim atualizar os dados.
        :return: None (Vazio).
        """
        # Envia alterações para os metadados
        self._exportar_dados_material()

        # Obtém, valída e calcula
        resina, suporte, peso, fixo = self._obter_valores()
        custo = self.calculo_gasto_material(resina, suporte, peso, fixo)

        valor_numerico = custo
        valor_formatado = f"{custo:.2f}".replace('.', ',')

        # Formata e atualiza objeto
        self._atualizar_rotulo_custo_total_material(valor=valor_formatado)

        # Envia as informações para fora, requisitando nova atualização da soma geral
        self.calculadora_geral.set_valor("material", valor_numerico)
        self.calculadora_geral.atualizar_total()

    @staticmethod
    def calculo_gasto_material(
            resina: float,
            suporte: float,
            peso: float,
            fixo: float) -> float:
        """
        Aplica uma fórmula para descobrir quanto em dinheiro foi gasto através do peso em resina:
        :param resina: Custo do 1kg em resina (Qualquer tipo, o importante é o preço)
        :param suporte: % de suportes utilizados para imprimir a peça (Opcional)
        :param peso: Peso em (g) usado para imprimir a peça (Alguns fatiadores somam com suporte, cuidado!)
        :param fixo: Custo fixo cobrado pela peça independente do material gasto (Opcional)
        :return: Resultado da Fórmula ((peso / 1000) * resina) * (1 + suporte / 100) + fixo
        """
        resultado = ((peso / 1000) * resina) * (1 + suporte / 100) + fixo
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

    def _atualizar_rotulo_custo_total_material(self, valor: str) -> None:
        """
        Apenas atualiza label de total do objeto, junto com a variável para possíveis alterações futuras.
        :param valor: Valor em texto já formatado.
        :return: None (Vazio).
        """
        self.custo_total_material = valor
        self.rotulo_custo_total_material.configure(
            text=f'R$ {self.custo_total_material:>7}',
        )

    # /// Métodos de Importação e Exportação ///////////////////////////////////////////
    def _exportar_dados_material(self) -> None:
        """
        Envia os dados inseridos nas caixas para o sistema de Menu Principal que poderá salvá-los caso necessário.
        Obs: A chave é importante para saber onde exatamente as informações devem ser armazenadas.
        :return: None (Vazio).
        """
        self.menu.ativar_alteracao()

        resina = self.var_resina.get()
        suporte = self.var_suporte.get()
        peso = self.var_peso.get()
        custo_fixo = self.var_fixo.get()

        chave = "material"
        itens = {"resina": resina, "suporte": suporte, "peso": peso, "custo_fixo": custo_fixo}

        self.menu.receber_alteracao((chave, itens))

    def importar_dados_material(self, resina: str, suporte: str, peso: str, custo_fixo: str) -> None:
        """
        Recebe um conjunto de valores correspondentes às caixas quando um arquivo é aberto pelo Menu Principal.
        :param resina: Insere dados na caixa -> var_resina
        :param suporte: Insere dados na caixa -> var_suporte
        :param peso: Insere dados na caixa -> var_peso
        :param custo_fixo: Insere dados na caixa -> var_fixo
        :return: None (Vazio).
        """
        self.var_resina.set(resina)
        self.var_suporte.set(suporte)
        self.var_peso.set(peso)
        self.var_fixo.set(custo_fixo)

    def limpar_dados_material(self) -> None:
        """
        Limpa os dados nas caixas sempre que um novo arquivo é criado no Menu Principal.
        :return: None (Vazio).
        """
        for var in [self.var_resina, self.var_suporte, self.var_peso, self.var_fixo]:
            var.set("")

        self._atualizar_rotulo_custo_total_material("0,00")