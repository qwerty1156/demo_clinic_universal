# Demo Clinic — universal AI clinic assistant

This project is intentionally split into a platform-independent Core and channel adapters. Telegram is the first working channel; WhatsApp and Instagram can be added later without rewriting booking/application/clinic logic.

## Project structure

```text
demo_clinic_universal/
├── bot.py
├── settings.py
├── requirements.txt
├── .env.example
├── .gitignore
├── config/
│   ├── __init__.py
│   └── clinic.py
├── core/
│   ├── __init__.py
│   ├── ai.py
│   ├── applications.py
│   ├── booking.py
│   ├── clinic.py
│   └── models.py
├── database/
│   ├── __init__.py
│   └── database.py
├── channels/
│   ├── __init__.py
│   ├── base.py
│   └── telegram/
│       ├── __init__.py
│       ├── adapter.py
│       ├── handlers.py
│       ├── keyboards.py
│       └── webhook.py
└── utils/
    ├── __init__.py
    └── validators.py
```

## Environment

Copy `.env.example` to `.env` and set:

```env
ADMIN_ID=123456789
ADMIN_USERNAME=your_username
BOT_TOKEN=...
GEMINI_API_KEY=...
PORT=8080
WEBHOOK_URL=https://your-app.onrender.com
```

No OpenAI key is required. Gemini is called directly over HTTPS.

## Local run

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python bot.py
```

For local webhook testing, `WEBHOOK_URL` must be publicly reachable. For local development you can temporarily add a tunnel, but Render is the intended deployment target.

## Render

Create a **Web Service**.

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
python bot.py
```

Add the six environment variables from `.env.example` to Render.

The app listens on `0.0.0.0:$PORT` and automatically sets Telegram's webhook to:

```text
WEBHOOK_URL/webhook/BOT_TOKEN
```

## What to customize for a real clinic

Most customer-specific content is in `config/clinic.py`:

- clinic name
- description
- address
- schedule
- map URL
- services and prices

The application/admin workflow is in `core/applications.py` and can be extended with a CRM or calendar integration.

## WhatsApp / Instagram later

Create a new adapter implementing `ChannelAdapter` and translate incoming webhook events into `IncomingMessage`. Send the adapter's outgoing messages back through the channel API. Do not change `BookingService`, `ClinicService`, `ApplicationService`, `Database`, or `GeminiAI` just because the channel changes.

## Important deployment note about SQLite

SQLite is ideal for this demo because it keeps deployment simple. On a hosting service, local filesystem persistence can be limited depending on the plan/infrastructure. For a real multi-instance production system, move the database layer to Postgres without changing the Core services.

## Demo flow

`/start` → services → service → date → name → phone → confirmation → SQLite application → admin notification → admin confirm/reject → user notification.
