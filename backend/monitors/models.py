from django.db import models


class Monitor(models.Model):

    name = models.CharField(max_length=100)
    url = models.URLField(unique=True)
    frequency_seconds = models.PositiveIntegerField(default=60)  
    is_active = models.BooleanField(default=True)  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.url})"

    @property
    def current_status(self):
        
        last_log = self.logs.first()  
        if last_log is None:
            return "pending"  
        return "up" if last_log.is_success else "down"


class PingLog(models.Model):
    

    monitor = models.ForeignKey(
        Monitor, on_delete=models.CASCADE, related_name="logs"
    )
    checked_at = models.DateTimeField(auto_now_add=True)
    is_success = models.BooleanField()
    status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-checked_at"] 

    def __str__(self):
        result = "OK" if self.is_success else "KO"
        return f"{self.monitor.name} - {result} - {self.checked_at:%d/%m/%Y %H:%M:%S}"