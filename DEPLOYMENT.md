# Deployment Guide

This project is separated into a FastAPI Backend and a Next.js Frontend.

## Backend Deployment (Render)

Render is perfect for deploying Python FastAPI applications.

1. Create a new **Web Service** on [Render](https://render.com/).
2. Connect your GitHub repository containing this codebase.
3. Set the Root Directory to `backend`.
4. Environment Setup:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
5. Render will automatically expose your API (e.g., `https://your-api.onrender.com`).
6. Update the Frontend WebSocket URL in `frontend/src/components/Dashboard.tsx` to point to `wss://your-api.onrender.com/stream`.

## Frontend Deployment (Vercel)

Vercel is the optimal platform for Next.js applications.

1. Log in to [Vercel](https://vercel.com/) and click "Add New Project".
2. Import your GitHub repository.
3. Configure the Project:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
4. Click **Deploy**. Vercel will automatically build and host your Next.js application.

## Local Execution

To run locally, you need two terminal windows.

**Terminal 1 (Backend)**:
```bash
cd backend
python -m venv venv
source venv/Scripts/activate # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

**Terminal 2 (Frontend)**:
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.
