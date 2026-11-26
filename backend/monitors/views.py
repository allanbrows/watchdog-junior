import json

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Monitor


from .stats import compute_monitor_stats

MIN_FREQUENCY = 10  


def monitor_to_dict(monitor):
    
    return {
        "id": monitor.id,
        "name": monitor.name,
        "url": monitor.url,
        "frequency_seconds": monitor.frequency_seconds,
        "is_active": monitor.is_active,
        "status": monitor.current_status,  
    }


@csrf_exempt  
def monitors_list(request):
    """GET /monitors : liste des sites. POST /monitors : création d'un site."""
    if request.method == "GET":
        data = [monitor_to_dict(m) for m in Monitor.objects.all()]
        return JsonResponse(data, safe=False)

    if request.method == "POST":
       
        try:
            payload = json.loads(request.body)
        except ValueError:  
            return JsonResponse({"error": "JSON invalide"}, status=400)

        if not isinstance(payload, dict):
            return JsonResponse({"error": "Le corps doit être un objet JSON"}, status=400)

        name = str(payload.get("name", "")).strip()
        url = str(payload.get("url", "")).strip()
        frequency = payload.get("frequency_seconds", 60)

        
        if not name or not url:
            return JsonResponse({"error": "Les champs 'name' et 'url' sont obligatoires"}, status=400)

        try:
            URLValidator(schemes=["http", "https"])(url)
        except ValidationError:
            return JsonResponse({"error": "URL invalide (http:// ou https:// requis)"}, status=400)

        if isinstance(frequency, bool) or not isinstance(frequency, int) or frequency < MIN_FREQUENCY:
            return JsonResponse(
                {"error": f"La fréquence doit être un entier >= {MIN_FREQUENCY} secondes"},
                status=400,
            )

        if Monitor.objects.filter(url=url).exists():
            return JsonResponse({"error": "Ce site est déjà surveillé"}, status=409)

        # 4. Création
        monitor = Monitor.objects.create(name=name, url=url, frequency_seconds=frequency)
        return JsonResponse(monitor_to_dict(monitor), status=201)

    return JsonResponse({"error": "Méthode non autorisée"}, status=405)





def log_to_dict(log):
    
    return {
        "id": log.id,
        "checked_at": log.checked_at.isoformat(),
        "is_success": log.is_success,
        "status_code": log.status_code,
        "response_time_ms": log.response_time_ms,
        "error_message": log.error_message,
    }


def monitor_logs(request, monitor_id):
    """GET /logs/<id> : historique des pings d'un site (100 derniers)."""
    try:
        monitor = Monitor.objects.get(id=monitor_id)
    except Monitor.DoesNotExist:
        return JsonResponse({"error": "Site introuvable"}, status=404)

    logs = monitor.logs.all()[:100]
    return JsonResponse([log_to_dict(log) for log in logs], safe=False)


def stats(request):
    
    per_monitor = [compute_monitor_stats(m) for m in Monitor.objects.all()]

    total = sum(s["total_pings"] for s in per_monitor)
    successes = sum(s["successful_pings"] for s in per_monitor)

    global_stats = {
        "total_pings": total,
        "successful_pings": successes,
        "availability_percent": round(successes / total * 100, 2) if total > 0 else None,
        "outage_count": sum(s["outage_count"] for s in per_monitor),
        "total_downtime_seconds": sum(s["downtime_seconds"] for s in per_monitor),
    }

    return JsonResponse({"global": global_stats, "monitors": per_monitor})