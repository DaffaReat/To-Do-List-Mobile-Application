# To-Do-List-Mobile-Application

A hierarchical task management app built with Python + SQLite backend,
served via WebUI2 to an HTML/JS frontend embedded directly in main.py.

---

## Stack
- **Backend:** Python 3.10+
- **Database:** SQLite3 with FTS5 extension
- **Bridge:** WebUI2 (webui2 v2.5.7)
- **Frontend:** Single-file HTML/CSS/JS embedded in main.py

---

## Setup & Run

### 1. Install dependency
```bash
pip install webui2
```

### 2. Run
```bash
cd backend
python main.py
```

That's it. The app opens in a browser window automatically.
The database file `outliner.db` is created in `backend/` on first run.

---

## Code Pipeline
```
main.py
│
├── init_schema()
│   └── database/schema.py        Creates nodes table, FTS5 virtual table,
│                                  and sync triggers on first run
│
├── webui.Window()                 Opens the WebUI window
│
├── window.bind("fn", handler)     Registers Python functions as RPC endpoints
│   ├── rpc/node_rpc.py            CRUD + tree handlers (Daffa)
│   └── main.py (inline)          Features handlers: search, agenda, repeater, export
│
└── window.show(HTML)              Serves the HTML string directly into the WebView
    └── frontend HTML/JS
        └── webui.call("fn", JSON) Calls Python RPC from JavaScript
```

### Request Flow (JS → Python → DB → JS)
```
User taps "+" in UI
  → JS calls webui.call('create_node', JSON)
    → main.py receives event
      → node_rpc.py: rpc_create_node(e)
        → e.get_string() extracts JSON payload
          → node_service.py: create_node(...)
            → node_repository.py: INSERT INTO nodes
              → returns Node dataclass
          → serialized to dict → JSON string
        → e.return_string(result)
    → JS receives {"ok": true, "data": {...}}
  → UI re-renders with new node
```

### File Responsibilities

| File | Owner | Responsibility |
|---|---|---|
| `main.py` | Daffa | Entry point, RPC registration, HTML embedding |
| `database/connection.py` | Daffa | SQLite connection, WAL mode, pragmas |
| `database/schema.py` | Daffa | Table creation, FTS5, triggers |
| `models/node.py` | Daffa | Node dataclass, row_to_node converter |
| `repositories/node_repository.py` | Daffa | Raw SQL: CRUD, tree, cascade delete |
| `services/node_service.py` | Daffa | Business logic, validation, cycle-check |
| `rpc/node_rpc.py` | Daffa | RPC handlers: parse event, call service, return JSON |
| `features/features.py` | Teammate | FTS5 search, agenda queries, repeater logic, export |

---

## To Reset the Database
Delete `backend/outliner.db` and restart.