# Outliner App — Setup & Run Guide

## Folder Structure
```
project/
├── backend/
│   ├── main.py
│   ├── database/
│   ├── models/
│   ├── repositories/
│   ├── services/
│   ├── rpc/
│   └── features/
└── frontend/
    └── index.html
```

## Step 1 — Make sure you have Python 3.10+
```bash
python --version
```

## Step 2 — Create a virtual environment
```bash
cd backend
python -m venv venv
```

## Step 3 — Activate it

Windows:
```bash
venv\Scripts\activate
```

Mac/Linux:
```bash
source venv/bin/activate
```

## Step 4 — Install dependencies
```bash
pip install webui2
```

## Step 5 — Run the app
```bash
python main.py
```

That's it. The app opens automatically. The database file `outliner.db` is created in the `backend/` folder on first run.

---

## To reset the database

Just delete `backend/outliner.db` and restart.