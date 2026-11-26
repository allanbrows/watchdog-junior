from datetime import timedelta
from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase
from django.utils import timezone

from .models import Monitor, PingLog
from .pinger import ping_monitor
from .stats import compute_monitor_stats


def make_log(monitor, ok, minutes_ago):
    """Crée un PingLog avec une date précise (checked_at est auto, on la force ensuite)."""
    log = PingLog.objects.create(
        monitor=monitor,
        is_success=ok,
        status_code=200 if ok else None,
        response_time_ms=100 if ok else None,
    )
    PingLog.objects.filter(pk=log.pk).update(
        checked_at=timezone.now() - timedelta(minutes=minutes_ago)
    )
    return log


# ---------- Tests unitaires : statut ----------
class MonitorStatusTests(TestCase):
    def setUp(self):
        self.monitor = Monitor.objects.create(name="Test", url="https://exemple.fr")

    def test_status_pending_without_logs(self):
        self.assertEqual(self.monitor.current_status, "pending")

    def test_status_up_when_last_ping_succeeded(self):
        make_log(self.monitor, ok=False, minutes_ago=2)
        make_log(self.monitor, ok=True, minutes_ago=1)
        self.assertEqual(self.monitor.current_status, "up")

    def test_status_down_when_last_ping_failed(self):
        make_log(self.monitor, ok=True, minutes_ago=2)
        make_log(self.monitor, ok=False, minutes_ago=1)
        self.assertEqual(self.monitor.current_status, "down")


# ---------- Tests unitaires : ping (requests.get est simulé) ----------
class PingMonitorTests(TestCase):
    def setUp(self):
        self.monitor = Monitor.objects.create(name="Test", url="https://exemple.fr")

    @patch("monitors.pinger.requests.get")
    def test_ping_success(self, mock_get):
        mock_get.return_value = MagicMock(ok=True, status_code=200)
        log = ping_monitor(self.monitor)
        self.assertTrue(log.is_success)
        self.assertEqual(log.status_code, 200)
        self.assertIsNotNone(log.response_time_ms)

    @patch("monitors.pinger.requests.get")
    def test_ping_http_error_is_failure(self, mock_get):
        mock_get.return_value = MagicMock(ok=False, status_code=500)
        log = ping_monitor(self.monitor)
        self.assertFalse(log.is_success)
        self.assertEqual(log.status_code, 500)
        self.assertEqual(log.error_message, "HTTP 500")

    @patch("monitors.pinger.requests.get")
    def test_ping_network_error_is_failure(self, mock_get):
        mock_get.side_effect = requests.ConnectionError("site injoignable")
        log = ping_monitor(self.monitor)
        self.assertFalse(log.is_success)
        self.assertIsNone(log.status_code)
        self.assertIn("injoignable", log.error_message)

    @patch("monitors.pinger.requests.get")
    def test_ping_saves_one_log(self, mock_get):
        mock_get.return_value = MagicMock(ok=True, status_code=200)
        ping_monitor(self.monitor)
        self.assertEqual(PingLog.objects.filter(monitor=self.monitor).count(), 1)


# ---------- Tests unitaires : calculs statistiques ----------
class StatsTests(TestCase):
    def setUp(self):
        self.monitor = Monitor.objects.create(
            name="Test", url="https://exemple.fr", frequency_seconds=60
        )

    def test_no_logs(self):
        result = compute_monitor_stats(self.monitor)
        self.assertEqual(result["total_pings"], 0)
        self.assertIsNone(result["availability_percent"])

    def test_availability_percent(self):
        for i, ok in enumerate([True, True, True, False]):
            make_log(self.monitor, ok=ok, minutes_ago=10 - i)
        result = compute_monitor_stats(self.monitor)
        self.assertEqual(result["availability_percent"], 75.0)

    def test_consecutive_failures_count_as_one_outage(self):
        # OK, KO, KO, OK, KO : 2 interruptions (3 échecs au total)
        for i, ok in enumerate([True, False, False, True, False]):
            make_log(self.monitor, ok=ok, minutes_ago=10 - i)
        result = compute_monitor_stats(self.monitor)
        self.assertEqual(result["outage_count"], 2)
        self.assertEqual(result["downtime_seconds"], 3 * 60)


# ---------- Tests d'API ----------
class ApiTests(TestCase):
    def post_monitor(self, data):
        return self.client.post("/monitors", data, content_type="application/json")

    def test_create_monitor(self):
        response = self.post_monitor(
            {"name": "Portainer", "url": "https://portainer.exemple.fr", "frequency_seconds": 30}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "pending")
        self.assertEqual(Monitor.objects.count(), 1)

    def test_create_monitor_default_frequency(self):
        response = self.post_monitor({"name": "A", "url": "https://a.exemple.fr"})
        self.assertEqual(response.json()["frequency_seconds"], 60)

    def test_create_rejects_invalid_url(self):
        response = self.post_monitor({"name": "A", "url": "pasuneurl"})
        self.assertEqual(response.status_code, 400)

    def test_create_rejects_low_frequency(self):
        response = self.post_monitor(
            {"name": "A", "url": "https://a.exemple.fr", "frequency_seconds": 2}
        )
        self.assertEqual(response.status_code, 400)

    def test_create_rejects_missing_name(self):
        response = self.post_monitor({"url": "https://a.exemple.fr"})
        self.assertEqual(response.status_code, 400)

    def test_create_rejects_duplicate_url(self):
        self.post_monitor({"name": "A", "url": "https://a.exemple.fr"})
        response = self.post_monitor({"name": "B", "url": "https://a.exemple.fr"})
        self.assertEqual(response.status_code, 409)

    def test_create_rejects_invalid_json(self):
        response = self.client.post("/monitors", "pas du json", content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_list_monitors(self):
        Monitor.objects.create(name="A", url="https://a.exemple.fr")
        response = self.client.get("/monitors")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_logs_endpoint(self):
        monitor = Monitor.objects.create(name="A", url="https://a.exemple.fr")
        make_log(monitor, ok=True, minutes_ago=2)
        make_log(monitor, ok=False, minutes_ago=1)
        response = self.client.get(f"/logs/{monitor.id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertFalse(data[0]["is_success"])  # le plus récent d'abord

    def test_logs_unknown_monitor_returns_404(self):
        response = self.client.get("/logs/999")
        self.assertEqual(response.status_code, 404)

    def test_stats_endpoint(self):
        monitor = Monitor.objects.create(name="A", url="https://a.exemple.fr")
        make_log(monitor, ok=True, minutes_ago=2)
        make_log(monitor, ok=False, minutes_ago=1)
        response = self.client.get("/stats")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["global"]["availability_percent"], 50.0)
        self.assertEqual(response.json()["global"]["outage_count"], 1)