import customtkinter as ctk
import webbrowser
import os
from PIL import Image


class JanelaSobre(ctk.CTkToplevel):
    def __init__(self, master=None):
        """
        Janela responsável por exibir informações sobre o software.
        :param master: Referência da qual esta janela está inserida.
        """
        super().__init__(master)

        # /// Configurações Padrão /////////////////////////////////////////////////////
        self.master = master
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.title("Sobre")
        self.geometry("360x570")
        self.resizable(False, False)
        self.configure(fg_color="#1a1a1a")
        self._centralizar()
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)
        self.after(100, lambda: self.attributes("-topmost", False))
        self.update_idletasks()
        #self.grab_set()

        # /// Logo /////////////////////////////////////////////////////////////////////
        caminho_logo = os.path.join("assets", "logo.png")

        if os.path.exists(caminho_logo):
            self.logo_img = ctk.CTkImage(
                light_image=Image.open(caminho_logo),
                size=(200, 200)
            )

            self.label_logo = ctk.CTkLabel(self, image=self.logo_img, text="")
            self.label_logo.pack(pady=(15, 5))

        # /// Título + Versão //////////////////////////////////////////////////////////
        self.label_titulo = ctk.CTkLabel(
            self,
            text="Maker Price 3D",
            font=("Courier", 18, "bold")
        )
        self.label_titulo.pack(pady=(5, 0))

        self.label_versao = ctk.CTkLabel(
            self,
            text="v1.0",
            font=("Courier", 10)
        )
        self.label_versao.pack(pady=(0, 10))

        # /// Desenvolvedor ////////////////////////////////////////////////////////////
        self.label_dev = ctk.CTkLabel(
            self,
            text="Desenvolvido por:\nCleitinhoDEV",
            font=("Courier", 14, "bold"),
            fg_color="#131313",
            corner_radius=10
        )
        self.label_dev.pack(padx=15, pady=10, fill="x")

        # /// Frame Principal //////////////////////////////////////////////////////////
        self.frame_info = ctk.CTkFrame(self, fg_color="#242424", corner_radius=12)
        self.frame_info.pack(padx=15, pady=10, fill="both", expand=True)

        # /// Site Oficial /////////////////////////////////////////////////////////////
        self.label_site = ctk.CTkLabel(
            self.frame_info,
            text="Site Oficial",
            font=("Courier", 13, "bold")
        )
        self.label_site.pack(pady=(10, 2))

        self.link_site = ctk.CTkLabel(
            self.frame_info,
            text="https://www.bugzinho.com/",
            font=("Courier", 12, "underline"),
            text_color="#4ea6ff",
            cursor="hand2"
        )
        self.link_site.pack()
        self.link_site.bind("<Button-1>", lambda e: self._abrir_link("https://www.bugzinho.com/"))

        # /// Doações /////////////////////////////////////////////////////////////////
        self.label_doacao = ctk.CTkLabel(
            self.frame_info,
            text="Doações",
            font=("Courier", 13, "bold")
        )
        self.label_doacao.pack(pady=(10, 2))

        self.link_doacao = ctk.CTkLabel(
            self.frame_info,
            text="https://www.bugzinho.com/donate",
            font=("Courier", 12, "underline"),
            text_color="#4ea6ff",
            cursor="hand2"
        )
        self.link_doacao.pack()
        self.link_doacao.bind("<Button-1>", lambda e: self._abrir_link("https://www.bugzinho.com/donate"))

        # /// Bugs /////////////////////////////////////////////////////////////////////
        self.label_bug = ctk.CTkLabel(
            self.frame_info,
            text="Reportar Bugs",
            font=("Courier", 13, "bold")
        )
        self.label_bug.pack(pady=(10, 2))

        self.email_bug = ctk.CTkLabel(
            self.frame_info,
            text="cleitinhodev@outlook.com",
            font=("Courier", 12, "underline"),
            text_color="#4ea6ff",
            cursor="hand2"
        )
        self.email_bug.pack()
        self.email_bug.bind("<Button-1>", lambda e: self._abrir_link("cleitinhodev@outlook.com"))

        # /// Rodapé ///////////////////////////////////////////////////////////////////
        self.label_final = ctk.CTkLabel(
            self,
            text="Obrigado pelo apoio! :)",
            font=("Courier", 12)
        )
        self.label_final.pack(pady=(5, 15))

    # /// Métodos de Janela ////////////////////////////////////////////////////////////
    def _centralizar(self) -> None:
        self.update_idletasks()

        largura = self.winfo_width()
        altura = self.winfo_height()

        largura_tela = self.winfo_screenwidth()
        altura_tela = self.winfo_screenheight()

        x = (largura_tela // 2) - (largura // 2)
        y = (altura_tela // 2) - (altura // 2)

        self.geometry(f"{largura}x{altura}+{x}+{y}")

    def _ao_fechar(self) -> None:
        self.master.focus()
        self.withdraw()
        self.update_idletasks()
        self.master.janela_sobre = None
        self.destroy()

    # /// Utilidades /////////////////////////////////////////////////////////////////
    @staticmethod
    def _abrir_link(url: str) -> None:
        webbrowser.open(url)