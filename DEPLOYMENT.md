# SiteCast Deployment Guide

## Option 1: Streamlit Community Cloud (Recommended - Free)

1. **Prepare your repository:**
   ```bash
   git init
   git add .
   git commit -m "Ready for deployment"
   ```

2. **Push to GitHub:**
   - Create a new repository on GitHub
   - Push your code:
     ```bash
     git remote add origin https://github.com/YOUR_USERNAME/SiteCast.git
     git push -u origin main
     ```

3. **Deploy on Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with your GitHub account
   - Click "New app"
   - Select your repository, branch, and main file (main.py)
   - Click "Deploy"

## Option 2: Local Network

Run the app accessible on your local network:
```bash
streamlit run main.py --server.address 0.0.0.0 --server.port 8501
```

Access from any device on your network: `http://YOUR_COMPUTER_IP:8501`

## Option 3: Docker

1. **Build the image:**
   ```bash
   docker build -t sitecast .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8501:8501 sitecast
   ```

## Option 4: Cloud Platforms

### Heroku
```bash
heroku create your-app-name
git push heroku main
```

### Railway
1. Connect your GitHub repo at [railway.app](https://railway.app)
2. It will auto-detect and deploy

### Google Cloud Run
```bash
gcloud run deploy --source .
```

## Environment Variables

If using secrets or API keys, set them in:
- Streamlit Cloud: App settings → Secrets
- Heroku: `heroku config:set KEY=value`
- Docker: `-e KEY=value` flag
- Local: `.streamlit/secrets.toml` file

## Custom Domain

Most platforms support custom domains:
- Streamlit Cloud: In app settings
- Heroku: `heroku domains:add yourdomain.com`
- Cloud Run: Domain mapping in console