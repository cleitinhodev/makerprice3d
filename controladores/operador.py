import customtkinter as ctk


class CalculadoraGeral:
    def __init__(self, master):
        """
        Classe responsável por realizar a soma e validação de todos os campos da interface principal.
        :param master: Referência da qual este objeto está inserido.
        """

        # /// Atributos e Objetos Principais ///////////////////////////////////////////
        self.master = master
        self.total_display = None

        self.valores = {
            "material": 0,
            "energia": 0,
            "desgaste": 0,
            "lavagem": 0,
            "lixa": 0,
            "pintura": 0,
            "despesas": 0,
            "logistica": 0,
            "mao_de_obra": 0
        }

        self.lucro = 0

        self.total_gasto = 0
        self.total_ganho = 0
        self.total_absoluto = 0
        self.sugestao = ['-', 'white']  # -, Prejuízo, Baixo, Ideal, Alto, Muito Alto

        self.CORES = {
            "vermelho": "#ff4c4c",
            "laranja": "#ff9f43",
            "amarelo": "#ffd24c",
            "verde": "#4cff4c",
            "azul": "#4c9dff",
        }

    # /// Métodos gerais ///////////////////////////////////////////////////////////////
    def set_widget_total(self, widget_total: ctk.CTkFrame) -> None:
        """
        Estabelece uma referência mútua com a classe que exibe o Total.
        :param widget_total: referência ao widget já criado.
        """
        self.total_display = widget_total

    def set_valor(self, chave: str, valor: float) -> None:
        """
        Recebe um valor numérico referente ao campo calculado e armazena no dicionário principal.
        :param chave: Chave simples que insere o valor no item correspondente.
        :param valor: Valor numérico representando o total somado.
        """
        if chave in self.valores:  # proteção simples
            self.valores[chave] = valor
            self.atualizar_total()

    def set_lucro(self, valor: int) -> None:
        """
        Define a porcentagem de lucro.
        :param valor: número de 0 a 100 que indica a porcentagem.
        """
        self.lucro = float(valor) / 100
        self.atualizar_total()

    def _soma_valores(self) -> None:
        """
        Realiza a soma dos valores com limites de segurança.
        """
        # Limita entre 0 e 9999.99
        self.total_gasto = max(0.0, min(9999.99, sum(self.valores.values())))

        self.total_ganho = self.total_gasto * self.lucro

        # Garante que o total não ultrapasse o limite
        if self.total_gasto + self.total_ganho > 9999.99:
            self.total_ganho = 9999.99 - self.total_gasto

        self.total_absoluto = self.total_gasto + self.total_ganho

    def _definir_sugestao(self) -> None:
        """
        Define a sugestão com base na porcentagem de lucro.
        """
        porcentagem = self.lucro * 100

        if porcentagem < 0:
            self.sugestao = ["Prejuízo", self.CORES["vermelho"]]
        elif porcentagem <= 10:
            self.sugestao = ["Baixo", self.CORES["laranja"]]
        elif porcentagem <= 30:
            self.sugestao = ["Ideal", self.CORES["verde"]]
        elif porcentagem <= 60:
            self.sugestao = ["Alto", self.CORES["azul"]]
        else:
            self.sugestao = ["Muito Alto", self.CORES["amarelo"]]

    def atualizar_total(self) -> None:
        """
        Atualiza todos os cálculos e envia os dados para o display.
        """
        self._soma_valores()
        self._definir_sugestao()

        # Dados para gráfico
        lista_para_grafico = list(self.valores.values()) + [self.total_ganho]

        # Remove valores negativos
        lista_filtrada = [max(0, item) for item in lista_para_grafico]

        # Resultados finais
        lista_de_resultados = [
            self.total_gasto,
            self.total_ganho,
            self.total_absoluto,
            self.sugestao
        ]

        # Atualiza interface (com proteção)
        if self.total_display:
            self.total_display.atualizar_grafico_delay(lista_filtrada)
            self.total_display.atualizar_display(lista_de_resultados)
