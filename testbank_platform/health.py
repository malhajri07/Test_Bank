"""
Health check endpoints for Kubernetes/Cloud Run and load balancers.

- /healthz: Liveness probe — app is running
- /readyz: Readiness probe — app can serve traffic (DB connected)
"""

from django.db import connection
from django.http import JsonResponse


def healthz(request):
    """Liveness: returns 200 if the process is alive."""
    return JsonResponse({'status': 'ok'})


def readyz(request):
    """Readiness: returns 200 if DB is reachable, 503 otherwise."""
    try:
        connection.ensure_connection()
        return JsonResponse({'status': 'ok', 'database': 'connected'})
    except Exception:
        return JsonResponse(
            {'status': 'error', 'database': 'disconnected'},
            status=503,
        )
