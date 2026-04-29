import customtkinter as ctk


class JanelaConsumoEnergia(ctk.CTkToplevel):
    def __init__(self, master=None):
        """
        Janela responsável por realizar calculo simples de gasto de energia.
        :param master: Referência da qual esta janela está inserida.
        """
        super().__init__(master)

        # /// Configurações Padrão /////////////////////////////////////////////////////
        self.master = master
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.title("Consumo de Energia")
        self.geometry("350x600")
        self.resizable(False, False)
        self.configure(fg_color="#1a1a1a")
        self._centralizar()  # trava foco na janela
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)
        self.after(100, lambda: self.attributes("-topmost", False))

        # /// Título Principal /////////////////////////////////////////////////////////
        self.label_titulo_principal = ctk.CTkLabel(
            self,
            text="Calculadora de Consumo",
            font=("Courier", 18, "bold")
        )
        self.label_titulo_principal.pack(pady=(15, 10))

        # /// Frame: campos de consumo /////////////////////////////////////////////////
        self.frame_campos_de_consumo = ctk.CTkFrame(self, fg_color="#242424", corner_radius=12)
        self.frame_campos_de_consumo.pack(padx=15, pady=10, fill="both", expand=True)

        # /// Geração de Campos  ///////////////////////////////////////////////////////
        self.campo_potencia = self._criar_input("Potência (W)", "Ex: 1500")
        self.campo_tempo = self._criar_input("Minutos por dia", "Ex: 10")
        self.campo_dias = self._criar_input("Dias por mês", "Ex: 30")
        self.campo_valor = self._criar_input("R$/kWh", "Ex: 0.80")

        # /// Botão de Calculo /////////////////////////////////////////////////////////
        self.botao_calcular = ctk.CTkButton(
            self.frame_campos_de_consumo,
            text="Calcular",
            command=self.calcular,
            fg_color="#4e3a95",
            hover_color="#696dbd",
            border_width=1,
            border_color="white",
        )
        self.botao_calcular.pack(pady=15, padx=15, fill="x")

        # /// Resultados ///////////////////////////////////////////////////////////////
        self.frame_rotulos_de_exibicao = ctk.CTkFrame(
            self.frame_campos_de_consumo,
            fg_color="#1a1a1a",
        )
        self.frame_rotulos_de_exibicao.pack(pady=(10, 15))

        # Faz o grid expandir corretamente
        self.frame_rotulos_de_exibicao.grid_columnconfigure(0, weight=1)
        self.frame_rotulos_de_exibicao.grid_columnconfigure(1, weight=1)
        self.frame_rotulos_de_exibicao.grid_rowconfigure(0, weight=1)
        self.frame_rotulos_de_exibicao.grid_rowconfigure(1, weight=1)

        # Labels de cima (lado a lado)
        self.rotulo_esquerda = ctk.CTkLabel(
            self.frame_rotulos_de_exibicao,
            font=('Courier', 15, 'bold'),
            text=f"Consumo:\n0.0 kWh",
            width=145,
            height=60,
            fg_color="#131313",
            corner_radius=10,
        )
        self.rotulo_esquerda.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.rotulo_direita = ctk.CTkLabel(
            self.frame_rotulos_de_exibicao,
            font=('Courier', 15, 'bold'),
            text=f"Custo Mensal:\nR$ 0,00",
            width=145,
            height=60,
            fg_color="#131313",
            corner_radius=10,
        )
        self.rotulo_direita.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # Label de baixo (ocupa as duas colunas)
        self.rotulo_inferior = ctk.CTkLabel(
            self.frame_rotulos_de_exibicao,
            font=('Courier', 20, 'bold'),
            text=f"Custo Diário:\nR$ 0,00",
            width=290,
            height=60,
            fg_color="#131313",
            corner_radius=10,
        )
        self.rotulo_inferior.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)


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
        self.master.janela_calculadora_energetica = None
        self.destroy()

    # /// Métodos de geração ///////////////////////////////////////////////////////////
    def _criar_input(self, texto: str, placeholder: str) -> ctk.CTkEntry:
        """
        Gera uma caixa de texto com um rótulo acima.
        :param texto: Texto que será exibido no rótulo.
        :param placeholder: Texto fantasma que fica dentro da caixa como exemplo.
        :return: ctk.CTkEntry (Objeto do tipo Entry)
        """
        label = ctk.CTkLabel(self.frame_campos_de_consumo, text=texto)
        label.pack(anchor="w", padx=15, pady=(10, 0))

        entry = ctk.CTkEntry(self.frame_campos_de_consumo, placeholder_text=placeholder)
        entry.pack(padx=15, pady=5, fill="x")

        return entry

    # /// Métodos de calculo ///////////////////////////////////////////////////////////
    def calcular(self) -> None:
        """
        Recolhe os valores das caixas de texto, e se forem válidos, realiza um calculo de consumo kWh.
        Potência (W): Potência especificada no aparelho. (pode variar e nem sempre é constante)
        Minutos (m): Quantidade de minutos em que o aparelho permanece ligado por dia.
        Dias (d): Dias de uso por mês.
        Valor (kWh): custo em kW (1000 Watts) por hora. (Pode variar conforme a região e empresa fornecedora.)
        :return: None (Vazio).
        """
        try:
            # Captura valores das caixas, converte em strings e verifica se estão ou não vazios.
            potencia_str = self.campo_potencia.get().strip()
            minutos_str = self.campo_tempo.get().strip()
            dias_str = self.campo_dias.get().strip()
            valor_kwh_str = self.campo_valor.get().strip()

            if not potencia_str or not minutos_str or not dias_str or not valor_kwh_str:
                raise ValueError

            # Converte para float e verifica se são maiores que 0.
            potencia = float(potencia_str.replace(",", "."))
            minutos = float(minutos_str.replace(",", "."))
            dias = float(dias_str.replace(",", "."))
            valor_kwh = float(valor_kwh_str.replace(",", "."))

            if potencia < 0 or minutos < 0 or dias < 0 or valor_kwh < 0:
                raise ValueError

            # Converte minutos em horas, e realiza as fórmulas para descobrir consumo.
            horas = minutos / 60

            consumo_dia = (potencia * horas) / 1000
            consumo_mes = consumo_dia * dias
            custo_mes = consumo_mes * valor_kwh
            custo_dia = consumo_dia * valor_kwh

            consumo_mes_formatado = f"{consumo_mes:.2f}".replace('.', ',')
            custo_mes_formatado = f"{custo_mes:.2f}".replace('.', ',')
            custo_dia_formatado = f"{custo_dia:.2f}".replace('.', ',')

            # Muda os valores nos rótulos de resultado.
            self.rotulo_esquerda.configure(
                text=f"Consumo:\n{consumo_mes_formatado} kWh"
            )

            self.rotulo_direita.configure(
                text=f"Custo Mensal:\nR$ {custo_mes_formatado}"
            )

            self.rotulo_inferior.configure(
                text=f"Custo Diário:\nR$ {custo_dia_formatado}"
            )

        except ValueError:
            self.rotulo_esquerda.configure(text=f"Consumo:\n-.- kWh")
            self.rotulo_direita.configure(text=f"Custo Mensal:\nR$ -,--")
            self.rotulo_inferior.configure(text=f"Preencha todos \nos campos corretamente.")

