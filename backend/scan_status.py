"""Describe saved scan evidence without equating a scheduled trigger with timeliness.

This summarizes reported collection checks, not independent source authenticity,
GitHub delivery latency or publishing success. It performs no I/O or trading.
"""

def summarize_scan(scan):
    pending = "Trial-week SEC metadata schedule configured; successful scheduled execution not yet verified"
    if scan is None:
        return {"activity": "No saved SEC poll", "schedule_note": pending}
    event = scan.get("github_event_name")
    context = scan.get("schedule_status")
    if context == "GITHUB_RUN" and event == "schedule":
        label = "Schedule-triggered SEC poll"
    elif context == "GITHUB_RUN" and event == "workflow_dispatch":
        label = "Manually dispatched SEC poll"
    elif context == "MANUAL_RUN" and event is None:
        label = "Manual SEC poll"
    elif context == "GITHUB_RUN":
        label = "Other GitHub-triggered SEC poll"
    else:
        label = "SEC poll with unverified trigger"
    total, success = scan.get("configured_issuers"), scan.get("successful_issuers")
    valid_counts = type(total) is int and total > 0 and type(success) is int and 0 <= success <= total
    complete = (valid_counts and success == total and scan.get("metadata_window_complete") is True
                and scan.get("errors") == [])
    coverage = f"{success}/{total} issuer checks reported" if valid_counts else "issuer-check counts unavailable or invalid"
    health = "complete metadata window reported" if complete else "metadata coverage incomplete or unverified"
    activity = f"{label}: {coverage}; {health}. Metadata discoveries are not trade signals."
    note = pending
    if label == "Schedule-triggered SEC poll":
        note = ("A schedule-triggered SEC poll reported complete issuer checks; trigger punctuality and future reliability are not verified"
                if complete else "A schedule-triggered SEC poll is recorded, but complete issuer coverage is not verified")
    return {"activity": activity, "schedule_note": note}
