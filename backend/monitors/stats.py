def compute_monitor_stats(monitor):
    
    logs = list(monitor.logs.order_by("checked_at"))  # du plus ancien au plus récent
    total = len(logs)

    
    if total == 0:
        return {
            "id": monitor.id,
            "name": monitor.name,
            "total_pings": 0,
            "successful_pings": 0,
            "availability_percent": None,
            "outage_count": 0,
            "downtime_seconds": 0,
        }

    successes = sum(1 for log in logs if log.is_success)
    failures = total - successes

    
    outage_count = 0
    previous_ok = True
    for log in logs:
        if not log.is_success and previous_ok:
            outage_count += 1
        previous_ok = log.is_success

    return {
        "id": monitor.id,
        "name": monitor.name,
        "total_pings": total,
        "successful_pings": successes,
        "availability_percent": round(successes / total * 100, 2),
        "outage_count": outage_count,
        "downtime_seconds": failures * monitor.frequency_seconds,  
    }