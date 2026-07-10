# 🤖 VIOLET — WhatsApp AI Assistant

A production-ready, fully automated WhatsApp AI assistant that orchestrates a full vendor marketplace ecosystem. VIOLET handles customer conversations, processes orders, manages a multi-vendor marketplace, assigns dispatch riders, and handles complex payment flows via Posteering (Ledger & Escrow) — all through WhatsApp.

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
- [Troubleshooting](#troubleshooting)

---

## Overview

VIOLET is a WhatsApp bot that integrates the **Meta WhatsApp Cloud API** with **Anthropic Claude** to deliver intelligent, context-aware responses to customers. It features role-based routing to support Customers, Vendors, and Dispatch Riders. VIOLET utilizes **Posteering** to automatically generate FBO virtual accounts, handle payments securely in escrow, and disburse funds seamlessly to vendor ledgers.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🧠 **AI Responses** | Powered by Claude (`claude-sonnet-4-5`) for natural, context-aware replies |
| 👥 **Multi-role Support** | Seamlessly switches between Customer, Vendor, and Rider modes |
| 🏬 **Vendor Marketplace** | Customers can browse vendors, and vendors can manage their menus |
| 🛵 **Dispatch Riders** | Auto-assignment or manual pairing of delivery riders |
| 💳 **Posteering Integration** | Generates payment links via Posteering One API and monitors FBO callbacks |
| 🏦 **Ledger Escrow System** | Funds are held securely until order completion, then disbursed to vendor accounts |
| 🙋 **Human Escalation** | Detects frustration or explicit requests and flags conversations for human agents |
| 🔒 **Webhook Security** | Validates incoming Meta and Posteering webhooks via HMAC-SHA256 |

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
- Python 3.12+
- Node.js 18+
- A running PostgreSQL database (e.g. Railway)
- A running Redis instance (e.g. Railway)
- Meta Developer account with a WhatsApp app
- Anthropic account with API credits
- Posteering sandbox account (https://app.posteering.com)

### Steps

**1. Clone the repo:**
```bash
git clone https://github.com/your-fork/violet-bot.git
cd violet-bot
```

**2. Create your backend `.env`:**
```bash
cp .env.example .env
# Open .env and fill in ALL the values — see the comments inside
```

**3. Install Python dependencies & run migrations:**
```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
python -m alembic upgrade head
```

**4. Seed the database with a test vendor:**
```bash
python seed.py
# This prints a Vendor ID + phone number — save them for step 9
```

**5. Start the backend server:**
```bash
uvicorn app.main:app --reload --port 8000
```

**6. Set up the frontend:**
```bash
cd frontend
cp .env.example .env
# VITE_API_BASE=http://localhost:8000/api/v1  (default is fine for local dev)
npm install
npm run dev
```

**7. Expose your local server to the internet (for WhatsApp webhooks):**
```bash
ngrok http 8000
```
Copy the generated `https://` URL.

**8. Configure the Meta Webhook:**
- Go to Meta Developer Dashboard → WhatsApp → Configuration
- Set Callback URL to: `https://your-ngrok-url/api/v1/webhooks/whatsapp`
- Set Verify Token to `WHATSAPP_WEBHOOK_VERIFY_TOKEN` from your `.env`
- Subscribe to the `messages` webhook field

**9. Log in to the vendor dashboard:**
- Open the frontend in your browser (usually `http://localhost:5173`)
- Go to **Login**
- Enter the **Vendor ID** and **phone number** printed by `seed.py`

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
