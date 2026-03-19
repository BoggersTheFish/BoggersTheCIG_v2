# BoggersTheCIG-v2 — Git Setup

## Push to GitHub

1. **Initialize git** (if not already):
   ```bash
   cd BoggersTheCIG_v2
   git init
   ```

2. **Create .gitignore** (optional but recommended):
   ```
   __pycache__/
   *.pyc
   .venv/
   venv/
   ```

3. **Add and commit**:
   ```bash
   git add .
   git commit -m "BoggersTheCIG-v2 MAX-SPEED edition"
   ```

4. **Create repo on GitHub** (github.com → New repository → e.g. `BoggersTheCIG-v2`)

5. **Push**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/BoggersTheCIG-v2.git
   git branch -M main
   git push -u origin main
   ```

6. **Enable Actions** — Workflow will run every 5 minutes automatically.

## One-Liner (after repo exists)

```bash
git init && git add . && git commit -m "BoggersTheCIG-v2 MAX-SPEED" && git remote add origin https://github.com/YOUR_USERNAME/BoggersTheCIG-v2.git && git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.
