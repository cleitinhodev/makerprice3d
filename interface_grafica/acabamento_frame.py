import customtkinter as ctk
from customtkinter import CTkFrame


class AcabamentoFrame(ctk.CTkFrame):
    def __init__(self, master, calculadora, menu):
        """
        Classe responsável por receber e calcular os parâmetros relacionados a lavagem, lixa e pintura. Separado em
        3 blocos dedicados com seus próprios parâmetros individuais.
        :param master: Referência da qual esta janela está inserida.
        :param calculadora: Referência à calculadora geral do sistema.
        :param menu: Referência ao menu principal do sistema.
        """
        super().__init__(
            master,
            width=450,
            height=360,
            fg_color="#131313",
            border_width=2,
            border_color="#c2c2c2",
        )

        # /// Atributos e Objetos Principais ///////////////////////////////////////////
        self.calculadora_geral = calculadora
        self.menu = menu
        self.custo_total_lavagem = '0,00'
        self.custo_total_lixa = '0,00'
        self.custo_total_pintura = '0,00'

        # /// Variáveis de Controle ////////////////////////////////////////////////////
        # _______ Variáveis: Lavagem ___________________________________________________
        self.var_custo_solvente = ctk.StringVar()  # Custo médio 1L de solvente. (Álcool Isopropílico)
        self.var_lavagens_por_peca = ctk.StringVar()  # Quantidade média de lavagens possíveis por 1L até perder efeito.
        self.var_litros_usados = ctk.StringVar()  # Quantos litros foram usados na peça em questão.
        # _______ Variáveis: Lixa ______________________________________________________
        self.var_custo_de_ponta = ctk.StringVar()  # Custo médio de uma ponta de Micro Retifíca. (pode variar muito)
        self.var_vida_util_ponta = ctk.StringVar()  # Quantidade de usos até desgastar totalmente.
        self.var_pontas_usadas = ctk.StringVar()  # Quantidade de pontas utilizadas no processo.
        # _______ Variáveis: Pintura ___________________________________________________
        self.var_custo_unidade_tinta = ctk.StringVar()  # Custo médio de tinta em R$.
        self.var_ml_por_unidade = ctk.StringVar()  # Quantidade em (ml) por produto.
        self.var_uso_de_tinta_medio = ctk.StringVar()  # Quantos (ml) foram usados na peça toda.

        # /// Padrões e Personalização /////////////////////////////////////////////////
        self.FONTE_SIMPLES = ('Arial', 12)
        self.FONTE_NEGRITO = ('Segoe UI', 15, 'bold')

        # /// Título Principal /////////////////////////////////////////////////////////
        self.texto_titulo = ctk.CTkLabel(self, text='Acabamento', font=self.FONTE_NEGRITO)
        self.texto_titulo.place(relx=0.5, y=5, anchor="n")

        # /// Criação dos Frames + Widgets /////////////////////////////////////////////
        # _______ Variáveis: Lavagem ___________________________________________________
        self.rotulo_lavagem = None
        self.frame_lavagem = None
        self.titulos_indicativos_lavagem = {}
        self.caixas_de_entrada_lavagem = {}
        self.dados_dos_titulos_lavagem = [
            ('custo_solvente', 'Solvente 1L (R$)', 10),
            ('lavagens_por_peca', 'Qnt. Lavagens/1L', 80),
            ('litros_usados', 'Total Usado (L)', 150),
        ]  # chave, texto, y
        self.dados_caixas_de_entrada_lavagem = [
            ('custo_solvente', self.var_custo_solvente, 100, 35),
            ('lavagens_por_peca', self.var_lavagens_por_peca, 100, 105),
            ('litros_usados', self.var_litros_usados, 100, 175),
        ]  # chave, variável de controle, largura, y
        self.rotulo_custo_total_lavagem = None

        # _______ Variáveis: Lixa ______________________________________________________
        self.rotulo_lixa = None
        self.frame_lixa = None
        self.titulos_indicativos_lixa = {}
        self.caixas_de_entrada_lixa = {}
        self.dados_dos_titulos_lixa = [
            ('custo_de_ponta', 'Custo de Ponta(R$)', 10),
            ('vida_util_ponta', 'Vida Útil (qnt)', 80),
            ('pontas_usadas', 'Pontas Usadas (qnt)', 150),
        ]  # chave, texto, y
        self.dados_caixas_de_entrada_lixa = [
            ('custo_de_ponta', self.var_custo_de_ponta, 100, 35),
            ('vida_util_ponta', self.var_vida_util_ponta, 100, 105),
            ('pontas_usadas', self.var_pontas_usadas, 100, 175),
        ]  # chave, variável de controle, largura, y
        self.rotulo_custo_total_lixa = None

        # _______ Variáveis: Pintura ___________________________________________________
        self.rotulo_pintura = None
        self.frame_pintura = None
        self.titulos_indicativos_pintura = {}
        self.caixas_de_entrada_pintura = {}
        self.dados_dos_titulos_pintura = [
            ('custo_unidade_tinta', 'Custo Unidade(R$)', 10),
            ('ml_por_unidade', 'ml / Unidade', 80),
            ('uso_de_tinta_medio', 'Uso Médio (ml)', 150),
        ]  # chave, texto, y
        self.dados_caixas_de_entrada_pintura = [
            ('custo_unidade_tinta',self.var_custo_unidade_tinta, 100, 35),
            ('ml_por_unidade', self.var_ml_por_unidade, 100, 105),
            ('uso_de_tinta_medio', self.var_uso_de_tinta_medio, 100, 175),
        ]  # chave, variável de controle, largura, y
        self.rotulo_custo_total_pintura = None

        # _______ Chamadas _____________________________________________________________
        self._criar_aba_lavagem()
        self._criar_aba_lixa()
        self._criar_aba_pintura()

        # /// Eventos Automáticos //////////////////////////////////////////////////////
        # Lavagem
        for var in [self.var_custo_solvente, self.var_lavagens_por_peca, self.var_litros_usados]:
            var.trace_add("write", lambda *args, i='lavagem': self._recalcular_total(indice=i))

        # Lixa
        for var in [self.var_custo_de_ponta, self.var_vida_util_ponta, self.var_pontas_usadas]:
            var.trace_add("write", lambda *args, i='lixa': self._recalcular_total(indice=i))

        # Pintura
        for var in [self.var_custo_unidade_tinta, self.var_ml_por_unidade, self.var_uso_de_tinta_medio]:
            var.trace_add("write", lambda *args, i='pintura': self._recalcular_total(indice=i))

    # /// Métodos de construção ////////////////////////////////////////////////////////

    def _criar_aba_lavagem(self):
        # Título Principal
        self.rotulo_lavagem = ctk.CTkLabel(self, text='Lavagem',)
        self.rotulo_lavagem.place(x=50, y=35)

        # Frame
        self.frame_lavagem = ctk.CTkFrame(
            self,
            width=136,
            height=290,
            fg_color='#202020',
            border_width=1,
            border_color="#c2c2c2",
        )
        self.frame_lavagem.place(x=10, y=60)

        # Geração Títulos e Caixas de Entrada
        self.gerar_objetos(
            self.frame_lavagem,
            self.titulos_indicativos_lavagem,
            self.caixas_de_entrada_lavagem,
            self.dados_dos_titulos_lavagem,
            self.dados_caixas_de_entrada_lavagem, )

        # Rótulo que exibe total
        self.rotulo_custo_total_lavagem = ctk.CTkLabel(
            self.frame_lavagem,
            text=f'R$ {self.custo_total_lavagem:>7}',
            font=self.FONTE_NEGRITO,
            bg_color='#ffd24c',
            text_color='black',
            width=100,
            height=40,
        )
        self.rotulo_custo_total_lavagem.place(relx=0.5, y=230, anchor="n")

    def _criar_aba_lixa(self):
        # Título Principal
        self.rotulo_lixa = ctk.CTkLabel(self, text='Lixa')
        self.rotulo_lixa.place(x=210, y=35)

        # Frame
        self.frame_lixa = ctk.CTkFrame(
            self,
            width=136,
            height=290,
            fg_color='#202020',
            border_width=1,
            border_color="#c2c2c2",
        )
        self.frame_lixa.place(x=156, y=60)

        # Geração Títulos e Caixas de Entrada
        self.gerar_objetos(
            self.frame_lixa,
            self.titulos_indicativos_lixa,
            self.caixas_de_entrada_lixa,
            self.dados_dos_titulos_lixa,
            self.dados_caixas_de_entrada_lixa,
        )

        # Rótulo que exibe total
        self.rotulo_custo_total_lixa = ctk.CTkLabel(
            self.frame_lixa,
            text=f'R$ {self.custo_total_lixa:>7}',
            font=self.FONTE_NEGRITO,
            bg_color="#ff7afc",
            text_color='black',
            width=100,
            height=40,
        )
        self.rotulo_custo_total_lixa.place(relx=0.5, y=230, anchor="n")

    def _criar_aba_pintura(self):
        # Título Principal
        self.rotulo_pintura = ctk.CTkLabel(self, text='Pintura')
        self.rotulo_pintura.place(x=355, y=35)

        # Frame
        self.frame_pintura = ctk.CTkFrame(
            self,
            width=136,
            height=290,
            fg_color='#202020',
            border_width=1,
            border_color="#c2c2c2",
        )
        self.frame_pintura.place(x=303, y=60)

        # Geração Títulos e Caixas de Entrada
        self.gerar_objetos(
            self.frame_pintura,
            self.titulos_indicativos_pintura,
            self.caixas_de_entrada_pintura,
            self.dados_dos_titulos_pintura,
            self.dados_caixas_de_entrada_pintura,
        )

        # Rótulo que exibe total
        self.rotulo_custo_total_pintura = ctk.CTkLabel(
            self.frame_pintura,
            text=f'R$ {self.custo_total_pintura:>7}',
            font=self.FONTE_NEGRITO,
            bg_color="#4cfff6",
            text_color='black',
            width=100,
            height=40,
        )
        self.rotulo_custo_total_pintura.place(relx=0.5, y=230, anchor="n")

    @staticmethod
    def gerar_objetos(
            container: CTkFrame,
            memoria_titulos: dict,
            memoria_caixas: dict,
            dados_titulos: list,
            dados_caixas: list,
    ) -> None:
        """
        Gerador simples de títulos e caixas de entrada, auxilia na criação de widgets evitando repetições.

        :param container: Frame da qual os elementos irão pertencer.
        :param memoria_titulos: Dicionário onde serão armazenados os obtejos criados (Labels).
        :param memoria_caixas: Dicionário onde serão armazenados os obtejos criados (Entry).
        :param dados_titulos: Lista com informações que serão usadas nos títulos dos rótulos.
        :param dados_caixas: Lista com informações que serão usadas nas caixas de entrada.
        :return:
        """
        for chave, texto, y in dados_titulos:
            titulo = ctk.CTkLabel(
                container,
                text=texto,
            )
            titulo.place(relx=0.5, y=y, anchor="n")
            memoria_titulos[chave] = titulo

        for chave, var, largura, y in dados_caixas:
            caixa = ctk.CTkEntry(
                container,
                textvariable=var,
                width=largura,
            )
            caixa.place(relx=0.5, y=y, anchor="n")
            memoria_caixas[chave] = caixa

    # /// Métodos de cálculo ///////////////////////////////////////////////////////////
    def _obter_valores(self, indice: str) -> tuple:
        """
        Recolhe os valores inseridos nas caixas de texto e envia para conversão.
        :param indice: String que representa um indicador de quais grupos de variáveis obter os devidos valores.
        :return: Retorna uma tupla com valores já convertidos que serão armazenados nas respectivas variáveis.
        """
        if indice == 'lavagem':
            return (
                self.converter_float(self.var_custo_solvente.get()),
                self.converter_int(self.var_lavagens_por_peca.get()),
                self.converter_float(self.var_litros_usados.get()),
            )
        elif indice == 'lixa':
            return (
                self.converter_float(self.var_custo_de_ponta.get()),
                self.converter_int(self.var_vida_util_ponta.get()),
                self.converter_int(self.var_pontas_usadas.get()),
            )
        else:
            return (
                self.converter_float(self.var_custo_unidade_tinta.get()),
                self.converter_int(self.var_ml_por_unidade.get()),
                self.converter_int(self.var_uso_de_tinta_medio.get())
            )


    def _recalcular_total(self, indice: str, *args) -> None:
        """
        Realiza o processo de chamada de métodos, desde obter valores, realizar calculo e por fim atualizar os dados.
        :return: None (Vazio).
        """
        # Envia alterações para os metadados
        self._exportar_dados_acabamento()

        # Obtém, valída e calcula
        if indice == 'lavagem':
            custo_solvente, lavagens_por_peca, litros_usados = self._obter_valores(indice='lavagem')
            custo = self.calculo_custo_total_lavagem(custo_solvente, lavagens_por_peca, litros_usados)
        elif indice == 'lixa':
            custo_de_ponta, vida_util_ponta, pontas_usadas = self._obter_valores(indice='lixa')
            custo = self.calculo_custo_total_lixa(custo_de_ponta, vida_util_ponta, pontas_usadas)
        else:
            custo_unidade_tinta, ml_por_unidade, uso_de_tinta_medio = self._obter_valores(indice='pintura')
            custo = self.calculo_custo_total_pintura(custo_unidade_tinta, ml_por_unidade, uso_de_tinta_medio)

        valor_numerico = custo
        valor_formatado = f"{custo:.2f}".replace('.', ',')

        # Formata e atualiza objeto
        self._atualizar_rotulo_total_direcionado(valor=valor_formatado, indice=indice)

        # Envia as informações para fora, requisitando nova atualização da soma geral
        self.calculadora_geral.set_valor(indice, valor_numerico)
        self.calculadora_geral.atualizar_total()

    @staticmethod
    def calculo_custo_total_lavagem(
            custo_solvente: float,
            lavagens_por_peca: int,
            litros_usados: float,
    ) -> float:
        """
        Aplica uma fórmula simples que descobre quanto é gasto em média na lavagem de uma ou mais peças com base em
        custo e quantidade, isso pode variar, esta é apenas uma de várias fórmulas possíveis.
        :param custo_solvente: Custo médio de 1l de solvente.
        :param lavagens_por_peca: Quantidade média de lavagens até o solvente perder o efeito.
        :param litros_usados: Quantidade de litros usados na limpeza da peça.
        :return: Retorna o resultado da fórmula (custo_solvente / lavagens_por_peca) * litros_usados
        """
        if lavagens_por_peca == 0:  # Evita erro divisão por zero (Gambiarra, mas vou arrumar um dia :3)
            lavagens_por_peca = 1

        resultado = (custo_solvente / lavagens_por_peca) * litros_usados
        limite_maximo = 9999.99
        resultado = max(0, min(resultado, limite_maximo))
        return resultado

    @staticmethod
    def calculo_custo_total_lixa(
            custo_de_ponta: float,
            vida_util_ponta: int,
            pontas_usadas: int,
    ) -> float:
        """
        Aplica uma fórmula para descobrir o custo médio em acabamento com lixa, considerando o preço aproximado de uma
        ponta apesar do formato e numeração.
        :param custo_de_ponta: Custo médio de uma ponta para micro retificadora
        :param vida_util_ponta: Quantidade média de usos até a ponta se desgastar completamente.
        :param pontas_usadas: Quantidade de pontas usadas no acabamento da peça em questão.
        :return: Retorna o resultado da fórmula (custo_de_ponta / vida_util_ponta) * pontas_usadas
        """
        if vida_util_ponta == 0:
            vida_util_ponta = 1

        resultado = (custo_de_ponta / vida_util_ponta) * pontas_usadas
        limite_maximo = 9999.99
        resultado = max(0, min(resultado, limite_maximo))
        return resultado

    @staticmethod
    def calculo_custo_total_pintura(
            custo_unidade_tinta: float,
            ml_por_unidade: int,
            uso_de_tinta_medio: int,
    ) -> float:
        """
        Aplica uma fórmula simples de regra de três para descobrir quanto foi gasto em tinta.
        :param custo_unidade_tinta: Custo médio de um pote de tinta simples.
        :param ml_por_unidade: Quantidade de (ml) em cada pote.
        :param uso_de_tinta_medio: Total usado em (ml) na pintura.
        :return: Retorna o resultado da fórmula (custo_unidade_tinta * uso_de_tinta_medio) / ml_por_unidade
        """
        if ml_por_unidade == 0:
            ml_por_unidade = 1

        resultado = (custo_unidade_tinta * uso_de_tinta_medio) / ml_por_unidade
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
            return int(valor)
        except ValueError:
            return int(1)

    # /// Métodos de atualização ///////////////////////////////////////////////////////

    def _atualizar_rotulo_total_direcionado(self, valor: str, indice: str) -> None:
        """
        Apenas atualiza label de total do objeto, junto com a variável para possíveis alterações futuras.
        :param valor: Valor em texto já formatado.
        :param indice: Indice que orienta qual dos rótulos deve ser atualizado.
        :return: None (Vazio).
        """
        if indice == 'lavagem':
            self.custo_total_lavagem = valor
            self.rotulo_custo_total_lavagem.configure(
                text=f'R$ {self.custo_total_lavagem:>7}',
            )
        elif indice == 'lixa':
            self.custo_total_lixa = valor
            self.rotulo_custo_total_lixa.configure(
                text=f'R$ {self.custo_total_lixa:>7}',
            )
        else:
            self.custo_total_pintura = valor
            self.rotulo_custo_total_pintura.configure(
                text=f'R$ {self.custo_total_pintura:>7}',
            )

    # /// Métodos de Importação e Exportação ///////////////////////////////////////////
    def _exportar_dados_acabamento(self) -> None:
        """
        Envia os dados inseridos nas caixas para o sistema de Menu Principal que poderá salvá-los caso necessário.
        :return: None (Vazio).
        """
        self.menu.ativar_alteracao()

        # Lavagem
        custo_solvente = self.var_custo_solvente.get()
        lavagens_por_peca = self.var_lavagens_por_peca.get()
        litros_usados = self.var_litros_usados.get()

        # Lixa
        custo_de_ponta = self.var_custo_de_ponta.get()
        vida_util_ponta = self.var_vida_util_ponta.get()
        pontas_usadas = self.var_pontas_usadas.get()

        # Pintura
        custo_unidade_tinta = self.var_custo_unidade_tinta.get()
        ml_por_unidade = self.var_ml_por_unidade.get()
        uso_de_tinta_medio = self.var_uso_de_tinta_medio.get()

        chave = "acabamento"
        itens = {
            "lavagem": {
                "custo_solvente": custo_solvente,
                "lavagens_por_peca": lavagens_por_peca,
                "litros_usados": litros_usados
            },
            "lixa": {
                "custo_de_ponta": custo_de_ponta,
                "vida_util_ponta": vida_util_ponta,
                "pontas_usadas": pontas_usadas
            },
            "pintura": {
                "custo_unidade_tinta": custo_unidade_tinta,
                "ml_por_unidade": ml_por_unidade,
                "uso_de_tinta_medio": uso_de_tinta_medio
            }
        }

        self.menu.receber_alteracao((chave, itens))

    def importar_dados_acabamento(self, lavagem: dict, lixa: dict, pintura: dict) -> None:
        """
        Recebe um conjunto de valores correspondentes às caixas quando um arquivo é aberto pelo Menu Principal.
        :return: None (Vazio).
        """
        # Lavagem
        self.var_custo_solvente.set(lavagem.get("custo_solvente", ""))
        self.var_lavagens_por_peca.set(lavagem.get("lavagens_por_peca", ""))
        self.var_litros_usados.set(lavagem.get("litros_usados", ""))

        # Lixa
        self.var_custo_de_ponta.set(lixa.get("custo_de_ponta", ""))
        self.var_vida_util_ponta.set(lixa.get("vida_util_ponta", ""))
        self.var_pontas_usadas.set(lixa.get("pontas_usadas", ""))

        # Pintura
        self.var_custo_unidade_tinta.set(pintura.get("custo_unidade_tinta", ""))
        self.var_ml_por_unidade.set(pintura.get("ml_por_unidade", ""))
        self.var_uso_de_tinta_medio.set(pintura.get("uso_de_tinta_medio", ""))

    def limpar_dados_acabamento(self) -> None:
        """
        Limpa os dados nas caixas sempre que um novo arquivo é criado no Menu Principal.
        :return: None (Vazio).
        """
        for var in [
            self.var_custo_solvente,
            self.var_lavagens_por_peca,
            self.var_litros_usados,
            self.var_custo_de_ponta,
            self.var_vida_util_ponta,
            self.var_pontas_usadas,
            self.var_custo_unidade_tinta,
            self.var_ml_por_unidade,
            self.var_uso_de_tinta_medio
        ]:
            var.set("")

        self._atualizar_rotulo_total_direcionado("0,00", "lavagem")
        self._atualizar_rotulo_total_direcionado("0,00", "lixa")
        self._atualizar_rotulo_total_direcionado("0,00", "pintura")