# ✨ Glowup Coach

**AI-powered facial aesthetics coaching — $0 running cost.**

Analyzes your face using 468 MediaPipe landmarks, computes a gender-specific Glow Score (0–100), ranks you on a global leaderboard, and delivers expert-guided improvement tips with medical disclaimers.

---

## 🚀 Quick Start (Local)

```bash
# One command to start everything:
bash start.sh
```

Then open **http://localhost:5173**

> **API Docs**: http://localhost:8000/docs

---

## 🧬 How It Works

1. **Sign up** → choose your gender (sets scoring weights)
2. **Consent** → biometric scanning disclosure
3. **30-second scan** → webcam captures 1 frame every 3 seconds (10 total)
4. **Analysis** → MediaPipe extracts 468 facial landmarks per frame
5. **Score** → gender-specific weighted scoring across 10 features
6. **Results** → animated score reveal + radar chart + expandable AI tips
7. **Leaderboard** → global ranking with male/female filters

---

## ⚧ Gender-Specific Scoring Weights

| Feature | Male | Female |
|---|---|---|
| Bilateral Symmetry | 18% | 22% |
| Jawline | **17%** | 3% |
| Eye Shape | 10% | **15%** |
| Lip Shape | 8% | **12%** |
| Golden Ratio | 10% | 13% |
| Nose Profile | 13% | 7% |
| Facial Harmony | 5% | 3% |
| *(+ others)* | | |

You can override your gender setting at any time in Settings → the system re-scores with the appropriate weights.

---

## 🏗 Architecture

```
glowup-coach/
├── backend/          FastAPI + SQLite + MediaPipe
│   ├── main.py       All routes + WebSocket
│   ├── analyzer.py   MediaPipe FaceMesh engine
│   ├── scorer.py     Gender-specific weighted scoring
│   ├── guidance.py   Rule-based tips + Ollama hook
│   └── auth.py       JWT + argon2 auth
├── frontend/         React (Vite)
│   └── src/pages/    Auth, Scan, Results, Leaderboard
├── start.sh          One-command launcher
└── docker-compose.yml
```

---

## 🔒 Privacy & Compliance

- **No images stored** — frames are processed in-memory and discarded
- **Only numeric metrics stored** — landmark distances, ratios
- **Biometric consent modal** before every scan session
- **Medical disclaimers** on every guidance tip
- **Gender override** available at any time
- **Delete account** → removes all data: `DELETE /auth/account`

---

## 🐋 VPS Deployment (Oracle Cloud Free Tier)

```bash
# On your VPS:
git clone <your-repo>
cd glowup-coach
docker compose up -d
```

### Phase 2: Enable Ollama LLM
```bash
# Uncomment the ollama service in docker-compose.yml, then:
docker compose up -d ollama
docker exec glowup-ollama ollama pull llama3:8b
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/signup` | Register new user |
| POST | `/auth/login` | Get JWT token |
| POST | `/auth/logout` | Blacklist token |
| GET | `/auth/me` | Current user info |
| PATCH | `/auth/gender` | Update gender |
| DELETE | `/auth/account` | Delete account |
| POST | `/analyze` | Analyze one frame |
| POST | `/analyze/finalize` | Save final averaged score |
| GET | `/leaderboard` | Top 50 scores |
| GET | `/scores/me` | My score history |
| WS | `/ws/scan/{user_id}` | Real-time scan notifications |

---

## ⚕️ Disclaimer

Glowup Coach is a **cosmetic guidance tool only** and does not constitute medical advice. All suggestions require consultation with a qualified healthcare professional. Facial geometry metrics are educational and should not be used to make medical decisions.

---

*Built with MediaPipe · FastAPI · React · SQLite — $0/month*
