# Maker Price 3D Studio — versão experimental 2.0

Uma nova interface desktop em **PySide6 / Qt Widgets**, mantendo a versão clássica intacta em `main.py`.

## Windows

Baixe o artefato `MakerPrice3D-Studio-Windows-x64` na execução bem-sucedida de **Actions → Studio Windows preview**. Extraia **todo o ZIP** para uma pasta e abra `MakerPrice3D-Studio.exe`. Não mova apenas o EXE: a pasta `_internal` contém as bibliotecas necessárias. Não precisa instalar Python.

Esta é uma versão experimental, sem assinatura digital. A compilação é feita no Windows e executa testes antes de publicar o pacote. A edição clássica permanece disponível separadamente.

## Novidades

- Painel clássico em três colunas com Material/Energia/Desgaste, Acabamento/Despesas e Logística/Mão de obra/Total. Cores próprias nos blocos, subtotais e gráfico; biblioteca e exportações em janelas auxiliares.
- Resina e FDM com perfis locais de materiais e impressoras.
- Consumo em g ou ml com densidade; suportes adicionais e perdas configuráveis.
- Custo de todo o lote, embalagem por peça e rateio por unidade.
- Energia, desgaste/hora, trabalho ativo, acabamento e reserva de imprevistos.
- Margem sobre venda ou acréscimo sobre custo, taxas e desconto após o preço sugerido.
- Comparação de três metas; alerta para preço abaixo dos custos.
- Biblioteca SQLite com busca, atualização e duplicação de projetos.
- Proposta PDF para cliente, custos em CSV e orçamento em JSON.
- Gráfico leve desenhado com Qt, sem Matplotlib e sem consultas de internet.

## Regras de cálculo

Todos os consumos e tempos são do lote inteiro. Quantidade de peças divide o preço final e multiplica **somente a embalagem por peça**. Aumentar a quantidade não estima automaticamente novo consumo ou tempo: ajuste os dados do fatiador.

Material = consumo em g × (1 + suportes/100) × (1 + perda/100) × preço/kg / 1000.
Consumo em ml é convertido para g pela densidade. Se os suportes já estão no consumo, deixe o adicional em zero.
Energia = horas × watts / 1000 × tarifa/kWh. Desgaste = horas × custo de desgaste/hora.
Reserva de imprevistos = soma dos custos × percentual configurado; não é um modelo probabilístico de falhas.

Margem: preço = custo / (1 − margem − taxas).
Acréscimo: preço = custo × (1 + acréscimo) / (1 − taxas).
Preço sugerido arredondado para cima ao centavo; desconto é subtraído depois; taxas são calculadas sobre a venda descontada. O resultado exibido deduz custos e taxas. A margem efetiva pode ficar abaixo da meta após desconto. O valor por peça é uma média arredondada: prevalece o total do pedido.

Valores iniciais são exemplos e precisam ser ajustados ao seu equipamento e operação. Custos são estimativas configuradas pelo usuário, não aconselhamento fiscal.

## Dados e compatibilidade

`Salvar` (Ctrl+S) salva na biblioteca local, não em um arquivo JSON. Use Exportar JSON para compartilhar ou manter cópia externa. Qt armazena o banco `studio.sqlite3` no diretório de dados do aplicativo (`QStandardPaths.AppDataLocation`), normalmente sob AppData no Windows. Faça backup desse arquivo com o aplicativo fechado.

Arquivos JSON da edição clássica **não são importados automaticamente nesta preview**: continue abrindo-os na versão clássica. O Studio usa esquema versionado v2 e rejeita arquivos incompatíveis antes de substituir a tela. A edição nova consolida os detalhes de acabamento em um custo por lote e o desgaste em um custo/hora; não inclui a antiga consulta de moedas.

## Executar pelo código

```bash
python -m venv .venv
# Ative o ambiente virtual
python -m pip install -r requirements-qt.txt
python main_qt.py
python -m unittest discover -s tests -v
```

Para compilar no Windows:

```bash
python -m pip install -r requirements-build.txt
python -m PyInstaller --noconfirm --clean --windowed --onedir --name MakerPrice3D-Studio --icon assets/favicon.ico --add-data "LICENSE.txt;." main_qt.py
```

Não use o PyInstaller no Linux para produzir um EXE Windows. A automação incluída usa `windows-latest`.

Arquitetura: `makerprice/domain.py` (cálculo Decimal), `storage.py` (SQLite/JSON atômico), `ui.py` (Qt). GPL v3 ou posterior, conforme a licença do projeto. PySide6/Qt mantêm suas respectivas licenças e avisos distribuídos com as dependências.
