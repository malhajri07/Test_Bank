"""
E2E test configuration.

Uses pytest-django live_server and pytest-playwright for browser automation.
Run with: pytest e2e/ -v
"""

import pytest


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for E2E tests."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
    }
