# 🛡️ CrowdGuard AI — Predictive Crowd Panic Detection & Containment System

**RV College of Engineering | Interdisciplinary Project**  
**Guide:** Prof. Mithun T P

| USN | Name | Dept |
|-----|------|------|
| 1RV23AI085 | Samruddhi D | AI & ML |
| 1RV23BT044 | Priyam Parashar | Biotech |
| 1RV23CS134 | Meghana D Hegde | CS |
| 1RV23EC128 | Saloni Jadhav | ECE |

---

## 📌 Overview

An end-to-end AI system that detects and predicts crowd violence and panic using **multimodal analysis** (video + audio), generates real-time alerts, and provides a live monitoring dashboard.

### Architecture Pipeline
```
INPUT → PREPROCESS → VIDEO MODEL → AUDIO MODEL → FUSION → RISK SCORE → ALERT → DASHBOARD
```

---

## 🗂️ Project Structure

```
crowd-panic-system/
├── notebook/
│   └── crowdguard_training.ipynb   # Complete Colab training notebook
├── backend/
│   ├── main.py                     # FastAPI app
│   ├── model_loader.py             # Model loading (TF + fallback)
│   ├── inference.py                # Video / audio / multimodal pipelines
│   ├── requirements.txt
│   └── Procfile                    # Render deployment
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx            # Home / landing page
│   │   │   ├── upload/page.tsx     # Analysis upload page
│   │   │   ├── dashboard/page.tsx  # Live dashboard
│   │   │   ├── layout.tsx
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── Navbar.tsx
│   │   │   ├── RiskGauge.tsx       # Canvas-based animated gauge
│   │   │   └── AlertPanel.tsx      # Real-time alert log with audio
│   │   └── lib/
│   │       └── api.ts              # API client
│   ├── package.json
│   ├── tailwind.config.js
│   └── next.config.js
└── README.md
```

---

## 🤖 Models

### Video Model — MobileNetV2 + BiLSTM
- Transfer learning backbone: MobileNetV2 (fine-tune last 30 layers)
- Temporal modelling: Bidirectional LSTM (256 hidden units)
- Input: `(16, 112, 112, 3)` — 16 frames per clip
- Output: `[normal_prob, violence_prob]`
- Target accuracy: **88–92%**

### Audio Model — 2D CNN on MFCC
- Feature: 40 MFCC coefficients × 128 time steps
- 4-block CNN with BatchNorm + GlobalAveragePooling
- Data augmentation: SpecAugment (time & frequency masking)
- Output: `[normal_prob, panic_prob]`
- Target accuracy: **85–90%**

### Multimodal Fusion — Late Fusion
```python
risk_score = 0.6 × violence_prob + 0.4 × panic_prob
```
| Score | Risk Level |
|-------|-----------|
| ≥ 0.70 | 🔴 HIGH |
| ≥ 0.40 | 🟡 MEDIUM |
| < 0.40 | 🟢 LOW |

---

## 🏋️ Training (Google Colab)

1. Open `notebook/crowdguard_training.ipynb` in Google Colab
2. Enable GPU: Runtime → Change runtime type → T4 GPU
3. Run Cell 3 and upload your `kaggle.json`
4. Run all cells sequentially — datasets download automatically
5. Models saved to `/content/models/video_model.h5` and `audio_model.h5`
6. Cell 20 downloads a zip with all models + evaluation charts

### Datasets
| Dataset | Use | Link |
|---------|-----|------|
| Real-Life Violence Situations | Video training | [Kaggle](https://www.kaggle.com/datasets/mohamedmustafa/real-life-violence-situations-dataset) |
| UCF Crime Dataset | Video (optional) | [Kaggle](https://www.kaggle.com/datasets/mission-ai/crimeucfdataset) |
| SCVD Dataset | Video (optional) | [Kaggle](https://www.kaggle.com/datasets/toluwaniaremu/smartcity-cctv-violence-detection-dataset-scvd) |
| Audio Violence Dataset | Audio training | [Kaggle](https://www.kaggle.com/datasets/fangfangz/audio-based-violence-detection-dataset) |

---

## 🚀 Backend Deployment (Render)

### Local Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Render Deployment
1. Push `backend/` folder to a GitHub repo
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your GitHub repo
4. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free (or Starter for GPU)
5. Add Environment Variables (optional):
   ```
   VIDEO_MODEL_PATH=models/video_model.h5
   AUDIO_MODEL_PATH=models/audio_model.h5
   ```
6. Deploy → Copy your public URL

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/health` | System status |
| POST | `/analyze/video` | Video violence analysis |
| POST | `/analyze/audio` | Audio panic analysis |
| POST | `/analyze/multimodal` | Combined video + audio |
| GET | `/demo/simulate` | Simulated result for testing |

#### Example Request
```bash
curl -X POST https://your-api.onrender.com/analyze/video \
  -F "file=@crowd_video.mp4"
```

#### Response JSON
```json
{
  "job_id": "uuid-...",
  "violence_score": 0.823,
  "panic_score": 0.741,
  "risk_level": "HIGH",
  "confidence": 0.912,
  "processing_time_ms": 342.1,
  "alert_triggered": true,
  "details": {
    "frames_analyzed": 16,
    "fusion_method": "late_fusion",
    "fused_score": 0.790
  }
}
```

---

## 🌐 Frontend Deployment (Vercel)

### Local Setup
```bash
cd frontend
npm install
npm run dev         # http://localhost:3000
```

### Vercel Deployment
1. Push `frontend/` to GitHub
2. Go to [vercel.com](https://vercel.com) → New Project → Import repo
3. Framework Preset: **Next.js**
4. Add Environment Variable:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
   ```
5. Deploy

### Pages
| Route | Description |
|-------|-------------|
| `/` | Landing page with system overview |
| `/upload` | Upload video/audio for analysis |
| `/dashboard` | Live monitoring dashboard with real-time charts |

---

## 🔔 Features
- **Video analysis** — CNN+LSTM violence detection
- **Audio analysis** — MFCC + CNN panic/distress detection
- **Multimodal fusion** — Late fusion with configurable weights
- **Risk scoring** — LOW / MEDIUM / HIGH with thresholds
- **Alert sound** — Web Audio API alarm on HIGH risk detection
- **Live dashboard** — Real-time gauges, area charts, bar charts, alert log
- **Edge compatible** — Demo mode runs without GPU

---

## 📊 Expected Performance
| Metric | Video Model | Audio Model | Fused |
|--------|------------|------------|-------|
| Accuracy | ~90% | ~87% | ~91% |
| Precision | ~89% | ~86% | ~90% |
| Recall | ~91% | ~88% | ~92% |
| F1-Score | ~90% | ~87% | ~91% |

---

## 🔬 References
1. Sreenu G. et al. (2024). Violence detection using nuanced facial expression analysis. *Systems and Soft Computing*, 6.
2. Ramzan M. et al. (2019). State-of-the-Art Violence Detection Techniques. *IEEE Access*, 7.
3. Zhang T. et al. (2016). Violence Detection in Surveillance Scenes. *Multimedia Tools and Applications*, 75.
4. Wu P. et al. (2023). Weakly Supervised Audio-Visual Violence Detection. *IEEE Trans. Multimedia*, 25.
5. Bakhshi A. et al. (2023). Violence Detection Using Lightweight Deep Neural Networks. *Procedia CS*, 222.

---

*© 2024 CrowdGuard AI — RV College of Engineering*
