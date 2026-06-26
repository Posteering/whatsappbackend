# 🤖 Devon — WhatsApp AI Secretary Bot

A production-ready, fully automated WhatsApp AI assistant for **Easy Eat**, a food delivery business. Devon handles customer conversations, processes orders, generates payment links, and escalates to human agents — all through WhatsApp.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Environment Variables](#environment-variables)
- [Local Setup](#local-setup)
- [Deployment](#deployment)
- [API Endpoints](#api-endpoints)
- [How It Works](#how-it-works)
- [Updating API Keys](#updating-api-keys)
- [Troubleshooting](#troubleshooting)

---

## Overview

Devon is a WhatsApp bot that integrates the **Meta WhatsApp Cloud API** with **Anthropic Claude** to deliver intelligent, context-aware responses to customers. It is designed to run 24/7, handling everything from greeting new users to generating payment invoices automatically.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🧠 **AI Responses** | Powered by Claude (`claude-sonnet-4-5`) for natural, context-aware replies |
| 👤 **Auto Onboarding** | Automatically detects new users and collects their name |
| 💬 **Conversation Memory** | Maintains the last 10 messages of context per user |
| 💳 **Payment Link Generation** | AI triggers automatic payment link creation when a customer is ready to pay |
| ⏰ **Payment Reminders** | Sends automatic WhatsApp follow-ups for pending payments older than 24 hours |
| 🙋 **Human Escalation** | Detects frustration or explicit requests and flags conversations for human agents |
| 🌍 **Multilingual** | Replies in the same language the user writes in |
| 🔒 **Webhook Security** | Validates all incoming Meta webhooks with HMAC-SHA256 signature verification |

---

## 🏗 Architecture

```
User (WhatsApp)
      │
      ▼
Meta WhatsApp Cloud API
      │  (Webhook POST)
      ▼
┌─────────────────────┐
│   FastAPI Web App   │  ← Verifies signature, parses payload
│   (port 8000)       │
└────────┬────────────┘
         │ Dispatches task
         ▼
┌─────────────────────┐
│    Redis Broker     │  ← Railway-hosted Redis
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐      ┌──────────────────────┐
│   Celery Worker     │ ───► │  Anthropic Claude API │
│  (background task)  │      └──────────────────────┘
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   PostgreSQL DB     │  ← Railway-hosted Postgres
│  (conversation log) │
└─────────────────────┘
         │
         ▼
Meta WhatsApp Cloud API
      │  (Send reply)
      ▼
User (WhatsApp)
```

The system also runs a **Celery Beat** scheduler that periodically checks for unpaid orders and sends reminder messages.

---

## 📁 Project Structure

```
whatsapp bot/
├── app/
│   ├── ai/
│   │   ├── chat.py              # Anthropic Claude integration
│   │   └── prompts.py           # System prompt for Devon
│   ├── api/
│   │   ├── webhooks.py          # WhatsApp webhook endpoints
│   │   └── admin.py             # Admin routes
│   ├── core/
│   │   ├── config.py            # Environment variable settings
│   │   └── celery_app.py        # Celery & Beat configuration
│   ├── database/
│   │   └── session.py           # SQLAlchemy DB session
│   ├── models/
│   │   ├── user.py              # User model
│   │   ├── conversation.py      # Conversation model
│   │   ├── message.py           # Message model
│   │   └── payment.py           # Payment model
│   ├── services/
│   │   ├── background_tasks.py  # Celery task definitions
│   │   ├── conversation_service.py # Core message processing logic
│   │   ├── onboarding_service.py   # New user detection & greeting
│   │   ├── payment_service.py      # Payment link generation
│   │   └── escalation_service.py   # Human escalation logic
│   ├── whatsapp/
│   │   ├── client.py            # Meta Graph API client
│   │   └── security.py          # Webhook signature verification
│   └── main.py                  # FastAPI application entry point
├── alembic/                     # Database migrations
├── Dockerfile                   # Container definition
├── docker-compose.yml           # Multi-container orchestration
├── requirements.txt             # Python dependencies
└── .env                         # Secret environment variables
```

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **API Framework** | FastAPI (Python 3.12) |
| **AI Model** | Anthropic Claude (`claude-sonnet-4-5`) |
| **Task Queue** | Celery 5.x |
| **Task Scheduler** | Celery Beat |
| **Message Broker** | Redis (Railway) |
| **Database** | PostgreSQL (Railway) + SQLAlchemy ORM |
| **WhatsApp API** | Meta WhatsApp Cloud API v19 |
| **Containerization** | Docker + Docker Compose |
| **Tunnel (Dev)** | ngrok |

---

## 🔑 Environment Variables

Create a `.env` file in the root directory with the following:

```env
# Database
DATABASE_URL=postgresql://user:password@host:port/dbname

# Redis (used as Celery broker and result backend)
REDIS_URL=redis://default:password@host:port

# WhatsApp Cloud API
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_custom_verify_token
WHATSAPP_API_TOKEN=your_meta_access_token
WHATSAPP_APP_SECRET=your_meta_app_secret

# AI
ANTHROPIC_API_KEY=sk-ant-api03-...

# Security
SECRET_KEY=your_random_secret_key
```

### Where to get each key:

| Variable | Source |
|---|---|
| `DATABASE_URL` | Railway → your PostgreSQL service → Connect tab |
| `REDIS_URL` | Railway → your Redis service → Connect tab |
| `WHATSAPP_PHONE_NUMBER_ID` | Meta Developer Dashboard → WhatsApp → API Setup |
| `WHATSAPP_WEBHOOK_VERIFY_TOKEN` | You define this (e.g. `DAVIDSMITH001`) |
| `WHATSAPP_API_TOKEN` | Meta Developer Dashboard → WhatsApp → API Setup → Temporary or Permanent Token |
| `WHATSAPP_APP_SECRET` | Meta Developer Dashboard → App Settings → Basic |
| `ANTHROPIC_API_KEY` | [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys) |

> **Note:** The temporary Meta access token expires every 24 hours. To get a permanent token, use the Meta Business Manager to generate a System User token.

---

## 🚀 Local Setup

### Prerequisites
- Docker Desktop (running)
- ngrok account (free tier is fine)
- Meta Developer account with a WhatsApp app
- Anthropic account with API credits

### Steps

**1. Clone the repo and create your `.env` file:**
```bash
cp .env.example .env
# Fill in all the values
```

**2. Start all containers:**
```bash
docker compose up --build -d
```

This starts 3 services:
- `web` — FastAPI server on port 8000
- `worker` — Celery background worker
- `beat` — Celery periodic task scheduler

**3. Expose your local server to the internet:**
```bash
ngrok http 8000
```
Copy the generated `https://` URL.

**4. Configure the Meta Webhook:**
- Go to Meta Developer Dashboard → WhatsApp → Configuration
- Set Callback URL to: `https://your-ngrok-url.ngrok-free.app/api/v1/webhooks/whatsapp`
- Set Verify Token to the value you put in `WHATSAPP_WEBHOOK_VERIFY_TOKEN`
- Click **Verify and Save**
- Subscribe to the `messages` webhook field

**5. Add your phone number as a test recipient:**
- Go to WhatsApp → API Setup
- Under "To", add and verify your personal phone number

**6. Test it:**
Send a WhatsApp message to your bot number. You should receive a reply from Devon!

---

## 🌐 API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/webhooks/whatsapp` | Meta webhook verification |
| `POST` | `/api/v1/webhooks/whatsapp` | Receive incoming WhatsApp messages |
| `GET` | `/api/v1/admin/...` | Admin management routes |

---

## ⚙️ How It Works

### Message Flow

1. A user sends a WhatsApp message to the bot's phone number.
2. Meta delivers it to the webhook URL as a `POST` request.
3. The **FastAPI web server** verifies the request signature using HMAC-SHA256 and the App Secret.
4. The message is dispatched as a **Celery background task** to Redis.
5. The **Celery worker** picks up the task and runs `process_incoming_message_task`.
6. The **ConversationService** checks if the user is new (onboarding) or existing.
7. The last 10 messages of conversation history are loaded and sent to **Claude** along with the system prompt.
8. Claude generates a reply. If it contains `<TRIGGER_PAYMENT: amount>`, a payment link is generated. If it contains `<ESCALATE_HUMAN>`, the conversation is flagged.
9. The clean reply text is sent back to the user via the **Meta Graph API**.

### AI Persona — Devon
Devon is defined in `app/ai/prompts.py`. It is configured to:
- Be warm, professional, and multilingual
- Reply in whatever language the user writes in
- Guide users through food orders and confirm totals in Nigerian Naira (₦)
- Output special action tokens for the backend to process

---

## 🔄 Updating API Keys

If a token expires (e.g. the Meta temporary token), you do **not** need to rebuild Docker. Just update `docker-compose.yml`:

```yaml
- WHATSAPP_API_TOKEN=your_new_token_here
```

Then restart:
```bash
docker compose up -d
```

> ⚠️ The Meta temporary token expires every **24 hours**. For production, generate a **Permanent System User Token** in Meta Business Manager.

---

## 🔧 Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Bot receives messages but doesn't reply | Anthropic API credits exhausted | Add credits at [console.anthropic.com/settings/billing](https://console.anthropic.com/settings/billing) |
| Messages not reaching the server | ngrok URL has changed | Update the Callback URL in Meta Dashboard |
| `403 Forbidden` on webhook | Wrong App Secret or verify token | Check `WHATSAPP_APP_SECRET` and `WHATSAPP_WEBHOOK_VERIFY_TOKEN` in `.env` |
| `Connection refused` errors | Celery can't reach Redis | Check `REDIS_URL` is correct in `docker-compose.yml` |
| `#131030` error from Meta | Your phone number not in allowed list | Add your number in Meta → API Setup → To field |
| Bot replies to your number but not others | App is in Development Mode | Switch app to Live Mode in Meta Dashboard (requires Business Verification) |

---

## 📦 Going to Production

To allow **anyone** to message the bot (not just verified test numbers):

1. **Verify your business** in Meta Business Manager
2. **Add a payment method** in WhatsApp Manager
3. **Switch your Meta app** from Development → Live mode
4. **Generate a Permanent System User Token** so you don't need to refresh every 24 hours
5. **Deploy to a cloud server** (e.g. Railway, Render, AWS) instead of running locally with ngrok
