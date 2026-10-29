# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
from decimal import Decimal

import pytest

from makerprice3d.core import projeto as pj


def test_migrar_v1(projeto_v1):
    projeto_v1["despesas"]["tabela"].append(["Tinta", "Material", "", "R$ 7,25"])
    proj, migrado = pj.migrar(projeto_v1)
    assert migrado
    assert proj["schema_version"] == pj.SCHEMA_VERSION
    assert proj["material"]["resina"] == "150"
    assert proj["acabamento"]["lixa"]["pontas_usadas"] == "2"
    tabela = proj["despesas"]["tabela"]
    assert tabela[0] == {"nome": "Base", "tipo": "Acessório", "quantidade": "2", "valor": "14.00"}
    assert tabela[2]["valor"] == "7.25"
    assert tabela[2]["quantidade"] == "1"
    assert proj["lucro"] == {"estado": 30, "modo": "markup"}
    # seções novas vêm vazias
    assert proj["perdas"]["taxa_falha"] == ""


def test_migrar_atual_completa_campos():
    dados = {"schema_version": pj.SCHEMA_VERSION, "material": {"peso": 5}, "lucro": {"estado": "12", "modo": "margem"}}
    proj, migrado = pj.migrar(dados)
    assert not migrado
    assert proj["material"]["peso"] == "5"
    assert proj["desgaste"]["preco_lcd"] == ""
    assert proj["lucro"]["modo"] == "margem"


@pytest.mark.parametrize("dados", [[], "x", {"outra": 1}, {"schema_version": "2"}])
def test_migrar_invalido(dados):
    with pytest.raises(pj.ProjetoInvalidoError):
        pj.migrar(dados)


def test_versao_futura():
    with pytest.raises(pj.VersaoNaoSuportadaError):
        pj.migrar({"schema_version": pj.SCHEMA_VERSION + 1})


def test_valores_e_padroes():
    proj = pj.projeto_vazio({"mao_de_obra.ganho_por_hora": "25", "lucro.estado": 30})
    assert pj.obter_valor(proj, "mao_de_obra.ganho_por_hora") == "25"
    assert pj.obter_valor(proj, "nao.existe", "x") == "x"
    pj.definir_valor(proj, "meta.nome", "Peça")
    assert proj["meta"]["nome"] == "Peça"
    assert proj["venda"]["acrescimo_premium"] == "25"


def test_despesa():
    item = pj.item_despesa("Base", "Acessório", 3, "2,50")
    assert item == {"nome": "Base", "tipo": "Acessório", "quantidade": "3", "valor": "7.50"}
    assert pj.valor_unitario_despesa(item) == Decimal("2.5")
    assert pj.item_despesa("x", "y", 0, "-1")["quantidade"] == "1"


def test_preparar_para_salvar():
    proj = pj.projeto_vazio()
    proj["schema_version"] = 0
    copia = pj.preparar_para_salvar(proj)
    assert copia["schema_version"] == pj.SCHEMA_VERSION
    assert proj["schema_version"] == 0
