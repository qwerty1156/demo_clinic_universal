# Demo Clinic — appointment request assistant

A Python Telegram bot that collects appointment requests, stores them in SQLite and
lets an administrator confirm or reject them. Includes clinic information and a Gemini integration.

## User flow

Choose a service → enter a preferred date, name and phone → confirm the request →
administrator reviews it → the user receives a notification.

This is a demo request workflow: it does not check a live calendar or reserve an available time slot.

## Architecture

- `core/`: booking states, application handling and clinic information.
- `channels/telegram/`: Telegram handlers, keyboards and webhook adapter.
- `database/`: SQLite persistence.
- `config/clinic.py`: configurable clinic services and details.

Telegram is the implemented channel. WhatsApp and Instagram are extension ideas, not implemented integrations.

## Try the booking core offline

```bash
python -m pip install -r demo_clinic_universal/requirements.txt
python scripts/demo.py
```

Uses the project dependencies, synthetic settings/contact details and a disposable database.
Exercises request collection, persistence and administrator confirmation. It does not send
messages or call Gemini; live channel integration is a separate check.

## Run the Telegram bot

```bash
git clone https://github.com/qwerty1156/demo_clinic_universal.git
cd demo_clinic_universal/demo_clinic_universal
python -m venv .venv
# Activate the virtual environment for your OS.
python -m pip install -r requirements.txt
# Copy .env.example to .env and fill in your own settings.
python bot.py
```

The webhook requires a publicly reachable HTTPS endpoint and a Telegram bot token.
[Detailed setup and deployment](demo_clinic_universal/README.md).

## Status

Portfolio demo, built with AI-assisted development. Live Telegram delivery and Gemini calls
have not been revalidated as part of this portfolio update. SQLite persistence must be configured
for the deployment; this repository is not presented as a production medical system.
