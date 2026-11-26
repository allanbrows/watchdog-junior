import time

import requests

from .models import PingLog

TIMEOUT_SECONDS = 10  # au-delà, on considère que le site ne répond pas


def ping_monitor(monitor):
    """Pingue un site et enregistre le résultat dans un PingLog."""
    start = time.monotonic()
    try:
        response = requests.get(monitor.url, timeout=TIMEOUT_SECONDS)
        elapsed_ms = int((time.monotonic() - start) * 1000)

        # Succès si le code HTTP est < 400 (response.ok)
        is_success = response.ok

        return PingLog.objects.create(
            monitor=monitor,
            is_success=is_success,
            status_code=response.status_code,
            response_time_ms=elapsed_ms,
            error_message="" if is_success else f"HTTP {response.status_code}",
        )
    except requests.RequestException as exc:
        # Site injoignable, timeout, DNS, certificat invalide...
        return PingLog.objects.create(
            monitor=monitor,
            is_success=False,
            status_code=None,
            response_time_ms=None,
            error_message=str(exc)[:500],
        )