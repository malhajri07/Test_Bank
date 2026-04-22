"""
Tests for payments.currency — display-only multi-currency helpers.
"""

from decimal import Decimal

from django.test import SimpleTestCase, override_settings

from payments import currency


class ConvertFromBaseTests(SimpleTestCase):
    def test_sar_passthrough_uses_two_decimals(self):
        result = currency.convert_from_base(Decimal('10'), 'SAR')
        self.assertEqual(result, Decimal('10.00'))

    def test_usd_conversion_rounds_to_two_decimals(self):
        # 10 SAR * 0.2667 = 2.667 -> 2.67
        result = currency.convert_from_base(Decimal('10'), 'USD')
        self.assertEqual(result, Decimal('2.67'))

    def test_kwd_conversion_uses_three_decimals(self):
        # 10 SAR * 0.0818 = 0.818
        result = currency.convert_from_base(Decimal('10'), 'KWD')
        self.assertEqual(result, Decimal('0.818'))

    def test_unknown_currency_returns_none(self):
        self.assertIsNone(currency.convert_from_base(Decimal('10'), 'XYZ'))

    @override_settings(CURRENCY_FX_RATES={'SAR': 1, 'USD': '0.30'})
    def test_settings_override_wins(self):
        result = currency.convert_from_base(Decimal('10'), 'USD')
        self.assertEqual(result, Decimal('3.00'))


class FormatAmountTests(SimpleTestCase):
    def test_sar_format(self):
        self.assertEqual(currency.format_amount(Decimal('10'), 'SAR'), '10.00 SAR')

    def test_usd_format(self):
        self.assertEqual(currency.format_amount(Decimal('10'), 'USD'), '2.67 USD')

    def test_kwd_format_three_decimals(self):
        self.assertEqual(currency.format_amount(Decimal('10'), 'KWD'), '0.818 KWD')

    def test_unknown_currency_falls_back(self):
        self.assertEqual(currency.format_amount(Decimal('10'), 'XYZ'), '10 XYZ')

    def test_thousands_separator_applied(self):
        self.assertEqual(currency.format_amount(Decimal('1234'), 'SAR'), '1,234.00 SAR')


class DisplayOptionsTests(SimpleTestCase):
    def test_every_configured_currency_returned(self):
        opts = currency.display_options(Decimal('10'))
        codes = [o['code'] for o in opts]
        self.assertEqual(codes, [c['code'] for c in currency.CURRENCY_META])

    def test_options_include_formatted_amount(self):
        opts = {o['code']: o['formatted'] for o in currency.display_options(Decimal('10'))}
        self.assertEqual(opts['SAR'], '10.00 SAR')
        self.assertEqual(opts['USD'], '2.67 USD')
        self.assertEqual(opts['KWD'], '0.818 KWD')
