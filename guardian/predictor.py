def predict_system_issues(stats: dict):
    """Analyze system metrics to predict potential failures or performance drops."""
    alerts = []

    # CPU Threshold
    if stats.get("cpu", 0) > 85:
        alerts.append("⚠️ HIGH NEURAL LOAD: System latency imminent. Consider closing heavy applications.")

    # RAM Threshold
    if stats.get("ram", 0) > 90:
        alerts.append("⚠️ MEMORY DEPLETION: Neural processing restricted. RAM usage critical.")

    # Disk Space (Junk)
    junk_count = len(stats.get("junk", []))
    if junk_count > 5:
        alerts.append(f"🧹 CLUTTER DETECTED: {junk_count} large junk files identified. Cleanup recommended.")

    # Security
    if "threat" in str(stats.get("security", "")).lower():
        alerts.append("🚨 SECURITY BREACH: Potential threat detected during background scan.")

    return alerts
