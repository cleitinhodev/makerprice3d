# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
import copy

import pytest

PROJETO_V1 = {
    "material": {"resina": "150", "suporte": "10", "peso": "80", "custo_fixo": "2,5"},
    "energia": {"impressao": "0,45", "lixa_retificadora": "0,05", "lavagem_cura": "0,10", "pintura": ""},
    "desgaste": {
        "preco_lcd": "600",
        "vida_util": "2000",
        "tempo_total": "5",
        "preco_fep": "60",
        "durabilidade": "30",
        "porcentagem_area": "40",
        "manutencao_fixa_extra": "0,5",
    },
    "acabamento": {
        "lavagem": {"custo_solvente": "35", "lavagens_por_peca": "10", "litros_usados": "0,1"},
        "lixa": {"custo_de_ponta": "12", "vida_util_ponta": "6", "pontas_usadas": "2"},
        "pintura": {"custo_unidade_tinta": "15", "ml_por_unidade": "20", "uso_de_tinta_medio": "4"},
    },
    "despesas": {"tabela": [["Base", "Acessório", "2", "14.00"], ["Ímã", "Peça", "1", "3.50"]]},
    "logistica": {"embrulho": "3", "descontos": "1", "impostos": "0", "frete": "12"},
    "mao_de_obra": {"ganho_por_hora": "25", "horas_trabalhadas": "1,5"},
    "lucro": {"estado": 30},
}


@pytest.fixture
def projeto_v1() -> dict:
    return copy.deepcopy(PROJETO_V1)


@pytest.fixture
def banco(tmp_path):
    from makerprice3d.services.banco import Banco

    b = Banco(tmp_path / "teste.db")
    yield b
    b.fechar()
