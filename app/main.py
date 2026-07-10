from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.webhooks import router as webhooks_router
from app.api.posteering_webhooks import router as posteering_webhooks_router
from app.api.admin import router as admin_router
from app.api.vendor import router as vendor_router
from app.core.celery_app import celery_app
from app.database.base import Base
from app.database.session import engine
import app.models  # noqa: F401 — ensures all models are imported before create_all

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Create all database tables on startup (safe to run repeatedly)
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Warning: Could not create database tables: {e}")

app.include_router(webhooks_router, prefix="/api/v1/webhooks", tags=["webhooks"])
app.include_router(posteering_webhooks_router, prefix="/api/v1/posteering", tags=["posteering"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(vendor_router, prefix="/api/v1/vendor", tags=["vendor"])


@app.get("/")
def root():
    return {"message": "WhatsApp AI Assistant API is running."}


@app.get("/privacy-policy", response_class=HTMLResponse)
def privacy_policy():
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Privacy Policy - VIOLET WhatsApp Commerce Bot</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: Inter, sans-serif; background: #0f0f13; color: #e2e8f0; line-height: 1.8; }
    header { background: linear-gradient(135deg, #6c3de8 0%, #9b59b6 100%); padding: 60px 24px 40px; text-align: center; }
    header h1 { font-size: 2.2rem; font-weight: 700; color: #fff; margin-bottom: 8px; }
    header p { color: rgba(255,255,255,0.75); font-size: 1rem; }
    .badge { display: inline-block; background: rgba(255,255,255,0.15); color: #fff; border-radius: 20px; padding: 4px 16px; font-size: 0.8rem; margin-bottom: 16px; border: 1px solid rgba(255,255,255,0.2); }
    main { max-width: 820px; margin: 0 auto; padding: 48px 24px 80px; }
    section { background: #1a1a24; border: 1px solid #2a2a3a; border-radius: 12px; padding: 32px; margin-bottom: 24px; }
    section h2 { font-size: 1.15rem; font-weight: 600; color: #a78bfa; margin-bottom: 14px; }
    section p, section li { color: #94a3b8; font-size: 0.95rem; }
    section ul { padding-left: 20px; margin-top: 8px; }
    section ul li { margin-bottom: 6px; }
    .highlight { background: rgba(108,61,232,0.12); border-left: 3px solid #6c3de8; padding: 12px 16px; border-radius: 0 8px 8px 0; margin-top: 12px; color: #a78bfa !important; font-size: 0.9rem; }
    .contact-box { background: rgba(108,61,232,0.1); border: 1px solid rgba(108,61,232,0.3); border-radius: 10px; padding: 20px; margin-top: 12px; }
    .contact-box p { color: #cbd5e1; }
    .contact-box a { color: #a78bfa; text-decoration: none; font-weight: 500; }
    footer { text-align: center; padding: 32px 24px; color: #4a5568; font-size: 0.85rem; border-top: 1px solid #1e1e2e; }
    footer span { color: #6c3de8; }
    a { color: #a78bfa; }
  </style>
</head>
<body>
<header>
  <div class="badge">Legal Document</div>
  <h1>Privacy Policy</h1>
  <p>VIOLET WhatsApp Commerce Bot &bull; Effective Date: June 29, 2026</p>
</header>
<main>
  <section><h2>1. Introduction</h2><p>VIOLET is a WhatsApp-powered commerce assistant that connects customers with local vendors and dispatch riders. This Privacy Policy explains how we collect, use, store, and protect your personal information when you interact with VIOLET through WhatsApp.</p><p class="highlight">By messaging VIOLET, you agree to the collection and use of your information as described in this policy.</p></section>
  <section><h2>2. Information We Collect</h2><p>When you interact with VIOLET, we may collect:</p><ul><li><strong>Phone Number:</strong> Your WhatsApp phone number, used to identify you and send replies.</li><li><strong>Messages:</strong> The text content of messages you send to VIOLET for processing your orders.</li><li><strong>Order Information:</strong> Details about products or services you request, including delivery addresses.</li><li><strong>Transaction Records:</strong> Orders placed, payments initiated, and delivery status updates.</li><li><strong>Vendor Information:</strong> Business name, location, products, and contact details provided during onboarding.</li></ul></section>
  <section><h2>3. How We Use Your Information</h2><p>We use the information we collect solely to:</p><ul><li>Process your orders and connect you with local vendors.</li><li>Send order confirmations, delivery updates, and receipts via WhatsApp.</li><li>Facilitate payment processing and virtual account generation.</li><li>Provide customer support and resolve disputes.</li><li>Improve the VIOLET service and fix technical issues.</li></ul><p class="highlight">We do NOT sell, rent, or share your personal data with third parties for marketing purposes.</p></section>
  <section><h2>4. Data Storage and Security</h2><p>Your data is stored securely on encrypted cloud servers. We implement industry-standard security measures including encrypted database connections (TLS/SSL), secure API tokens, hashed credentials, and access controls. While we take every reasonable precaution, no method of internet transmission is 100% secure.</p></section>
  <section><h2>5. Third-Party Services</h2><p>VIOLET uses the following trusted third-party services:</p><ul><li><strong>Meta / WhatsApp Business API:</strong> For sending and receiving messages. Subject to <a href="https://www.whatsapp.com/legal/privacy-policy">WhatsApp's Privacy Policy</a>.</li><li><strong>Anthropic (Claude AI):</strong> For AI-powered conversation processing. Subject to <a href="https://www.anthropic.com/privacy">Anthropic's Privacy Policy</a>.</li><li><strong>Railway:</strong> For secure cloud server infrastructure.</li><li><strong>Payment Processors:</strong> For generating virtual accounts and processing transactions.</li></ul></section>
  <section><h2>6. Data Retention</h2><p>We retain your personal data for as long as necessary to provide our services:</p><ul><li><strong>Order records</strong> are retained for up to 2 years for accounting and dispute resolution.</li><li><strong>Conversation data</strong> is retained for 90 days to enable customer support.</li><li><strong>Account data</strong> is retained until you request deletion.</li></ul></section>
  <section><h2>7. Your Rights</h2><p>You have the right to access, correct, or delete the personal data we hold about you. You may also opt out of non-essential communications by messaging VIOLET "STOP". To exercise any of these rights, please contact us using the details below.</p></section>
  <section><h2>8. Children's Privacy</h2><p>VIOLET is not intended for use by individuals under the age of 13. We do not knowingly collect personal information from children. If you believe a child has provided us with their information, please contact us immediately.</p></section>
  <section><h2>9. Contact Us</h2><p>If you have any questions about this Privacy Policy, please reach out:</p><div class="contact-box"><p><strong>VIOLET Support</strong></p><p>WhatsApp: <a href="https://wa.me/2347071149334">+234 707 114 9334</a></p><p>Business: David Smith &bull; Nigeria</p></div></section>
  <section><h2>10. Changes to This Policy</h2><p>We may update this Privacy Policy from time to time. When we do, we will update the effective date at the top of this page. Continued use of VIOLET after any changes constitutes your acceptance of the updated policy.</p></section>
</main>
<footer><p>&copy; 2026 VIOLET Commerce Bot &bull; Built by <span>Posteering</span> &bull; All rights reserved.</p></footer>
</body>
</html>"""
