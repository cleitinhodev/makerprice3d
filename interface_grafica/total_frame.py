import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class TotalFrame(ctk.CTkFrame):
    def __init__(self, master, calculadora, menu):
        """
        Área responsável por exibir a soma total de despesas na (impressão, acabamento e entrega) + lucro.
        :param master: Referência da qual esta janela está inserida.
        :param calculadora: Referência à calculadora geral do sistema.
        :param menu: Referência ao menu principal do sistema.
        """
        super().__init__(
            master,
            width=400,
            height=368,
            fg_color="#131313",
            border_width=2,
            border_color="#c2c2c2"
        )

        # /// Atributos e Objetos Principais ///////////////////////////////////////////
        self.calculadora_geral = calculadora
        self.menu = menu
        self.porcentagem_lucro = 0
        self.valor_total_gasto = '0,00'
        self.valor_total_ganho = '0,00'
        self.valor_total_absoluto = '0,00'
        self.sugestao = ['-', 'white'] # -, Prejuízo, Baixo, Ideal, Alto, Muito Alto
        self.valores_atuais = [1] * 10

        # /// Padrões e Personalização /////////////////////////////////////////////////
        self.FONTE_SIMPLES = ('Arial', 12)
        self.FONTE_TITULOS = ("Arial", 15, "bold")
        self.FONTE_NEGRITO = ('Segoe UI', 18, 'bold')

        # /// Títulos: Total, Lucro Estimado ///////////////////////////////////////////
        self.texto_titulo = ctk.CTkLabel(self, text="Total", font=self.FONTE_TITULOS)
        self.texto_titulo.place(relx=0.5, y=5, anchor="n")

        self.rotulo_lucro = ctk.CTkLabel(
            self,
            text=f"Lucro Estimado: {self.porcentagem_lucro}%",
            font=self.FONTE_TITULOS
        )
        self.rotulo_lucro.place(relx=0.5, y=35, anchor="n")

        # /// Slider de Lucro e chamada de gráfico /////////////////////////////////////
        self.slider_lucro = ctk.CTkSlider(
            self,
            from_=0,
            to=100,
            number_of_steps=100,
            command=self._atualizar_valor_lucro,
            width=350,
            button_color="#ff4c9d",
            button_hover_color="#fda8ce"
        )
        self.slider_lucro.place(relx=0.5, y=65, anchor="n")
        self.slider_lucro.set(0)

        self._criar_grafico()

        # /// Geração de legendas //////////////////////////////////////////////////////
        self.cores = {}
        self.legendas = {}

        self.cores_dados = [
            ("cor_material", "#ff4c4c", 25, 141),
            ("cor_gasto_energia", "#4cff4c", 100, 141),
            ("cor_desgaste", "#4c4cff", 170, 141),
            ("cor_lavagem", "#ffd24c", 250, 141),
            ("cor_lixa", "#ff7afc", 330, 141),

            ("cor_pintura", "#4cfff6", 15, 166),
            ("cor_gasto_despesas", "#f26522", 80, 166),
            ("cor_logistica", "#9d4cff", 165, 166),
            ("cor_mao_de_obra", "#4cff9d", 242, 166),
            ("cor_lucro", "#ff4c9d", 335, 166),
        ] # chave, cor hex, x, y

        self.legendas_dados = [
            ("rotulo_cor_material", "Material", 42, 135),
            ("rotulo_cor_gasto_energia", "Energia", 117, 135),
            ("rotulo_cor_desgaste", "Desgaste", 187, 135),
            ("rotulo_cor_lavagem", "Lavagem", 267, 135),
            ("rotulo_cor_lixa", "Lixa", 347, 135),

            ("rotulo_cor_pintura", "Pintura", 32, 160),
            ("rotulo_cor_gasto_despesas", "Despesas", 97, 160),
            ("rotulo_cor_logistica", "Logística", 182, 160),
            ("rotulo_cor_mao_de_obra", "Mão de Obra", 259, 160),
            ("rotulo_cor_lucro", "Lucro", 352, 160),
        ] # chave, texto, x, y

        for nome, cor, x, y in self.cores_dados:
            self.cores[nome] = ctk.CTkLabel(
                self,
                text='',
                corner_radius=100,
                width=15,
                height=5,
                fg_color=cor
            )
            self.cores[nome].place(x=x, y=y)

        for nome, texto, x, y in self.legendas_dados:
            self.legendas[nome] = ctk.CTkLabel(self, text=texto)
            self.legendas[nome].place(x=x, y=y)

        # /// Geração de métricas //////////////////////////////////////////////////////
        self.frames_de_metrica = {}
        self.dados_frames_de_metricas = [("total_gasto", 10), ("total_ganho", 140), ("sugestao", 270)] # chave, x

        for chave, x in self.dados_frames_de_metricas:
            self.frames_de_metrica[chave] = ctk.CTkFrame(
                self,
                width=120,
                height=65,
                fg_color="#131313",
                border_width=2,
                border_color="#c2c2c2"
            )
            self.frames_de_metrica[chave].place(x=x, y=195)

        self.rotulos_de_metrica = {}
        self.dados_rotulos_de_metrica = [
            ("total_gasto", self.frames_de_metrica["total_gasto"],
             "Total Gasto", self.FONTE_SIMPLES, 2),
            ("total_ganho", self.frames_de_metrica["total_ganho"],
             "Lucro", self.FONTE_SIMPLES, 2),
            ("sugestao", self.frames_de_metrica["sugestao"],
             "Sugestão", self.FONTE_SIMPLES, 2),

            ("total_gasto_valor", self.frames_de_metrica["total_gasto"],
             f"R$ {self.valor_total_gasto:>7}", self.FONTE_NEGRITO, 30),
            ("total_ganho_valor", self.frames_de_metrica["total_ganho"],
             f"R$ {self.valor_total_ganho:>7}", self.FONTE_NEGRITO, 30),
            ("sugestao_valor", self.frames_de_metrica["sugestao"],
             f"{self.sugestao[0]:^10}", self.FONTE_NEGRITO, 30),
        ] # chave, master, texto, fonte, y

        for chave, master, texto, fonte, y in self.dados_rotulos_de_metrica:
            self.rotulos_de_metrica[chave] = ctk.CTkLabel(master, text=texto, font=fonte,)
            self.rotulos_de_metrica[chave].place(relx=0.5, y=y, anchor="n")

        # /// Exibição: Total Absoluto /////////////////////////////////////////////////
        self.rotulo_total_absoluto = ctk.CTkLabel(
            self,
            text=f'R$ {self.valor_total_absoluto:>7}',
            font=('Arial', 70),
            fg_color='#0b0b0b',
            width=380,
            height=100,
            corner_radius=10
        )
        self.rotulo_total_absoluto.place(relx=0.5, y=260, anchor="n")

    # /// Métodos de Geração ///////////////////////////////////////////////////////////
    def _criar_grafico(self) -> None:
        """
        Cria e configura o gráfico horizontal empilhado utilizando matplotlib,
        integrando-o à interface Tkinter.

        O gráfico é inicializado com valores fictícios apenas para estrutura visual,
        definindo cores, fundo e removendo elementos como eixos e bordas para manter
        um visual limpo.

        O canvas do matplotlib é criado apenas uma vez e incorporado ao frame,
        permitindo que atualizações futuras sejam feitas de forma eficiente sem
        recriação do gráfico.

        Ao final, chama o método de atualização para aplicar os valores reais iniciais.
        :return: None (Vazio).
        """
        valores = [50, 30, 20]
        cores = ["#ff4c4c", "#4cff4c", "#4c4cff"]

        self.fig = Figure(figsize=(3.9, 0.5), dpi=100)
        self.ax = self.fig.add_subplot(111)

        cor_fundo = "#131313"
        self.fig.patch.set_facecolor(cor_fundo)
        self.ax.set_facecolor(cor_fundo)

        esquerda = 0
        for valor, cor in zip(valores, cores):
            self.ax.barh(0, valor, left=esquerda, color=cor)
            esquerda += valor

        self.ax.set_yticks([])
        self.ax.set_xticks([])
        self.ax.set_frame_on(False)

        # canvas criado UMA vez só
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().place(relx=0.5, y=85, anchor="n")

        # mantém a lógica
        self.atualizar_grafico([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])

    # /// Métodos de atualização ///////////////////////////////////////////////////////
    def _atualizar_valor_lucro(self, valor: float) -> None:
        """
        Atualiza a porcentagem de lucro com base no valor do slider,
        refletindo a mudança na interface e na lógica da calculadora.

        O valor recebido é convertido para inteiro e exibido no rótulo,
        além de ser enviado para a calculadora geral responsável pelos cálculos.
        :param valor: Valor do slider no intervalo de 0 a 100.
        :return: None (Vazio).
        """
        # Envia alterações para os metadados
        self._exportar_dados_total(valor)

        self.porcentagem_lucro = int(valor)
        self.rotulo_lucro.configure(
            text=f"Lucro Estimado: {self.porcentagem_lucro}%"
        )
        self.calculadora_geral.set_lucro(self.porcentagem_lucro)

    def atualizar_grafico(self, valores: list) -> None:
        """
        Atualiza o gráfico horizontal empilhado com novos valores.

        Os valores são normalizados proporcionalmente para ocupar 100% da largura,
        permitindo a visualização relativa de cada componente dentro do total.
        O gráfico é limpo e redesenhado sem recriar o canvas, garantindo melhor performance.

        :param valores: Lista de valores numéricos que representam cada categoria.
        :return: None (Vazio).
        """
        cores_base = [
            "#ff4c4c", "#4cff4c", "#4c4cff", "#ffd24c", "#ff7afc",
            "#4cfff6", "#f26522", "#9d4cff", "#4cff9d", "#ff4c9d",
            "#00c2ff", "#c2ff00", "#ff006e", "#8338ec", "#3a86ff"
        ]

        cores = [cores_base[i % len(cores_base)] for i in range(len(valores))]

        # só limpa o gráfico (não recria)
        self.ax.clear()

        cor_fundo = "#131313"
        self.fig.patch.set_facecolor(cor_fundo)
        self.ax.set_facecolor(cor_fundo)

        total = sum(valores) if sum(valores) != 0 else 1

        esquerda = 0
        for valor, cor in zip(valores, cores):
            largura = valor / total * 100
            # removido height → volta ao visual original
            self.ax.barh(0, largura, left=esquerda, color=cor)
            esquerda += largura

        self.ax.set_xlim(0, 100)
        self.ax.set_yticks([])
        self.ax.set_xticks([])
        self.ax.set_frame_on(False)

        # redesenho leve
        self.canvas.draw_idle()

    def atualizar_grafico_delay(self, valores: list) -> None:
        """
        Agenda a atualização animada do gráfico com um pequeno atraso (debounce),
        evitando múltiplas execuções consecutivas quando o método é chamado rapidamente.

        Caso já exista uma atualização pendente, ela é cancelada antes de agendar a nova,
        garantindo que apenas a última chamada seja executada.

        :param valores: Lista de valores que serão utilizados na animação do gráfico.
        :return: None
        """
        if hasattr(self, "_after_id"):
            self.after_cancel(self._after_id)

        self._after_id = self.after(80, lambda: self._animar_grafico(valores))

    def _animar_grafico(self, novos_valores: list, steps=10, delay=20) -> None:
        """
        Realiza uma animação suave de transição entre os valores atuais do gráfico
        e novos valores, utilizando interpolação linear.

        A animação ocorre em múltiplos passos, redesenhando o gráfico gradualmente
        até atingir os valores finais. Caso a quantidade de valores seja diferente
        da atual, a atualização ocorre instantaneamente sem animação.
        :param novos_valores: Lista de valores finais que serão exibidos no gráfico.
        :param steps: Quantidade de etapas da animação (quanto maior, mais suave).
        :param delay: Intervalo em milissegundos entre cada etapa da animação.
        :return: None (Vazio).
        """
        # Se tamanho diferente, evita erro
        if len(novos_valores) != len(self.valores_atuais):
            self.valores_atuais = novos_valores
            self.atualizar_grafico(novos_valores)
            return

        antigos = self.valores_atuais.copy()

        def interpolar(t):
            return [
                antigos[i] + (novos_valores[i] - antigos[i]) * t
                for i in range(len(novos_valores))
            ]

        def step(i=0):
            t = i / steps
            valores_interpolados = interpolar(t)

            self.atualizar_grafico(valores_interpolados)

            if i < steps:
                self.after(delay, lambda: step(i + 1))
            else:
                self.valores_atuais = novos_valores

        step()

    def atualizar_display(self, resultados: list) -> None:
        """
        Recebe um conjunto de dados já calculados e atualiza os respectivos displays conforme seus endereços.
        :param resultados: Lista no formato:
            [total_gasto, total_ganho, total_absoluto, sugestao]
            onde sugestao é uma estrutura contendo texto e cor.
        :return: None (Vazio).
        """
        self.valor_total_gasto = resultados[0]
        self.valor_total_ganho = resultados[1]
        self.valor_total_absoluto = resultados[2]
        self.sugestao = resultados[3]


        self.rotulos_de_metrica["total_gasto_valor"].configure(
            text=f'R$ {self.valor_total_gasto:>7.2f}'.replace('.', ','))
        self.rotulos_de_metrica["total_ganho_valor"].configure(
            text=f'R$ {self.valor_total_ganho:>7.2f}'.replace('.', ','))
        self.rotulos_de_metrica["sugestao_valor"].configure(
            text=self.sugestao[0], text_color=self.sugestao[1])
        self.rotulo_total_absoluto.configure(
            text=f'R$ {self.valor_total_absoluto:>7.2f}'.replace('.', ','))

    # /// Métodos de Importação e Exportação ///////////////////////////////////////////
    def _exportar_dados_total(self, estado: int) -> None:
        """
        Envia os dados do slider para o sistema de Menu Principal que poderá salvá-lo caso necessário.
        Obs: A chave é importante para saber onde exatamente as informações devem ser armazenadas.
        :return: None (Vazio).
        """

        self.menu.ativar_alteracao()

        estado_slider = int(estado)
        chave = "lucro"
        itens = {"estado": estado_slider}
        self.menu.receber_alteracao((chave, itens))

    def importar_dados_total(self, estado: int) -> None:
        """
        Recebe um novo estado quando um arquivo é aberto pelo Menu Principal.
        :return: None (Vazio).
        """
        self.slider_lucro.set(estado)
        self._atualizar_valor_lucro(float(estado))

    def limpar_dados_total(self) -> None:
        """
        Reseta o slider sempre que um novo arquivo é criado no Menu Principal.
        :return: None (Vazio).
        """
        self.slider_lucro.set(0)
        self._atualizar_valor_lucro(float(0))

    def pegar_total(self):
        try:
            total = float(self.valor_total_absoluto)
            return total
        except ValueError:
            return 0.0