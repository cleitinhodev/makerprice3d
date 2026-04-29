import customtkinter as ctk

class DesgasteFrame(ctk.CTkFrame):
    def __init__(self, master, calculadora, menu):
        """
        Classe responsável por calcular gastos relacionados a peças da impressora, desde LCD, até consumíveis como FEP.
        :param master: Referência da qual esta janela está inserida.
        :param calculadora: Referência à calculadora geral do sistema.
        :param menu: Referência ao menu principal do sistema.
        """
        super().__init__(
            master,
            width=390,
            height=320,
            fg_color="#131313",
            border_width=2,
            border_color="#c2c2c2"
        )

        # /// Atributos e Objetos Principais ///////////////////////////////////////////
        self.calculadora_geral = calculadora
        self.menu = menu
        self.custo_total_desgaste = '0,00'

        # /// Variáveis de Controle ////////////////////////////////////////////////////
        self.var_preco_lcd = ctk.StringVar()  # Preço médio de um lcd para impressora 3D. (pode variar muito)
        self.var_vida_util = ctk.StringVar()  # Vida útil em horas do lcd especificado.
        self.var_tempo_total = ctk.StringVar()  # Tempo de impressão em horas da peça em questão.
        self.var_preco_fep = ctk.StringVar()  # Preço médio de Fep para o Vat.
        self.var_durabilidade = ctk.StringVar()  # Quantidade de impressões média por Fep.
        self.var_porcentagem_area = ctk.StringVar()  # Porcentagem (%) de area usada na impressão.
        self.var_manutencao_fixa_extra = ctk.StringVar()  # Quantia extra a ser adicionada por razões individuais.

        # /// Padrões e Personalização /////////////////////////////////////////////////
        self.FONTE_SIMPLES = ('Arial', 12)
        self.FONTE_NEGRITO = ('Segoe UI', 15, 'bold')

        # /// título geral /////////////////////////////////////////////////////////////
        self.texto_titulo = ctk.CTkLabel(self, text='Desgaste', font=('Arial', 15, 'bold'))
        self.texto_titulo.pack(padx=10, pady=5)

        # /// criação de frames ////////////////////////////////////////////////////////
        self.desgaste_frames = {}
        self.dados_frames = [
            ('frame_lcd', 370, 95, '#202020', 10, 6),
            ('frame_fep', 370, 95, '#202020', 10, 6),
            ('frame_manutencao', 370, 55, '#202020', 10, 6),
        ] # chave, largura(width), altura(height), cor(fg_color), padx, pady

        for chave, largura, altura, cor, px, py in self.dados_frames:
            frame = ctk.CTkFrame(self, width=largura, height=altura, fg_color=cor)
            frame.pack(padx=px, pady=py)
            self.desgaste_frames[chave] = frame

        # /// criação de títulos ///////////////////////////////////////////////////////

        self.texto_titulo_lcd = ctk.CTkLabel(self.desgaste_frames['frame_lcd'], text='LCD', font=('Arial', 12))
        self.texto_titulo_lcd.place(relx=0.5, y=0, anchor="n")
        self.texto_titulo_fep = ctk.CTkLabel(self.desgaste_frames['frame_fep'], text='FEP', font=('Arial', 12))
        self.texto_titulo_fep.place(relx=0.5, y=0, anchor="n")
        self.texto_titulo_manutenção_fixa_extra = ctk.CTkLabel(
            self.desgaste_frames['frame_manutencao'],
            text='Manutenção(Fixa/Extra):',
            font=('Arial', 12, 'bold'),
        )
        self.texto_titulo_manutenção_fixa_extra.place(x=2, y=12)
        self.texto_igual = ctk.CTkLabel(self.desgaste_frames['frame_manutencao'], text='=', font=('Arial', 18, 'bold'))
        self.texto_igual.place(x=245, y=12)

        # /// criação de textos ////////////////////////////////////////////////////////
        self.textos_indicativos = {}
        self.dados_textos = [
            ('texto_preco_lcd', 'frame_lcd', 'Preço LCD (R$)', 12, 23),
            ('texto_vida_util', 'frame_lcd', 'Vida Útil (h)', 155, 23),
            ('texto_tempo_total', 'frame_lcd', 'Tempo Total (h)', 272, 23),
            ('texto_preco_fep', 'frame_fep', 'Preço FEP (R$)', 12, 23),
            ('texto_durabilidade', 'frame_fep', 'Durabilidade (qnt)', 138, 23),
            ('texto_porcentagem_area', 'frame_fep', 'Area (%)', 292, 23),
        ] # chave, frame, texto, x, y

        for chave, frame, texto, x, y in self.dados_textos:
            rotulo = ctk.CTkLabel(self.desgaste_frames[frame], text=texto, font=self.FONTE_SIMPLES)
            rotulo.place(x=x, y=y)
            self.textos_indicativos[chave] = rotulo

        # /// Caixas de Entrada Vazias /////////////////////////////////////////////////
        self.caixas_de_entrada = {}
        self.dados_das_caixas_de_entrada = [
            ('caixa_preco_lcd', 'frame_lcd', self.var_preco_lcd, 5, 48),
            ('caixa_vida_util', 'frame_lcd', self.var_vida_util, 135, 48),
            ('caixa_tempo_total', 'frame_lcd', self.var_tempo_total, 265, 48),
            ('caixa_preco_fep', 'frame_fep', self.var_preco_fep, 5, 48),
            ('caixa_durabilidade', 'frame_fep', self.var_durabilidade, 135, 48),
            ('caixa_porcentagem_area', 'frame_fep', self.var_porcentagem_area, 265, 48),
            ('caixa_manutenção_fixa_extra', 'frame_manutencao', self.var_manutencao_fixa_extra, 140, 12),
        ] # chave, frame, variavel de controle, x, y

        for chave, frame, var, x, y in self.dados_das_caixas_de_entrada:
            caixa = ctk.CTkEntry(self.desgaste_frames[frame], textvariable=var, width=100)
            caixa.place(x=x, y=y)
            self.caixas_de_entrada[chave] = caixa

        # /// Exibição: Resultado da Fórmula ///////////////////////////////////////////
        self.rotulo_custo_total_desgaste = ctk.CTkLabel(
            self.desgaste_frames['frame_manutencao'],
            text=f'R$ {self.custo_total_desgaste:>7}',
            font=self.FONTE_NEGRITO,
            bg_color='#4c4cff',
            width=100,
            height=40
        )
        self.rotulo_custo_total_desgaste.place(x=260, y=7)

        # /// Eventos Automáticos //////////////////////////////////////////////////////
        for var in [
            self.var_preco_lcd,
            self.var_vida_util,
            self.var_tempo_total,
            self.var_preco_fep,
            self.var_durabilidade,
            self.var_porcentagem_area,
            self.var_manutencao_fixa_extra,
        ]:
            var.trace_add("write", self._recalcular_total)

    # /// Métodos de cálculo ///////////////////////////////////////////////////////////
    def _obter_valores(self) -> tuple:
        """
        Recolhe os valores inseridos nas caixas de texto e envia para conversão.
        :return: Retorna uma tupla com valores já convertidos que serão armazenados nas respectivas variáveis.
        """
        return (
            self.converter_float(self.var_preco_lcd.get()),
            self.converter_int(self.var_vida_util.get()),
            self.converter_int(self.var_tempo_total.get()),
            self.converter_float(self.var_preco_fep.get()),
            self.converter_int(self.var_durabilidade.get()),
            self.converter_para_porcentagem(self.var_porcentagem_area.get()),
            self.converter_float(self.var_manutencao_fixa_extra.get())
        )

    def _recalcular_total(self, *args) -> None:
        """
        Realiza o processo de chamada de métodos, desde obter valores, realizar calculo e por fim atualizar os dados.
        :return: None (Vazio).
        """
        # Envia alterações para os metadados
        self._exportar_dados_desgaste()

        # Obtém, valída e calcula
        (preco_lcd,
         vida_util,
         tempo_total,
         preco_fep,
         durabilidade,
         porcentagem_area,
         manutencao_fixa_extra) = self._obter_valores()

        custo = self.calculo_desgaste(
            preco_lcd,
            vida_util,
            tempo_total,
            preco_fep,
            durabilidade,
            porcentagem_area,
            manutencao_fixa_extra
        )

        valor_numerico = custo
        valor_formatado = f"{custo:.2f}".replace('.', ',')

        # Formata e atualiza objeto
        self._atualizar_rotulo_desgaste(valor=valor_formatado)

        # Envia as informações para fora, requisitando nova atualização da soma geral
        self.calculadora_geral.set_valor("desgaste", valor_numerico)
        self.calculadora_geral.atualizar_total()

    @staticmethod
    def calculo_desgaste(
        preco_lcd: float,
        vida_util: int,
        tempo_total: int,
        preco_fep: float,
        durabilidade: int,
        porcentagem_area: float,
        manutencao_fixa_extra: float
    ) -> float:
        """
        Aplica uma fórmula que descobre o valor aproximado de desgaste das peças da máquina, LCD, FEP, etc.

        obs: 0.33 na fórmula representa 1/3 adicional devido a desgastes invisíveis como quantidade de camadas, sucção,
        ou tensão do material, são valores invisíveis e difíceis de dimensionar, mas também importantes.

        :param preco_lcd: Preço médio de um LCD novo.
        :param vida_util: Vida útil total em horas do produto.
        :param tempo_total: Tempo médio da impressão atual.
        :param preco_fep: Preço médio de um FEP novo.
        :param durabilidade: Quantidade média de usos (impressões) até desgastar completamente
        :param porcentagem_area: Porcentagem média da area usada do FEP para gerar a pela atual.
        :param manutencao_fixa_extra: Manutenção extra com parafusos, filtro, proteção. (Opcional)
        :return: Resultado da Fórmula ((preco_lcd / vida_util) * tempo_total) + ((preco_fep / durabilidade)
            * (porcentagem_area + 0.33)) + manutencao_fixa_extra
        """
        try:
            resultado = (((preco_lcd / vida_util) * tempo_total) +
                        ((preco_fep / durabilidade) * (porcentagem_area + 0.33)) + manutencao_fixa_extra)
        except ZeroDivisionError:
            resultado = 0.0

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
            return int(0)

        try:
            return int(valor)
        except ValueError:
            return int(0)

    @staticmethod
    def converter_para_porcentagem(valor: str) -> float:
        """
        Pega o valor na caixa de entrada e tenta converter para porcentagem (float/100)
        :param valor: Somente valores numéricos, evitando letras ou símbolos.
        :return: Retorna o número já convertido para porcentagem, em caso de erro retorna 1.0 (100%)
        """
        if not valor:
            return float(1.0)

        try:
            return float(valor) / 100
        except ValueError:
            return float(1.0)

    # /// Métodos de atualização ///////////////////////////////////////////////////////
    def _atualizar_rotulo_desgaste(self, valor: str) -> None:
        """
        Apenas atualiza label de total do objeto, junto com a variável para possíveis alterações futuras.
        :param valor: Valor em texto já formatado.
        :return: None (Vazio).
        """
        self.custo_total_desgaste = valor
        self.rotulo_custo_total_desgaste.configure(
            text=f'R$ {self.custo_total_desgaste:>7}',
        )

    # /// Métodos de Importação e Exportação ///////////////////////////////////////////
    def _exportar_dados_desgaste(self) -> None:
        """
        Envia os dados inseridos nas caixas para o sistema de Menu Principal que poderá salvá-los caso necessário.
        Obs: A chave é importante para saber onde exatamente as informações devem ser armazenadas.
        :return: None (Vazio).
        """
        self.menu.ativar_alteracao()

        preco_lcd = self.var_preco_lcd.get()
        vida_util = self.var_vida_util.get()
        tempo_total = self.var_tempo_total.get()
        preco_fep = self.var_preco_fep.get()
        durabilidade = self.var_durabilidade.get()
        porcentagem_area = self.var_porcentagem_area.get()
        manutencao_fixa_extra = self.var_manutencao_fixa_extra.get()

        chave = "desgaste"
        itens = {
            "preco_lcd": preco_lcd,
            "vida_util": vida_util,
            "tempo_total": tempo_total,
            "preco_fep": preco_fep,
            "durabilidade": durabilidade,
            "porcentagem_area": porcentagem_area,
            "manutencao_fixa_extra": manutencao_fixa_extra
        }

        self.menu.receber_alteracao((chave, itens))

    def importar_dados_desgaste(
        self,
        preco_lcd: str,
        vida_util: str,
        tempo_total: str,
        preco_fep: str,
        durabilidade: str,
        porcentagem_area: str,
        manutencao_fixa_extra: str
    ) -> None:
        """
        Recebe um conjunto de valores correspondentes às caixas quando um arquivo é aberto pelo Menu Principal.
        :return: None (Vazio).
        """
        self.var_preco_lcd.set(preco_lcd)
        self.var_vida_util.set(vida_util)
        self.var_tempo_total.set(tempo_total)
        self.var_preco_fep.set(preco_fep)
        self.var_durabilidade.set(durabilidade)
        self.var_porcentagem_area.set(porcentagem_area)
        self.var_manutencao_fixa_extra.set(manutencao_fixa_extra)

    def limpar_dados_desgaste(self) -> None:
        """
        Limpa os dados nas caixas sempre que um novo arquivo é criado no Menu Principal.
        :return: None (Vazio).
        """
        for var in [
            self.var_preco_lcd,
            self.var_vida_util,
            self.var_tempo_total,
            self.var_preco_fep,
            self.var_durabilidade,
            self.var_porcentagem_area,
            self.var_manutencao_fixa_extra
        ]:
            var.set("")

        self._atualizar_rotulo_desgaste("0,00")