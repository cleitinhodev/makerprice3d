# Maker Price 3D

## Download e Tutorial (PT/EN):

[Maker Price 3D (Windows 10/11)](https://www.bugzinho.com/makerprice3d)

## Apresentação

Maker Price 3D é uma ferramenta gratuita desenvolvida para auxiliar pequenos e médios empreendedores do setor de impressão 3D, oferecendo diversos cálculos que facilitam a definição do preço final de seus produtos.

## Sobre o Maker Price 3D

O programa funciona como uma grande calculadora, desenvolvida especialmente para ajudar o usuário a reunir e organizar todos os custos envolvidos na produção de uma peça em impressão 3D em resina. A proposta é contabilizar não apenas as despesas óbvias, mas também aqueles custos “invisíveis” que muitas vezes são ignorados, mas impactam diretamente no lucro final.

O desenvolvimento do software foi baseado na experiência de diversos usuários, desde iniciantes até profissionais que já atuam e lucram nesse mercado. Isso permitiu reunir os principais pontos, necessidades e detalhes que realmente fazem diferença no dia a dia, possibilitando a definição de preços mais justos e equilibrados, tanto para quem vende quanto para quem compra.

O Maker Price 3D aplica fórmulas de cálculo combinadas com testes personalizados, com o objetivo de chegar a valores mais precisos e realistas. Ele considera todas as etapas do processo, desde o início da impressão até o acabamento e envio, sem deixar de lado fatores sutis como desgaste da impressora, ferramentas, EPIs, entre outros. Assim, o sistema orienta o vendedor sobre quanto cobrar para manter a sustentabilidade e o crescimento do negócio.

A tecnologia utilizada foi desenvolvida em Python, com o apoio de bibliotecas externas, mantendo o sistema leve e prático, exatamente como a proposta do projeto exige. Além disso, o software conta com funcionalidades importantes, como salvar e carregar dados, permitindo que o usuário construa e atualize seu próprio banco de informações conforme necessário.

O software foi criado com cuidado e dedicação, prezando pela segurança e pela utilidade. A ideia é que ele seja uma ferramenta confiável no dia a dia, ajudando cada usuário a tirar o melhor proveito do seu trabalho.

## Novidades da versão 2.0

A v2.0 é uma repaginada completa, **100% focada em resina**. Nenhum campo da v1.x foi removido e as
fórmulas originais continuam as mesmas (há testes que comparam cada cálculo com o código da v1.x).

**Visual e uso**

- Interface nova em PySide6 (Qt): tema escuro/claro (Ctrl+T), cards, janela redimensionável e responsiva.
- Validação em tempo real: campo inválido fica vermelho e mostra o motivo.
- Atalhos: Ctrl+N (novo), Ctrl+O (abrir), Ctrl+S (salvar), Ctrl+Shift+S (salvar como), Ctrl+1…9 (páginas).
- Gráfico de composição animado, calculadora de kWh e cotação em outras moedas mantidos.

**Projetos**

- Novo formato `.mp3d` (JSON com `schema_version`); projetos `.json` da v1.x abrem e são convertidos.
- Salvamento atômico com cópia `.bak`, aviso de alterações não salvas, projetos recentes,
  salvamento automático e recuperação após fechamento inesperado.

**Cálculos novos (todos opcionais — vazios valem zero)**

- Mesa compartilhada: rateio por peso ou por quantidade de peças e tempo total pela altura da peça mais alta.
- Perdas de resina (tanque, lavagem, suportes extras) e taxa de falha (manual ou medida pelo histórico).
- Custos fixos rateados por hora de máquina e depreciação da impressora/mesa.
- Licença comercial de STL, EPI/consumíveis (luvas, máscara, filtro, papel) e climatização do ambiente.
- Tributos: DAS do MEI rateado pelas vendas do mês ou percentual (ex.: Simples) — **nenhuma alíquota
  oficial vem fixa no programa**, você informa a sua.
- Taxas do canal de venda (percentual + fixa). Os canais iniciais são **exemplos editáveis** — confira
  sempre a tarifa atual.
- Margem × markup, preços mínimo/sugerido/premium, preço reverso (quanto sobra de um preço já definido).
- Sem o antigo limite de R$ 9.999,99.

**Gestão do negócio**

- Perfis de impressoras, biblioteca de resinas e canais de venda (SQLite na pasta de dados do usuário).
- Clientes, orçamentos com validade/prazo/pagamento, PDF, link do WhatsApp (wa.me) e conversão em pedido.
- Catálogo de produtos com foto, escala e preço; kits/combos com desconto.
- Fila de produção (aguardando → imprimindo → lavando → curando → acabamento → pronto → entregue).
- Estoque com baixa automática quando o pedido entra em "imprimindo" e alerta de estoque baixo.
- Equipamentos: contador de LCD (horas) e FEP (impressões), histórico de manutenção, alerta de troca e
  registro de falhas que alimenta a taxa de falha medida.
- Painel mensal (faturamento, lucro, ticket médio, peças mais vendidas, resina usada), ponto de equilíbrio,
  retorno do investimento (payback) e simulação de cenários (ex.: resina +20%).
- Exportação em CSV e PDF, backup automático diário e exportação completa (.zip).

## Funcionalidades

- Cálculo completo de custos de impressão 3D
- Inclusão de custos ocultos (desgaste, energia, acabamento, etc.)
- Sistema de salvamento e carregamento de dados
- Interface prática e intuitiva
- Suporte para precificação mais precisa
- Precificação de várias peças com quantidade, orçamentos e pedidos (v2.0)

## Como executar a partir do código

Requer Python 3.10 ou superior.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python main.py          # ou: python -m makerprice3d
```

Para abrir um projeto direto: `python main.py caminho/do/projeto.mp3d`.

### Testes e qualidade

```bash
pip install -r requirements-dev.txt
pip install -e .
ruff check .
pytest --cov=makerprice3d.core --cov-fail-under=80
```

Em servidores sem tela, use `QT_QPA_PLATFORM=offscreen`. O GitHub Actions roda ruff e pytest em cada push.

### Estrutura

- `makerprice3d/core` — cálculos puros (sem interface), dinheiro em `Decimal`.
- `makerprice3d/services` — arquivos, banco SQLite, backup, cotação e exportação.
- `makerprice3d/ui` — interface PySide6.
- `tests` — testes automatizados, incluindo a paridade com as fórmulas da v1.x (`tests/legado_v1.py`).

### Onde ficam os dados

- Windows: `%APPDATA%\MakerPrice3D` · macOS: `~/Library/Application Support/MakerPrice3D` ·
  Linux: `~/.local/share/MakerPrice3D`.
- Lá ficam o banco (`makerprice3d.db`), os backups, as fotos do catálogo e os salvamentos automáticos.
  A variável `MP3D_DATA_DIR` muda esse local.

### Diferenças de comportamento em relação à v1.x

- Campos que a v1.x lia como número inteiro (vida útil, tempo total, durabilidade e os do acabamento)
  agora aceitam decimais: "2,5" h deixava de ser 0 (ou 1) e passa a valer 2,5.
- "Área (%)" aceita vírgula ("12,5"); antes isso virava 100%.
- O limite de R$ 9.999,99 foi removido.
- Projetos novos começam com o lucro padrão das Configurações (30%, editável); na v1.x começavam em 0%.

## Requisitos

É um programa leve, que provavelmente funcionará em qualquer computador com Windows 10 ou superior.

> **Nota:** Alguns antivírus ou o próprio Windows Defender podem, em casos raros, identificar o software como potencialmente indesejado. Isso pode ocorrer com aplicações distribuídas fora de grandes plataformas ou sem assinatura digital.

É importante ressaltar que o Maker Price 3D foi desenvolvido com foco na segurança do usuário. O código não contém qualquer funcionalidade prejudicial. No entanto, o usuário é inteiramente responsável caso opte por realizar o download por fontes não oficiais ou diferentes das indicadas aqui, ou faça uso indevido da ferramenta.

## Considerações Finais

Fico feliz em compartilhar este software com a comunidade. A impressão 3D é uma área que me fascina muito, e tenho interesse a longo prazo de aprender mais e quem sabe desenvolver novas ferramentas que ajudem a comunidade de forma geral. Caso queira me ajudar com alguma contribuição para incentivar a continuidade do desenvolvimento, aqui está o link: [Área de Doações](https://www.bugzinho.com/donate).

Agradeço pela atenção e espero que faça bom uso do meu software! :)

Por: CleitinhoDEV

## Créditos e Agradecimentos

O Maker Price 3D faz uso de diversas bibliotecas de código aberto, e gostaríamos de expressar nossa gratidão pelos desenvolvedores dessas ferramentas poderosas. Abaixo, estão as bibliotecas utilizadas no projeto, seus respectivos créditos e os links para as licenças correspondentes:

### PySide6 (Qt for Python) — v2.0

Descrição: Biblioteca da interface gráfica da versão 2.0 (janelas, temas, gráficos e geração de PDF).

Licença: GNU LGPL v3

Link para a Licença: https://www.gnu.org/licenses/lgpl-3.0.html

Créditos: https://www.qt.io/qt-for-python

### sqlite3 — v2.0

Descrição: Módulo padrão do Python usado para guardar perfis, resinas, clientes, pedidos, estoque e configurações.

Licença: Python Software Foundation License (SQLite é de domínio público)

Créditos: https://docs.python.org/3/library/sqlite3.html

### requests

Descrição: Biblioteca utilizada para realizar requisições HTTP, permitindo a comunicação com serviços externos e APIs (cotação de moedas).

Licença: Apache 2.0

Link para a Licença: https://www.apache.org/licenses/LICENSE-2.0

Créditos: https://github.com/psf/requests

### Bibliotecas usadas na v1.x

As bibliotecas abaixo foram usadas na interface da versão 1.x e continuam creditadas aqui.

#### CustomTkinter (v1.x)

Descrição: Biblioteca utilizada para criar interfaces gráficas modernas e personalizadas, contribuindo diretamente para a aparência e experiência visual do software.

Licença: MIT License

Link para a Licença: https://opensource.org/licenses/MIT

Créditos: https://github.com/TomSchimansky/CustomTkinter

#### webbrowser (v1.x)

Descrição: Módulo padrão do Python que permite abrir links diretamente no navegador do usuário, facilitando o acesso a conteúdos externos.

Licença: Python Software Foundation License

Créditos: https://docs.python.org/3/library/webbrowser.html

#### os (v1.x)

Descrição: Biblioteca padrão do Python utilizada para interagir com o sistema operacional, como manipulação de arquivos e diretórios.

Licença: Python Software Foundation License

Créditos: https://docs.python.org/3/library/os.html

#### Pillow (PIL) (v1.x)

Descrição: Biblioteca utilizada para manipulação e processamento de imagens dentro do software.

Licença: PIL Software License

Link para a Licença: https://opensource.org/licenses/PIL

Créditos: https://github.com/python-pillow/Pillow

#### json (v1.x)

Descrição: Biblioteca padrão do Python utilizada para leitura e escrita de dados no formato JSON, permitindo o armazenamento e carregamento de informações.

Licença: Python Software Foundation License

Créditos: https://docs.python.org/3/library/json.html

#### tkinter (v1.x)

Descrição: Biblioteca padrão do Python para criação de interfaces gráficas, utilizada como base para alguns componentes do sistema.

Licença: Python Software Foundation License

Créditos: https://docs.python.org/3/library/tkinter.html

#### matplotlib (v1.x)

Descrição: Biblioteca utilizada para criação de gráficos e visualização de dados, auxiliando na análise de informações dentro do software.

Licença: Matplotlib License (baseada na PSF)

Link para a Licença: https://matplotlib.org/stable/users/project/license.html

Créditos: https://matplotlib.org/

## Licença

Maker Price 3D é software livre sob a GNU GPL v3 ou posterior (veja `LICENSE.txt`).
