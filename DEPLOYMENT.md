# VEERA-SAFETY-AI Deployment Guide

## 1. Backend Deployment (Render)
- **Root Directory**: `backend`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**:
  - `PORT`: (Automatically set by Render)
  - `ALLOWED_ORIGINS`: `https://your-frontend.vercel.app`

## 2. Frontend Deployment (Vercel)
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `.next`
- **Environment Variables**:
  - `NEXT_PUBLIC_BACKEND_URL`: `your-backend-service.onrender.com`
  - `NEXT_PUBLIC_WS_URL`: `wss://your-backend-service.onrender.com/stream`

## 3. Local Development
- Copy `frontend/.env.local` and ensure it points to `localhost:8000`.
- Run `npm run dev` in `frontend`.
- Run `uvicorn main:app` in `backend`.
