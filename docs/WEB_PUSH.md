# Bill alerts (Web Push)

monAI can send a phone or PC alert before a bill is due. The alert lists:

- the unpaid bills of this month that are due in 3 days or fewer, and
- the bill reminders whose alert window ("Remind me, days before") starts today.

Each browser gets at most 1 alert a day.

## Requirements

- monAI must be open over **HTTPS** (for example the `tailscale serve` address).
  Browsers do not allow Web Push over plain HTTP.
- On iPhone, add monAI to the home screen first (iOS 16.4 or later).

## Turn alerts on

1. Open **More** in the new UI (`/app/more/`).
2. Under **Bill alerts on this device**, tap **Turn on** and allow notifications.
3. Tap **Send a test**. An alert comes in a few seconds.

Do this on each device that must get alerts.

The server key (VAPID) is made on first use and kept in the `WebPushKey` table.
If you delete it, each device must turn alerts on again.

## Send the alerts every day

The command `manage.py send_bill_alerts` sends today's alerts. Run it once a day.
With a systemd user timer (replace `/path/to/monAI` with the repo folder):

`~/.config/systemd/user/monai-bill-alerts.service`

```ini
[Unit]
Description=monAI bill alerts

[Service]
Type=oneshot
WorkingDirectory=/path/to/monAI
ExecStart=/path/to/monAI/.venv/bin/python manage.py send_bill_alerts
```

`~/.config/systemd/user/monai-bill-alerts.timer`

```ini
[Unit]
Description=Send monAI bill alerts every morning

[Timer]
OnCalendar=*-*-* 09:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Then turn the timer on:

```sh
systemctl --user daemon-reload
systemctl --user enable --now monai-bill-alerts.timer
```

`Persistent=true` sends the alert when the PC starts, if it was off at 09:00.
To check the last run: `journalctl --user -u monai-bill-alerts.service`.

## Security

The server sends requests to the push service URL that a browser gives it.
`budgetapp/services/push.py` accepts only the known push services (Google FCM,
Mozilla, Apple, Microsoft) over HTTPS, so a user cannot make the server call
other addresses.
