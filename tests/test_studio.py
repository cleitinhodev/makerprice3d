import json
from pathlib import Path
import tempfile
import unittest
from decimal import Decimal as D
from makerprice.domain import Quote, calculate, number, money
from makerprice.storage import Library, read_document, write_document


def baseline(**overrides):
    data = dict(material_price='1000', amount='100', waste='0', supports='0', hours='0',
                finishing='0', labor_hours='0', packaging_unit='0', shipping='0', extra='0',
                contingency='0', target='0', discount='0', fee='0')
    data.update(overrides)
    return Quote(**data)


class PricingTests(unittest.TestCase):
    def test_margin(self):
        r = calculate(baseline(target='30'))
        self.assertEqual(r.price, D('142.86'))
        self.assertGreaterEqual(r.margin, D(30))

    def test_markup(self):
        r = calculate(baseline(target='30', pricing='Acréscimo sobre custo'))
        self.assertEqual(r.price, D('130.00'))

    def test_fees(self):
        r = calculate(baseline(target='30', fee='10'))
        self.assertEqual(r.price, D('166.67'))
        self.assertEqual(r.fees, D('16.67'))
        self.assertEqual(r.profit, D('50'))

    def test_discount_is_applied_after_pricing(self):
        r = calculate(baseline(target='30', pricing='Acréscimo sobre custo', discount='10'))
        self.assertEqual(r.price, D('120'))
        self.assertEqual(r.profit, D('20'))

    def test_batch_cost_is_not_multiplied_again(self):
        r = calculate(baseline(units=10, packaging_unit='2'))
        self.assertEqual(r.cost, D('120'))
        self.assertEqual(r.unit_price, D('12'))

    def test_volume_supports_and_loss(self):
        r = calculate(baseline(amount_unit='ml', density='1.3', supports='10', waste='5'))
        self.assertEqual(r.grams, D('150.15'))

    def test_energy(self):
        r = calculate(baseline(hours='5', watts='200', tariff='1.20', wear_hour='0'))
        self.assertEqual(r.categories['Energia'], D('1.2'))

    def test_no_silent_price_limit(self):
        self.assertEqual(calculate(baseline(amount='20000')).cost, D('20000'))

    def test_zero(self):
        r = calculate(baseline(amount='0'))
        self.assertEqual(r.price, 0)
        self.assertEqual(r.margin, 0)

    def test_invalid_percentages(self):
        for kwargs in ({'target': '90', 'fee': '10'}, {'fee': '100'}, {'discount': '101'}, {'amount_unit': 'ml', 'density': '0'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                calculate(baseline(**kwargs))

    def test_invalid_quantities(self):
        for value in ('NaN', 'Infinity', '-1', 'abc'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                calculate(baseline(amount=value))
        for value in (0, -1, 1.5, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                calculate(baseline(units=value))

    def test_brazilian_number(self):
        self.assertEqual(number('1.234,56'), D('1234.56'))
        self.assertEqual(money('1234.56'), 'R$ 1.234,56')


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.library = Library(self.root / 'library.sqlite3')

    def tearDown(self):
        self.library.close()
        self.tmp.cleanup()

    def test_document_roundtrip(self):
        q = baseline(title='São Paulo — peça 01')
        path = self.root / 'test.json'
        write_document(path, q)
        self.assertEqual(read_document(path), q)

    def test_failed_write_does_not_replace_original(self):
        path = self.root / 'test.json'
        write_document(path, baseline())
        original = path.read_bytes()
        with self.assertRaises(ValueError):
            write_document(path, baseline(units=0))
        self.assertEqual(original, path.read_bytes())

    def test_update_and_duplicate(self):
        q = baseline(title='Primeiro')
        identity = self.library.save(q)
        q.title = 'Atualizado'
        self.library.save(q, identity)
        self.assertEqual(len(self.library.list()), 1)
        self.assertEqual(self.library.get(identity).title, 'Atualizado')
        self.library.save(q)
        self.assertEqual(len(self.library.list()), 2)
        self.assertEqual(len(self.library.list('inexistente')), 0)

    def test_profile(self):
        self.library.save_profile('material', 'PLA', {'material_price': '90'})
        self.library.save_profile('material', 'PLA', {'material_price': '95'})
        self.assertEqual(self.library.profiles('material'), [('PLA', {'material_price': '95'})])

    def test_invalid_document(self):
        for data in ({}, [], {'schema_version': 3}, {'schema_version': 2, 'quote': {}}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                Quote.from_document(data)
