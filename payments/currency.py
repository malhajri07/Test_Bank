"""
Multi-currency display helpers.

Design:
- The base currency is SAR — that's what prices are stored in and what Paylink
  charges. All other currencies are *display-only*: we show users a converted
  amount so they can judge the price in a familiar currency, but the actual
  settlement happens in SAR. (Paylink is a Saudi gateway and only reliably
  invoices in SAR; sending other currencies risks a pricing mismatch.)

- Rates are static for now. To swap in a live FX source, replace `_load_rates`
  with an API fetch + cache. Keep the public API (convert, format_amount,
  display_options) stable.
"""

from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings


BASE_CURRENCY = 'SAR'

# 1 SAR = N target currency.
# Conservative mid-market rates; refresh periodically or replace with an API.
DEFAULT_FX_RATES = {
    'SAR': Decimal('1.0000'),
    'USD': Decimal('0.2667'),
    'AED': Decimal('0.9793'),
    'KWD': Decimal('0.0818'),
    'BHD': Decimal('0.1005'),
    'QAR': Decimal('0.9707'),
    'OMR': Decimal('0.1027'),
    'EGP': Decimal('13.1500'),
}

# ISO 4217 minor units — Gulf dinars use 3 decimal places.
_DECIMALS = {
    'KWD': 3,
    'BHD': 3,
    'OMR': 3,
}

CURRENCY_META = [
    {'code': 'SAR', 'flag': '🇸🇦', 'name': 'Saudi Riyal'},
    {'code': 'USD', 'flag': '🇺🇸', 'name': 'US Dollar'},
    {'code': 'AED', 'flag': '🇦🇪', 'name': 'UAE Dirham'},
    {'code': 'KWD', 'flag': '🇰🇼', 'name': 'Kuwaiti Dinar'},
    {'code': 'BHD', 'flag': '🇧🇭', 'name': 'Bahraini Dinar'},
    {'code': 'QAR', 'flag': '🇶🇦', 'name': 'Qatari Riyal'},
    {'code': 'OMR', 'flag': '🇴🇲', 'name': 'Omani Rial'},
    {'code': 'EGP', 'flag': '🇪🇬', 'name': 'Egyptian Pound'},
]


def _load_rates():
    """Return the active rate table. Settings override wins, else defaults."""
    override = getattr(settings, 'CURRENCY_FX_RATES', None)
    if not override:
        return DEFAULT_FX_RATES
    return {code: Decimal(str(rate)) for code, rate in override.items()}


def decimals_for(currency):
    return _DECIMALS.get(currency, 2)


def convert_from_base(amount, target):
    """Convert a base-currency (SAR) amount into the target, rounded to minor units."""
    rates = _load_rates()
    rate = rates.get(target)
    if rate is None:
        return None

    quant = Decimal('1').scaleb(-decimals_for(target))
    return (Decimal(amount) * rate).quantize(quant, rounding=ROUND_HALF_UP)


def format_amount(amount, currency):
    """Return a user-facing string like '10.00 SAR' or '2.67 USD'."""
    if currency == BASE_CURRENCY:
        value = Decimal(amount).quantize(
            Decimal('1').scaleb(-decimals_for(BASE_CURRENCY)),
            rounding=ROUND_HALF_UP,
        )
    else:
        value = convert_from_base(amount, currency)
        if value is None:
            return f'{amount} {currency}'

    return f'{value:,.{decimals_for(currency)}f} {currency}'


def display_options(base_amount):
    """
    Pre-render the full currency list for a price, ready for a template select.

    Each option carries the formatted amount so the template doesn't need to
    re-run conversion logic, and the JS switcher can read it from a data attr.
    """
    return [
        {
            'code': c['code'],
            'flag': c['flag'],
            'name': c['name'],
            'formatted': format_amount(base_amount, c['code']),
        }
        for c in CURRENCY_META
    ]
