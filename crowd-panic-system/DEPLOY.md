# CrowdGuard AI - Deployment Guide

This guide covers deploying the CrowdGuard AI Crowd Panic Detection System to production.

## Architecture

```
┌─────────────────────┐         ┌─────────────────────┐
│   Frontend (Vercel) │────────▶│   Backend (Render)  │
│   Next.js 14        │         │   FastAPI + TF      │
│   Port: 80/443      │         │   Port: 10000       │
└─────────────────────┘         └─────────────────────┘
```

---

## Backend Deployment (Render)

### 1. Create a Render Account
- Go to [render.com](https://render.com) and sign up
- Connect your GitHub repository

### 2. Create a Web Service
- **Name**: `crowdguard-backend`
- **Environment**: `Python 3.12`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

> **Option**: You can also use the `render.yaml` file in the backend folder for automatic configuration via Render Blueprint.

### 3. Environment Variables
Add these in Render dashboard:
```
PYTHON_VERSION=3.12
TF_ENABLE_ONEDNN_OPTS=0
UPLOAD_DIR=/tmp/uploads
MAX_UPLOAD_SIZE=104857600
```

### 3. Environment Variables
Add these in Render dashboard:
```
PYTHON_VERSION=3.12
TF_ENABLE_ONEDNN_OPTS=0
```

### 4. Deploy
- Click "Create Web Service"
- Wait for deployment to complete
- Note your backend URL (e.g., `https://crowdguard-backend.onrender.com`)

---

## Frontend Deployment (Vercel)

### 1. Create a Vercel Account
- Go to [vercel.com](https://vercel.com) and sign up
- Connect your GitHub repository

### 2. Import Project
- Import the `crowd-panic-system/frontend` folder as a new project

### 3. Configure Environment Variables
Add in Vercel dashboard:
```
NEXT_PUBLIC_API_URL=https://crowdguard-backend.onrender.com
```

### 4. Deploy
- Click "Deploy"
- Wait for build to complete
- Your frontend will be live at `https://your-project.vercel.app`

---

## Alternative: Deploy Backend to Railway

### 1. Create Railway Account
- Go to [railway.app](https://railway.app) and sign up

### 2. Deploy Backend
- Create new project → "Deploy from GitHub repo"
- Select your backend folder
- Environment: Python 3.12
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### 3. Get Backend URL
- Note your Railway app URL
- Update frontend's `NEXT_PUBLIC_API_URL` accordingly

---

## Local Production Build

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run build
npm start
```

---

## Troubleshooting

### CORS Issues
If frontend can't reach backend, ensure backend has CORS configured:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific Vercel domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Model Loading Errors
The backend uses mock models if real `.h5` files aren't found. For production:
1. Train your models (CNN+LSTM for video, 1D CNN for audio)
2. Place them in `backend/models/` folder
3. Set environment variables: `VIDEO_MODEL_PATH`, `AUDIO_MODEL_PATH`

### Memory Issues
If deployment runs out of memory, add to Render/Railway:
```
PYTHONBLABLA=1
```

---

## Quick Deploy Buttons

### Render (Backend)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/your-repo)

### Vercel (Frontend)
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/your-repo/frontend)

---

## Production URLs (Example)

After deployment, your URLs will be:
- **Frontend**: `https://crowdguard-frontend.vercel.app`
- **Backend API**: `https://crowdguard-backend.onrender.com`
- **API Docs**: `https://crowdguard-backend.onrender.com/docs`

Update the frontend's `NEXT_PUBLIC_API_URL` to point to your backend URL.