
from django.urls import path
from . import views

urlpatterns = [
    path("monitors", views.monitors_list),
    path("logs/<int:monitor_id>", views.monitor_logs),
    path("stats", views.stats),
]