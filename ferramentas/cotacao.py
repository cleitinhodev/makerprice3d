import customtkinter as ctk
import requests


class JanelaConversorMoedas(ctk.CTkToplevel):
    def __init__(self, master=None, total_absoluto=0.0):
        """
        Janela responsável por exibir conversões de moeda com base em um valor recebido.
        :param master: Referência da qual esta janela está inserida.
        :param total_absoluto: Referência ao total somado no sistema.
        """
        super().__init__(master)

        # /// Configurações Padrão /////////////////////////////////////////////////////
        self.master = master
        self.total_absoluto = total_absoluto
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.title("Conversor de Moedas")
        self.geometry("400x500")
        self.resizable(False, False)
        self.configure(fg_color="#1a1a1a")
        self._centralizar()
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)
        self.after(100, lambda: self.attributes("-topmost", False))
        self.grab_set()


        # /// Variáveis ////////////////////////////////////////////////////////////////
        self.valor_base = 0.0

        # /// Título Principal /////////////////////////////////////////////////////////
        self.label_titulo = ctk.CTkLabel(
            self,
            text="Cotações em Tempo Real",
            font=("Courier", 18, "bold")
        )
        self.label_titulo.pack(pady=(15, 10))

        # /// Frame Principal //////////////////////////////////////////////////////////
        self.frame_moedas = ctk.CTkFrame(self, fg_color="#242424", corner_radius=12)
        self.frame_moedas.pack(padx=15, pady=10, fill="both", expand=True)

        # /// Configuração Grid ////////////////////////////////////////////////////////
        for i in range(5):
            self.frame_moedas.grid_rowconfigure(i, weight=1)

        for j in range(2):
            self.frame_moedas.grid_columnconfigure(j, weight=1)

        # /// Lista de Moedas //////////////////////////////////////////////////////////
        self.moedas = [
            "USD", "EUR",
            "GBP", "JPY",
            "AUD", "CAD",
            "CHF", "CNY",
            "ARS", "BTC"
        ]

        self.labels = {}

        # /// Criação dos Labels ///////////////////////////////////////////////////////
        index = 0
        for i in range(5):
            for j in range(2):
                moeda = self.moedas[index]

                label = ctk.CTkLabel(
                    self.frame_moedas,
                    text=f"{moeda}:\n-,-",
                    font=('Courier', 14, 'bold'),
                    fg_color="#131313",
                    corner_radius=10,
                    width=160,
                    height=60
                )

                label.grid(row=i, column=j, padx=5, pady=5, sticky="nsew")
                self.labels[moeda] = label

                index += 1

        # /// Label Base ///////////////////////////////////////////////////////////////
        self.label_base = ctk.CTkLabel(
            self,
            text="Valor Base:\nR$ 0,00",
            font=('Courier', 16, 'bold'),
            fg_color="#131313",
            corner_radius=10
        )
        self.label_base.pack(padx=15, pady=(5, 15), fill="x")

        self.atualizar_valor(self.total_absoluto)

    # /// Métodos de Janela ////////////////////////////////////////////////////////////
    def _centralizar(self) -> None:
        """
        Centraliza a janela.
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
        Fecha a janela corretamente e limpa referência.
        :return: None (Vazio).
        """
        self.master.focus()
        self.withdraw()
        self.update_idletasks()
        self.master.janela_conversor_moedas = None
        self.destroy()

    # /// Métodos de Atualização ///////////////////////////////////////////////////////
    def atualizar_valor(self, valor: float) -> None:
        """
        Recebe um valor base e atualiza as conversões.
        :param valor: float (Valor em reais)
        :return: None (Vazio).
        """
        self.valor_base = valor

        valor_formatado = f"{valor:.2f}".replace('.', ',')
        self.label_base.configure(text=f"Valor Base:\nR$ {valor_formatado}")

        self._buscar_cotacoes()

    def _buscar_cotacoes(self) -> None:
        """
        Busca cotações em tempo real e atualiza a interface.
        :return: None (Vazio).
        """
        try:
            url = "https://api.exchangerate-api.com/v4/latest/BRL"
            response = requests.get(url, timeout=5)

            if response.status_code != 200:
                raise Exception

            dados = response.json()
            rates = dados.get("rates", {})

            for moeda, label in self.labels.items():
                if moeda in rates:
                    valor_convertido = self.valor_base * rates[moeda]

                    if moeda == "JPY":
                        texto = f"{valor_convertido:.0f}"
                    else:
                        texto = f"{valor_convertido:.2f}"

                    texto = texto.replace('.', ',')

                    label.configure(text=f"{moeda}:\n{texto}")
                else:
                    label.configure(text=f"{moeda}:\n-,-")

        except Exception:
            self._fallback()

    def _fallback(self) -> None:
        """
        Caso não consiga obter dados, limpa os valores.
        :return: None (Vazio).
        """
        for moeda, label in self.labels.items():
            label.configure(text=f"{moeda}:\n-,-")