"""
Session-based shopping cart for test banks.

Stores a list of test bank IDs in the user's session. Quantity is always 1
per test bank (a user can't buy two copies of the same exam access).

Usage:
    cart = Cart(request)
    cart.add(test_bank_id=123)
    cart.remove(test_bank_id=123)
    cart.clear()
    for item in cart:  # yields TestBank instances
        ...
    total = cart.get_total()
    count = len(cart)
"""

from decimal import Decimal

from catalog.models import TestBank

SESSION_KEY = 'cart_test_bank_ids'


class Cart:
    """Session-backed cart. Items are unique TestBank IDs."""

    def __init__(self, request):
        self.session = request.session
        ids = self.session.get(SESSION_KEY)
        if ids is None:
            ids = []
            self.session[SESSION_KEY] = ids
        self._ids = ids

    def _save(self):
        self.session[SESSION_KEY] = self._ids
        self.session.modified = True

    def add(self, test_bank_id):
        """Add a test bank to the cart. No-op if already present."""
        tbid = int(test_bank_id)
        if tbid not in self._ids:
            self._ids.append(tbid)
            self._save()
            return True
        return False

    def remove(self, test_bank_id):
        """Remove a test bank from the cart. No-op if not present."""
        tbid = int(test_bank_id)
        if tbid in self._ids:
            self._ids.remove(tbid)
            self._save()
            return True
        return False

    def clear(self):
        self._ids = []
        self._save()

    def contains(self, test_bank_id):
        return int(test_bank_id) in self._ids

    def get_test_banks(self):
        """Return TestBank queryset for items currently in cart (active only)."""
        if not self._ids:
            return TestBank.objects.none()
        return TestBank.objects.filter(id__in=self._ids, is_active=True)

    def __iter__(self):
        yield from self.get_test_banks()

    def __len__(self):
        # Only count items still active & in DB
        return self.get_test_banks().count()

    @property
    def ids(self):
        return list(self._ids)

    def get_subtotal(self):
        """Sum of prices of all test banks in cart."""
        total = Decimal('0')
        for tb in self.get_test_banks():
            total += tb.price
        return total
