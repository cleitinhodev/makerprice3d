# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev

import customtkinter as ctk
from interface_grafica.menu_principal import MenuPrincipal
from interface_grafica.material_frame import MaterialFrame
from interface_grafica.gasto_energia_frame import GastoEnergiaFrame
from interface_grafica.desgaste_frame import DesgasteFrame
from interface_grafica.acabamento_frame import AcabamentoFrame
from interface_grafica.despesas_frame import DespesasFrame
from interface_grafica.logistica_frame import LogisticaFrame
from interface_grafica.mao_de_obra import MaoDeObraFrame
from interface_grafica.total_frame import TotalFrame
from controladores import operador
from tkinter import messagebox

class JanelaPrincipal:
    """
    Classe responsável por representar e gerenciar a janela principal da aplicação.

    Coordena a criação dos componentes visuais (frames), integra o sistema de cálculo
    e controla o fluxo geral dos dados entre interface e lógica.
    """
    def __init__(self, master):
        """
        Inicializa a janela principal e seus componentes.

        :param master: Janela raiz (CTk).
        """
        # /// Atributos e Objetos Principais ///////////////////////////////////////////
        self.root = master
        self.titulo_principal = "Maker Price 3D"
        self.nome_do_arquivo = "Sem Título"
        self._configurar_janela()

        # Widgets
        self.menu = None
        self.material = None
        self.gasto_em_energia = None
        self.desgaste = None
        self.acabamento = None
        self.despesas = None
        self.logistica = None
        self.mao_de_obra = None
        self.total = None
        self.calculadora_geral = operador.CalculadoraGeral(self.root)

        # /// Chamada de Eventos ///////////////////////////////////////////////////////
        self._criar_widgets()
        self.calculadora_geral.set_widget_total(self.total)



    # /// Métodos de Aplicação /////////////////////////////////////////////////////////
    def _configurar_janela(self) -> None:
        """
        Define propriedades da janela principal, como tamanho e posição.
        """
        largura = 1280
        altura = 720

        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()

        x = (largura_tela // 2) - (largura // 2)
        y = (altura_tela // 2) - (altura // 2)

        self.root.geometry(f"{largura}x{altura}+{x}+{y}")
        self.root.title(f"{self.titulo_principal} - {self.nome_do_arquivo}")
        self.root.resizable(False, False)

    # /// Métodos de Geração ///////////////////////////////////////////////////////////
    def _criar_widgets(self) -> None:
        """
        Cria e posiciona todos os componentes da interface gráfica (frames).
        """
        self.menu = MenuPrincipal(self.root, self)
        self.menu.pack(fill="x")
        self.material = MaterialFrame(self.root, self.calculadora_geral, self.menu)
        self.material.place(x=10, y=35)
        self.gasto_em_energia = GastoEnergiaFrame(self.root, self.calculadora_geral, self.menu)
        self.gasto_em_energia.place(x=10, y=215)
        self.desgaste = DesgasteFrame(self.root, self.calculadora_geral, self.menu)
        self.desgaste.place(x=10, y=395)
        self.acabamento = AcabamentoFrame(self.root, self.calculadora_geral, self.menu)
        self.acabamento.place(x=410, y=35)
        self.despesas = DespesasFrame(self.root, self.calculadora_geral, self.menu)
        self.despesas.place(x=410, y=405)
        self.logistica = LogisticaFrame(self.root, self.calculadora_geral, self.menu)
        self.logistica.place(x=870, y=35)
        self.mao_de_obra = MaoDeObraFrame(self.root, self.calculadora_geral, self.menu)
        self.mao_de_obra.place(x=870, y=215)
        self.total = TotalFrame(self.root, self.calculadora_geral, self.menu)
        self.total.place(x=870, y=345)

    # /// Métodos de Fluxo do Sistema //////////////////////////////////////////////////
    def limpar_todas_as_caixas(self) ->None:
        """
        Limpa todos os campos de entrada da aplicação e reseta o gráfico.
        """
        self.material.limpar_dados_material()
        self.gasto_em_energia.limpar_dados_energia()
        self.desgaste.limpar_dados_desgaste()
        self.acabamento.limpar_dados_acabamento()
        self.despesas.limpar_dados_despesas()
        self.logistica.limpar_dados_logistica()
        self.mao_de_obra.limpar_dados_mao_de_obra()
        self.total.limpar_dados_total()

        self.total.atualizar_grafico_delay([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])

    def reescrever_todas_as_caixas(self, dados: dict) -> bool:
        """
        Preenche todos os campos da interface com dados carregados de um arquivo.

        :param dados: Dicionário contendo os dados estruturados do sistema.
        :return: True se os dados foram aplicados com sucesso, False caso contrário.
        """
        try:
            material = dados["material"]
            self.material.importar_dados_material(material["resina"],
                                                  material["suporte"],
                                                  material["peso"],
                                                  material["custo_fixo"])
            energia = dados["energia"]
            self.gasto_em_energia.importar_dados_energia(energia["impressao"],
                                                         energia["lixa_retificadora"],
                                                         energia["lavagem_cura"],
                                                         energia["pintura"])
            desgaste = dados["desgaste"]
            self.desgaste.importar_dados_desgaste(desgaste["preco_lcd"],
                                                  desgaste["vida_util"],
                                                  desgaste["tempo_total"],
                                                  desgaste["preco_fep"],
                                                  desgaste["durabilidade"],
                                                  desgaste["porcentagem_area"],
                                                  desgaste["manutencao_fixa_extra"])
            acabamento = dados["acabamento"]
            self.acabamento.importar_dados_acabamento(acabamento["lavagem"],
                                                      acabamento["lixa"],
                                                      acabamento["pintura"])
            despesas = dados["despesas"]
            self.despesas.importar_dados_despesas(despesas["tabela"])
            logistica = dados["logistica"]
            self.logistica.importar_dados_logistica(logistica["embrulho"],
                                                    logistica["descontos"],
                                                    logistica["impostos"],
                                                    logistica["frete"])
            mao_de_obra = dados["mao_de_obra"]
            self.mao_de_obra.importar_dados_mao_de_obra(mao_de_obra["ganho_por_hora"],
                                                        mao_de_obra["horas_trabalhadas"])
            lucro = dados["lucro"]
            self.total.importar_dados_total(lucro["estado"])

            return True

        except KeyError:
            messagebox.showerror("Erro", "Arquivo inválido: chave(s) não encontrada(s).")
            self.menu.resetar_atributos()
            return False
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado:\n{e}")
            self.menu.resetar_atributos()
            return False

    def renomear_titulo(self, nome_arquivo: str) -> None:
        """
        Atualiza o título da janela com base no nome do arquivo atual.

        :param nome_arquivo: Nome do arquivo carregado/salvo.
        """
        self.nome_do_arquivo = nome_arquivo.replace(".json", "")
        self.root.title(f"{self.titulo_principal} - {self.nome_do_arquivo}")

    def solicitar_total_absoluto(self) -> float:
        """
        Obtém o valor total calculado no sistema.

        :return: Valor total absoluto.
        """
        total_absoluto = self.total.pegar_total()
        return total_absoluto


def iniciar_janela_principal():
    """
    Função responsável por inicializar e executar a aplicação.
    """
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    app = JanelaPrincipal(root)
    root.mainloop()


if __name__ == "__main__":
    """
    Ponto de entrada do programa.
    """
    iniciar_janela_principal()