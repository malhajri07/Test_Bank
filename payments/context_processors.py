"""Template context processors for the payments app."""

from .cart import Cart


def cart(request):
    """Inject `cart_count` into every template context.

    Uses the session-backed Cart helper. Zero or missing session → 0.
    Returns an int-valued count only (full Cart instance is not shipped
    into every render to keep the cost negligible).
    """
    try:
        c = Cart(request)
        return {'cart_count': len(c)}
    except Exception:
        return {'cart_count': 0}
