import time

from django.core.management.base import BaseCommand
from django.utils import timezone

from monitors.models import Monitor
from monitors.pinger import ping_monitor

CHECK_INTERVAL = 5  


def is_due(monitor):
    
    last_log = monitor.logs.first()  
    if last_log is None:
        return True 
    elapsed = (timezone.now() - last_log.checked_at).total_seconds()
    return elapsed >= monitor.frequency_seconds


class Command(BaseCommand):
    help = "Pingue en continu les sites selon leur fréquence."

    def handle(self, *args, **options):
        count = Monitor.objects.filter(is_active=True).count()
        self.stdout.write(f"Pinger démarré : {count} site(s) actif(s) (Ctrl+C pour arrêter)")
        try:
            while True:
                for monitor in Monitor.objects.filter(is_active=True):
                    if is_due(monitor):
                        log = ping_monitor(monitor)
                        result = "OK" if log.is_success else "KO"
                        detail = log.status_code or log.error_message[:60]
                        self.stdout.write(f"[{timezone.localtime():%H:%M:%S}] {monitor.name} : {result} ({detail})")
                time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            self.stdout.write("Pinger arrêté.")