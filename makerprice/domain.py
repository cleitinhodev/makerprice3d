"""Pure pricing model. All quantities cover a whole batch unless noted otherwise."""
from dataclasses import dataclass, fields, asdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, ROUND_CEILING

D = Decimal
CENT = D('0.01')


def number(value):
    if isinstance(value, bool):
        raise ValueError('Valor numérico inválido.')
    text = str(value).strip()
    if ',' in text:
        text = text.replace('.', '').replace(',', '.')
    try:
        result = D(text or '0')
    except InvalidOperation:
        raise ValueError('Valor numérico inválido.') from None
    if not result.is_finite():
        raise ValueError('O valor precisa ser finito.')
    return result


def money(value):
    result = f'{number(value).quantize(CENT, rounding=ROUND_HALF_UP):,.2f}'
    return 'R$ ' + result.replace(',', '_').replace('.', ',').replace('_', '.')


@dataclass
class Quote:
    title: str = 'Novo orçamento'
    client: str = ''
    notes: str = ''
    process: str = 'Resina'
    units: int = 1
    material_price: str = '180'
    amount: str = '100'
    amount_unit: str = 'g'
    density: str = '1.1'
    supports: str = '0'
    waste: str = '5'
    hours: str = '4'
    watts: str = '100'
    tariff: str = '0.95'
    wear_hour: str = '1.5'
    finishing: str = '0'
    labor_hours: str = '0.5'
    labor_rate: str = '25'
    packaging_unit: str = '2'
    shipping: str = '0'
    extra: str = '0'
    contingency: str = '5'
    pricing: str = 'Margem sobre venda'
    target: str = '30'
    fee: str = '0'
    discount: str = '0'

    def validate(self):
        if not isinstance(self.units, int) or isinstance(self.units, bool) or not 1 <= self.units <= 100000:
            raise ValueError('Quantidade deve estar entre 1 e 100.000 peças.')
        if self.process not in ('Resina', 'FDM') or self.amount_unit not in ('g', 'ml'):
            raise ValueError('Processo ou unidade inválidos.')
        if self.pricing not in ('Margem sobre venda', 'Acréscimo sobre custo'):
            raise ValueError('Modo de preço inválido.')
        for name in ('title', 'client', 'notes'):
            if not isinstance(getattr(self, name), str) or len(getattr(self, name)) > 20000:
                raise ValueError('Texto de orçamento inválido.')
        for name in NUMERIC:
            value = number(getattr(self, name))
            limit = D('100') if name == 'density' else D('1000') if name in ('supports', 'waste', 'contingency', 'target') else D('1000000000')
            if value < 0 or value > limit:
                raise ValueError(f'Valor fora do intervalo permitido em {name}: 0 a {limit}.')
        if self.amount_unit == 'ml' and number(self.density) <= 0:
            raise ValueError('Densidade precisa ser maior que zero para converter ml.')
        if number(self.fee) >= 100:
            raise ValueError('Taxas precisam ser menores que 100%.')
        if self.pricing == 'Margem sobre venda' and number(self.target) + number(self.fee) >= 100:
            raise ValueError('Margem + taxas precisam ser menores que 100%.')
        return self

    def document(self):
        self.validate()
        return {'schema_version': 2, 'quote': asdict(self)}

    @classmethod
    def from_document(cls, data):
        if not isinstance(data, dict) or data.get('schema_version') != 2:
            raise ValueError('Use um arquivo Studio v2. Arquivos antigos continuam disponíveis na versão clássica.')
        raw = data.get('quote')
        allowed = {f.name for f in fields(cls)}
        if not isinstance(raw, dict) or set(raw) != allowed:
            raise ValueError('Arquivo incompleto ou com campos desconhecidos.')
        return cls(**raw).validate()


NUMERIC = [f.name for f in fields(Quote) if f.name not in
           ('title', 'client', 'notes', 'process', 'units', 'amount_unit', 'pricing')]


@dataclass(frozen=True)
class Result:
    categories: dict
    cost: Decimal
    gross: Decimal
    price: Decimal
    unit_price: Decimal
    fees: Decimal
    profit: Decimal
    margin: Decimal
    grams: Decimal


def calculate(q):
    q.validate()
    n = lambda field: number(getattr(q, field))
    grams = n('amount') * (n('density') if q.amount_unit == 'ml' else 1)
    grams *= (1 + n('supports') / 100) * (1 + n('waste') / 100)
    categories = {
        'Material': grams / 1000 * n('material_price'),
        'Energia': n('hours') * n('watts') / 1000 * n('tariff'),
        'Desgaste': n('hours') * n('wear_hour'),
        'Acabamento': n('finishing'),
        'Mão de obra': n('labor_hours') * n('labor_rate'),
        'Embalagem e frete': n('packaging_unit') * q.units + n('shipping'),
        'Outros custos': n('extra'),
    }
    categories['Reserva de imprevistos'] = sum(categories.values()) * n('contingency') / 100
    cost = sum(categories.values())
    fee = n('fee') / 100
    target = n('target') / 100
    gross = cost / (1 - fee - target) if q.pricing == 'Margem sobre venda' else cost * (1 + target) / (1 - fee)
    gross = gross.quantize(CENT, rounding=ROUND_CEILING)
    price = gross - n('discount')
    if price < 0:
        raise ValueError('O desconto não pode superar o preço sugerido.')
    fees = (price * fee).quantize(CENT, rounding=ROUND_HALF_UP)
    profit = price - fees - cost
    margin = profit / price * 100 if price else D(0)
    return Result(categories, cost, gross, price, price / q.units, fees, profit, margin, grams)
