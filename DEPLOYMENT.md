# Less Token - Deployment & Release Guide

Complete deployment guide for Less Token desktop application and landing page.

## Deployment Architecture

```
Frontend (React)          Backend (Flask)
    ↓                          ↓
Vercel                    Cloud Platform
(CDN + Edge)          (Heroku/Railway/Fly.io)
```

## Frontend Deployment (Vercel)

### 1. Push to GitHub
```bash
git add .
git commit -m "feat: web app with React + Flask"
git push origin main
```

### 2. Connect to Vercel
```bash
# Option A: Vercel CLI
npm i -g vercel
cd web
vercel

# Option B: Vercel Dashboard
# https://vercel.com/new → Connect GitHub repo
```

### 3. Set Environment Variables
In Vercel Dashboard → Settings → Environment Variables:
```
VITE_API_URL=https://api.yourdomain.com
```

### 4. Deploy
```bash
vercel deploy --prod
```

Frontend will be live at: `https://your-project.vercel.app`

---

## Desktop App Release (Windows)

### 1. Build Executable with PyInstaller
```bash
pip install pyinstaller
python -m PyInstaller --onefile --windowed --name "Less Token" main.py
# Output: dist/Less Token.exe (23.6 MB)
```

### 2. Create Windows Installer with NSIS
Prerequisites:
```bash
# Install NSIS from: https://nsis.sourceforge.io/
# Or via chocolatey: choco install nsis
```

Build installer:
```bash
# Navigate to project root
cd C:\Projects\AIClipboardOptimizer

# Run NSIS compiler
makensis installer.nsi
# Output: lesstoken-setup.exe (5-10 MB)
```

### 3. Create GitHub Release
```bash
# Tag release
git tag v1.0.0
git push origin v1.0.0

# Create release with downloads
gh release create v1.0.0 dist/"Less Token.exe" \
  --title "Less Token v1.0.0" \
  --notes "Release notes here"

# Add installer to release
gh release upload v1.0.0 lesstoken-setup.exe
```

### 4. Distribution
Users can download:
- **Portable**: Less Token.exe (standalone, no installation)
- **Installer**: lesstoken-setup.exe (adds Start Menu shortcuts, Registry entries)

---

## Landing Page Deployment (Vercel)

### 1. Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

EXPOSE 5000

CMD ["gunicorn", \
     "-w", "4", \
     "-b", "0.0.0.0:5000", \
     "-t", "120", \
     "src.aiclipboardoptimizer.web:create_app()"]
```

### 2. Deploy Options

#### Option A: Heroku (Simplest)
```bash
heroku login
heroku create your-app-name
heroku config:set AI_CLIPBOARD_OPTIMIZER_CLAUDE_API_KEY=your-key
git push heroku main
```

#### Option B: Railway (Modern)
```bash
# Connect railway.app account
railway link
railway up
```

#### Option C: Fly.io (Fast)
```bash
fly auth login
fly launch
fly deploy
```

### 3. Set Production Environment Variables

In your platform's dashboard, set:
```
AI_CLIPBOARD_OPTIMIZER_AI_PROVIDER=claude
AI_CLIPBOARD_OPTIMIZER_CLAUDE_API_KEY=your-key
AI_CLIPBOARD_OPTIMIZER_OUTPUT_DIR=/tmp
```

---

## API Configuration

Update frontend `VITE_API_URL` to point to deployed backend:

```typescript
// web/src/api.ts
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'
```

---

## Monitoring & Logs

### Vercel
- Dashboard → Deployments → Logs

### Heroku
```bash
heroku logs --tail
```

### Railway
- Dashboard → Logs tab

### Fly.io
```bash
fly logs
```

---

## Custom Domain

### Vercel Frontend
1. Buy domain (Vercel Domains or external)
2. Dashboard → Settings → Domains
3. Add domain + DNS records

### Backend API
1. Create subdomain `api.yourdomain.com`
2. Point to your platform (e.g., `your-app.herokuapp.com`)

---

## Cost Estimates

| Service | Free Tier | Paid |
|---------|-----------|------|
| Vercel (Frontend) | ✅ 100GB/mo | $20+/mo |
| Heroku (Backend) | ✅ Removed | $7+/dyno |
| Railway | ✅ \$5/mo | Pay-as-you-go |
| Fly.io | ✅ 3 shared-cpu VMs | \$0.003/hour |

**Recommendation**: Railway or Fly.io for backend (cheaper than Heroku)

---

## Testing Deployment

```bash
# Test backend health
curl https://api.yourdomain.com/health

# Test frontend
open https://your-project.vercel.app
```

---

## Rollback

### Vercel
Dashboard → Deployments → Select previous → Redeploy

### Heroku
```bash
heroku releases
heroku rollback v123
```

### Railway
Dashboard → Deployments → Redeploy

---

## Security Checklist

- [ ] API keys in environment variables (never in code)
- [ ] HTTPS enabled (automatic on Vercel/Heroku)
- [ ] CORS configured correctly
- [ ] Rate limiting enabled
- [ ] Logging configured for production
- [ ] No debug mode in production
- [ ] Database backups configured (if using DB)

---

## Support

For deployment issues:
- Check logs first
- Verify environment variables are set
- Test API locally before deploying
- Check status page of your platform
