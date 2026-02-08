# Deployment Guide (Render.com)

This guide helps you deploy your **WhatsApp Chat Analyser** to the web using **Render.com** (a free and easy hosting platform).

## Prerequisites
1.  **GitHub Account**: You need to upload your code to a GitHub Repository.
2.  **Render Account**: Sign up at [dashboard.render.com](https://dashboard.render.com/).

## Step 1: Push Code to GitHub
1.  Create a **New Repository** on GitHub (e.g., `whatsapp-analyser`).
2.  Open your terminal in the project folder and run:
    ```bash
    git init
    git add .
    git commit -m "Initial commit"
    git branch -M main
    git remote add origin https://github.com/YOUR_USERNAME/whatsapp-analyser.git
    git push -u origin main
    ```

## Step 2: Create Web Service on Render
1.  Go to your **Render Dashboard** and click **"New +"** -> **"Web Service"**.
2.  Select **"Build and deploy from a Git repository"**.
3.  Connect your GitHub account and select your `whatsapp-analyser` repo.

## Step 3: Configure Settings
Fill in the details:
*   **Name**: `whatsapp-chat-analyser` (or anything you like)
*   **Region**: Frankfurt or Singapore (closest to you)
*   **Branch**: `main`
*   **Root Directory**: (Leave blank)
*   **Runtime**: `Python 3`
*   **Build Command**: `pip install -r requirements.txt`
*   **Start Command**: `gunicorn app:app`

## Step 4: Environment Variables (Critical!)
Scroll down to **"Environment Variables"** and click **"Add Environment Variable"**. Add these keys from your `.env` file:

| Key | Value |
| :--- | :--- |
| `GEMINI_API_KEY` | `AIzaSy...` (Your Actual API Key) |
| `SECRET_KEY` | `any_random_string` (Generate one) |
| `MAIL_USERNAME` | `your_email@gmail.com` |
| `MAIL_PASSWORD` | `your_app_password` |

> **Note**: Do NOT copy the `.env` file itself. Render needs these variables manually entered.

## Step 5: Deploy
1.  Click **"Create Web Service"**.
2.  Render will start building your app. It may take 2-3 minutes.
3.  Once finished, you will see a green **"Live"** badge and a URL (e.g., `https://whatsapp-analyser.onrender.com`).

**Success!** Your app is now live on the internet.
