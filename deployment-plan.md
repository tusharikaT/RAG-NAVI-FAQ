# Deployment Plan

This document outlines the strategy and step-by-step instructions for deploying the **Navi Mutual Fund FAQ Assistant** to production, utilizing **Railway** for the FastAPI backend and **Vercel** for the Next.js frontend.

## 1. Codebase Preparations Needed (Pre-Deployment)

Before deploying, we need to make a small adjustment to the frontend code so it knows how to talk to the production backend instead of the local machine.

- **Frontend Update**: In `frontend/src/app/page.tsx`, the fetch URL is currently hardcoded to `http://127.0.0.1:8000/api/v1/query`. We need to change this to use an environment variable:
  ```javascript
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
  const response = await fetch(`${apiUrl}/api/v1/query`, { ... });
  ```
- **Backend Port**: Railway dynamically assigns ports via the `$PORT` environment variable. By default, Railway's Nixpacks builder knows how to run Python apps, but we will explicitly define the start command to bind to `0.0.0.0`.

---

## 2. Backend Deployment (Railway)

We are deploying the FastAPI server to Railway. 

**How ChromaDB works in production here:**
Because our GitHub Action scheduler runs daily and *pushes* the updated `data/chroma_db` folder back to the `main` branch, **Railway will automatically redeploy every day at 10:00 AM IST** with the freshest mutual fund data! You do not need to set up a persistent volume on Railway.

### Steps:
1. Go to [Railway.app](https://railway.app/) and create an account/login.
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Select your repository: `tusharikaT/RAG-NAVI-FAQ`.
4. Click **Add Variables** before deploying:
   - `GROQ_API_KEY`: `<your_groq_api_key>`
5. Once the service is created, go to the service **Settings**:
   - Scroll down to **Deploy**.
   - Under **Custom Start Command**, enter:
     ```bash
     python -m uvicorn app.api:app --host 0.0.0.0 --port $PORT
     ```
6. Go to the **Networking** tab and click **Generate Domain** to get a public URL for your backend (e.g., `rag-navi-faq-production.up.railway.app`).
7. **Copy this Domain URL**. You will need it for the frontend!

---

## 3. Frontend Deployment (Vercel)

We are deploying the Next.js UI to Vercel.

### Steps:
1. Go to [Vercel.com](https://vercel.com/) and create an account/login.
2. Click **Add New...** -> **Project**.
3. Import your GitHub repository: `tusharikaT/RAG-NAVI-FAQ`.
4. In the **Configure Project** screen:
   - **Root Directory**: Click Edit and select the `frontend` folder.
   - **Framework Preset**: It should automatically detect **Next.js**.
5. Expand the **Environment Variables** section and add:
   - Name: `NEXT_PUBLIC_API_URL`
   - Value: `https://<your-railway-domain-from-step-6>` *(Ensure there is no trailing slash, e.g., `https://rag-navi-faq-production.up.railway.app`)*
6. Click **Deploy**.

Vercel will build the Tailwind CSS and Next.js app and provide you with a live, production URL!

---

## 4. Post-Deployment Verification

1. Open your Vercel URL in your browser.
2. Ask a question like "What is the expense ratio of Navi Nifty 50?".
3. Ensure the backend responds correctly. If it fails, check the Railway logs to ensure the `GROQ_API_KEY` is set and the server started successfully.
