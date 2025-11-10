# Product Delivery Demo - Quick Start Guide

## TL;DR

```powershell
# 1. Make sure you're on the right git commit (Nov 7, 2025 or later)
git checkout 0e7316d

# 2. Start backend (in arash/product-delivery-demo directory)
cd arash/product-delivery-demo/backend
py api.py

# 3. Start frontend (in new terminal)
cd arash/product-delivery-demo/frontend
npm run dev

# 4. Open browser
http://localhost:3000
```

## What You Need

- **Python 3.10+** (check: `py --version`)
- **Node.js 16+** (check: `node --version`)
- **npm** (check: `npm --version`)

## First Time Setup

```bash
# Install Python dependencies
cd arash/product-delivery-demo
pip install -r requirements.txt

# Install Node dependencies
cd frontend
npm install
cd ..
```

## Running the Demo

### Option 1: Two Terminals (Recommended for debugging)

**Terminal 1 - Backend:**
```bash
cd arash/product-delivery-demo/backend
py api.py
```

Wait for:
```
[OK] Loaded ZurvanGraph(centers=3, distributors=8, edges=24)
Starting FastAPI server...
API: http://127.0.0.1:8000
```

**Terminal 2 - Frontend:**
```bash
cd arash/product-delivery-demo/frontend
npm run dev
```

Wait for:
```
VITE v5.4.20  ready in 546 ms
➜  Local:   http://localhost:3000/
```

**Open:** http://localhost:3000

### Option 2: Background Processes (Windows)

```powershell
cd arash/product-delivery-demo

# Start backend
Start-Process -NoNewWindow -FilePath "py" -ArgumentList "backend\api.py"

# Start frontend
cd frontend
Start-Process -NoNewWindow cmd -ArgumentList "/c", "npm run dev"

# Wait 5-10 seconds, then open browser
```

## Verify It's Running

```powershell
# Check both servers are listening
netstat -ano | findstr ":8000"   # Backend should show LISTENING
netstat -ano | findstr ":3000"   # Frontend should show LISTENING
```

## What You Should See

1. **Geographic map** of the United States
2. **3 manufacturing centers** (Chicago, Pittsburgh, Nashville)
3. **8 distributors** across the US
4. **Simulation controls** (Play/Pause/Reset/Speed)
5. **Chat panel** on the right
6. **Live metrics** dashboard

## Common Issues

**"python is not recognized"** → Use `py` instead of `python`

**"Port 8000 already in use"** → Kill the existing process:
```powershell
netstat -ano | findstr ":8000"
taskkill /PID <process_id> /F
```

**Frontend shows different port** → Vite may use 3001, 3002, etc. if 3000 is busy. Check terminal output.

**Blank page in browser** → 
- Open browser console (F12) for errors
- Verify backend is running: http://127.0.0.1:8000
- Hard refresh: Ctrl+F5

## Stopping the Demo

**If running in terminals:** Press `Ctrl+C` in each terminal

**If running in background:**
```powershell
# Find and kill Python processes
Get-Process | Where-Object {$_.ProcessName -match "python|py"}
Stop-Process -Name python -Force

# Find and kill Node processes
Get-Process | Where-Object {$_.ProcessName -eq "node"}
Stop-Process -Name node -Force
```

## Interactive Features

Once running:
- **Click nodes** to see detailed stats (inventory, orders, financials)
- **Use simulation controls** to pause/resume/speed up
- **Try chat commands** (requires Ollama):
  - "Increase Chicago production to 25 units per hour"
  - "Add a distributor in Dallas, Texas"
  - "Show Pittsburgh status"

## More Documentation

- `README.md` - Full documentation
- `README-visualization.md` - Visualization architecture details
- `docs/` - Model specification and guides

