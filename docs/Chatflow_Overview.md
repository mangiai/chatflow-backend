
# 🧠 ChatFlow — Full SaaS Overview (from Day 1 → Production)

## 🏁 Project Genesis
ChatFlow started as an idea to create a **universal AI chat widget** that any business could embed on their website — similar to Intercom or Crisp, but powered by **LLMs and knowledge-base intelligence**.

The goal was simple but ambitious:
> “Allow businesses to upload their PDFs, FAQs, or data — then embed a small script on their site to enable AI-driven chat support.”

---

## 🧱 Core Architecture

| Layer | Stack | Purpose |
|-------|--------|----------|
| Frontend (App + Widget) | React (SWC) + Vite | Web dashboard for businesses + Embeddable widget for customer websites |
| Backend (API) | FastAPI + PostgreSQL + SQLAlchemy + JWT | Business management, user auth, knowledge ingestion, Q&A endpoints |
| Vector DB | Qdrant | Stores embeddings for semantic retrieval |
| LLM Layer | OpenAI (LangChain + LangChain Qdrant) | Provides contextual chat answers |
| Deployment | Ubuntu VPS + Nginx + PM2 + Certbot SSL | Full production stack |
| Build/Infra Tools | Lovable builder + Vite + Uvicorn | Fast iterative builds for frontend + backend |

---

## 📆 Project Timeline

### Phase 1 — Backend Bootstrapping
- FastAPI boilerplate (auth/signup/login + JWT)
- PostgreSQL integration with SQLAlchemy
- LangChain + Qdrant retrieval pipeline
- File parsing (PDF, DOCX)
- Email + password validation (pydantic[email], passlib, bcrypt)
- Manual Q&A via Swagger ✅

### Phase 2 — Frontend Development
- React interface via Lovable
- Business registration + knowledge upload
- Chat UI built (ChatBox)
- Dark-mode + localStorage persistence

### Phase 3 — Widget System
- Vite widget build (`vite.config.widget.ts`)
- Outputs: `chatflow-widget.js` & `widget.html`
- Embeddable via:
  ```html
  <script src="https://chat.safe-hands.health/widget/chatflow-widget.js" data-business="..."></script>
  ```
- Floating chat bubble + chat window
- Cross-origin embedding handled with CSP headers

### Phase 4 — Production Deployment
- API + Frontend on VPS
- Subdomains: `api.safe-hands.health` & `chat.safe-hands.health`
- SSL via Let’s Encrypt
- PM2 process management
- Nginx alias + routing setup
- Production tested + verified ✅

---

## 🌍 Infrastructure

| Component | Domain | Port | PM2 Process | Status |
|------------|---------|------|-------------|---------|
| Backend (API) | api.safe-hands.health | 8500 | chatflow-backend | ✅ Running |
| Frontend (App + Widget) | chat.safe-hands.health | 3500 | chatflow-frontend | ✅ Running |

---

## 🧩 APIs and Modules

| Module | Description |
|---------|--------------|
| `/auth/signup`, `/auth/login` | JWT auth for businesses |
| `/knowledge/upload` | Upload + embed docs into Qdrant |
| `/chat/query` | Retrieve contextual LLM answers |
| `/business/config` | Widget customization + branding |
| `/token/refresh` | Session refresh |

---

## 🚀 Features Completed
- ✅ JWT Auth + Signup/Login
- ✅ Knowledge Upload (PDF/DOCX)
- ✅ LangChain + Qdrant Q&A
- ✅ React Frontend + ChatBox
- ✅ Embeddable Widget + Multi-tenant
- ✅ HTTPS, SSL, and Nginx routing
- ✅ Live testing verified

---

## ⚙️ Pending Milestones

| Feature | Description | Priority |
|----------|--------------|-----------|
| 💳 Payment Gateway | Stripe integration + billing webhooks | High |
| 🧍 Avatar Images | Upload + configuration | High |
| 🎨 Widget Customization | Themes, colors, positions | Medium |
| 🧾 Analytics Dashboard | Chat + lead tracking | Medium |
| 💬 Persistent Chat Sessions | Cache + server memory | Medium |
| 🌐 i18n Support | Multi-language text | Low |

---

## 🧰 Build / Deploy Commands

```bash
npm install
npm run build
npx vite build --config vite.config.widget.ts
sudo nginx -t && sudo systemctl reload nginx
pm2 restart chatflow-frontend
pm2 restart chatflow-backend
```

---

## 🧭 Vision Roadmap

1. Phase 2 – Monetization & Branding
   - Stripe plans (free/pro/enterprise)
   - Custom branding + dashboard

2. Phase 3 – Automation & AI Agents
   - LangGraph multi-agent support
   - Smart lead qualification

3. Phase 4 – Public Launch
   - Landing page + trials + billing
   - Self-service onboarding
