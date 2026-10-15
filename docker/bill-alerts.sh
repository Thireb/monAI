#!/bin/sh
# Send the bill alerts (Web Push) once a day at BILL_ALERT_TIME (default 09:00),
# in the TIMEZONE of the server. docker-compose.yml runs this in the "alerts" service.
set -e

ALERT_TIME="${BILL_ALERT_TIME:-09:00}"
export TZ="${TIMEZONE:-UTC}"

while true; do
    now=$(date +%s)
    next=$(date -d "today $ALERT_TIME" +%s)
    if [ "$next" -le "$now" ]; then
        next=$(date -d "tomorrow $ALERT_TIME" +%s)
    fi
    echo "Next bill alerts at $(date -d "@$next")"
    sleep $((next - now))
    python manage.py send_bill_alerts || echo "send_bill_alerts failed; next try tomorrow"
done
