import json
import os
from webui import webui

from database.schema import init_schema
from rpc.node_rpc import (
    rpc_get_root_nodes,
    rpc_get_children,
    rpc_get_node,
    rpc_create_node,
    rpc_update_node,
    rpc_delete_node,
    rpc_move_node,
    rpc_reorder_siblings,
)
from features.features import (
    search_nodes,
    get_agenda,
    process_repeater,
    export_subtree_to_markdown,
)


def _ok(data) -> str:
    return json.dumps({"ok": True, "data": data})

def _err(msg) -> str:
    return json.dumps({"ok": False, "error": str(msg)})

def _parse(e) -> dict:
    try:
        raw = e.get_string()
        return json.loads(raw) if raw and raw.strip() not in ('', 'None') else {}
    except:
        return {}


def rpc_search_nodes(e) -> None:
    try:
        data = _parse(e)
        nodes = search_nodes(data["query"])
        e.return_string(_ok([n.to_dict() for n in nodes]))
    except Exception as ex:
        e.return_string(_err(ex))

def rpc_get_agenda(e) -> None:
    try:
        data = _parse(e)
        nodes = get_agenda(data["start_date"], data["end_date"])
        e.return_string(_ok([n.to_dict() for n in nodes]))
    except Exception as ex:
        e.return_string(_err(ex))

def rpc_process_repeater(e) -> None:
    try:
        data = _parse(e)
        node = process_repeater(data["id"])
        e.return_string(_ok(node.to_dict() if node else None))
    except Exception as ex:
        e.return_string(_err(ex))

def rpc_export_markdown(e) -> None:
    try:
        data = _parse(e)
        md = export_subtree_to_markdown(data["id"])
        e.return_string(_ok({"markdown": md}))
    except Exception as ex:
        e.return_string(_err(ex))


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Org-Lite</title>
    <script src="webui.js"></script>
    <style>
        :root {
            --bg: #121212;
            --surface: #1e1e1e;
            --surface2: #2a2a2a;
            --text: #ffffff;
            --text-dim: #888888;
            --primary: #bb86fc;
            --secondary: #03dac6;
            --danger: #cf6679;
            --warn: #ffb74d;
            --border: #2a2a2a;
            --todo: #888888;
            --doing: #ffb74d;
            --done: #bb86fc;
        }

        * { box-sizing: border-box; }

        body {
            margin: 0;
            padding: 0;
            background: var(--bg);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            padding-bottom: 120px;
            overscroll-behavior: none;
        }

        header {
            padding: 14px 16px;
            font-size: 20px;
            font-weight: bold;
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            background: var(--bg);
            z-index: 100;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        header .header-left { display: flex; flex-direction: column; }
        header .breadcrumb { font-size: 12px; color: var(--text-dim); margin-top: 2px; }

        .back-btn {
            background: var(--surface2);
            border: none;
            color: var(--text);
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 13px;
            cursor: pointer;
        }

        /* BOTTOM NAV */
        .bottom-nav {
            position: fixed;
            bottom: 0; left: 0; right: 0;
            height: 60px;
            background: var(--surface);
            border-top: 1px solid var(--border);
            display: flex;
            z-index: 200;
        }

        .nav-btn {
            flex: 1;
            background: none;
            border: none;
            color: var(--text-dim);
            font-size: 11px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 3px;
            cursor: pointer;
        }

        .nav-btn.active { color: var(--primary); }
        .nav-btn .icon { font-size: 20px; }

        /* FAB */
        .fab {
            position: fixed;
            bottom: 76px; right: 20px;
            width: 56px; height: 56px;
            border-radius: 28px;
            background: var(--primary);
            color: #000;
            font-size: 28px;
            border: none;
            box-shadow: 0 4px 12px rgba(187,134,252,0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 150;
        }

        /* VIEWS */
        .view { display: none; }
        .view.active { display: block; }

        /* TREE */
        ul { list-style: none; padding: 0; margin: 0; }

        ul ul {
            padding-left: 20px;
            border-left: 1px solid var(--border);
            margin-left: 14px;
        }

        .node-row {
            display: flex;
            align-items: center;
            padding: 10px 12px;
            border-bottom: 1px solid var(--border);
            min-height: 52px;
            gap: 6px;
        }

        /* EXPAND BTN */
        .expand-btn {
            width: 24px;
            height: 44px;
            background: none;
            border: none;
            color: var(--text-dim);
            font-size: 11px;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            flex-shrink: 0;
        }

        .expand-btn.no-children { visibility: hidden; pointer-events: none; }

        /* STATE BADGE */
        .state-badge {
            font-size: 9px;
            font-weight: bold;
            padding: 3px 5px;
            border-radius: 4px;
            cursor: pointer;
            flex-shrink: 0;
            min-width: 52px;
            text-align: center;
            min-height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            user-select: none;
        }

        .state-TODO      { background: #2a2a2a; color: var(--todo);    border: 1px solid var(--todo); }
        .state-DOING     { background: #2a1f00; color: var(--doing);   border: 1px solid var(--doing); }
        .state-DONE      { background: #1e0f2e; color: var(--done);    border: 1px solid var(--done); }
        .state-CANCELLED { background: #2a0f14; color: var(--danger);  border: 1px solid var(--danger); }

        /* NODE CONTENT */
        .node-content { flex: 1; min-width: 0; cursor: pointer; }

        .node-title {
            font-size: 14px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .node-title.done      { text-decoration: line-through; color: var(--text-dim); }
        .node-title.cancelled { text-decoration: line-through; color: var(--danger); opacity: 0.6; }

        .node-meta {
            font-size: 11px;
            color: var(--text-dim);
            margin-top: 3px;
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }

        .meta-scheduled { color: var(--secondary); }
        .meta-deadline  { color: var(--warn); }
        .meta-deadline.overdue { color: var(--danger); font-weight: bold; }
        .meta-repeater  { color: var(--primary); }

        /* ROW ACTION BUTTONS */
        .row-actions {
            display: flex;
            gap: 4px;
            flex-shrink: 0;
        }

        .icon-btn {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            border: none;
            background: var(--surface2);
            color: var(--text-dim);
            font-size: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            flex-shrink: 0;
        }

        .icon-btn.danger { background: #2a0f14; color: var(--danger); }
        .icon-btn.edit-btn { background: #1a1a2e; color: var(--primary); }

        /* SORT BAR */
        .sort-bar {
            display: flex;
            align-items: center;
            padding: 8px 16px;
            gap: 8px;
            border-bottom: 1px solid var(--border);
            font-size: 12px;
            color: var(--text-dim);
        }

        .sort-chip {
            padding: 4px 10px;
            border-radius: 12px;
            border: 1px solid var(--border);
            background: none;
            color: var(--text-dim);
            font-size: 11px;
            cursor: pointer;
        }

        .sort-chip.active { border-color: var(--primary); color: var(--primary); background: #1e0f2e; }

        /* EMPTY STATE */
        .empty-state {
            padding: 60px 16px;
            text-align: center;
            color: var(--text-dim);
            font-size: 15px;
            line-height: 1.6;
        }

        /* SEARCH */
        .search-bar {
            padding: 12px 16px;
            position: sticky;
            top: 57px;
            background: var(--bg);
            z-index: 99;
            border-bottom: 1px solid var(--border);
        }

        .search-bar input {
            width: 100%;
            padding: 10px 14px;
            border-radius: 10px;
            border: 1px solid var(--border);
            background: var(--surface);
            color: var(--text);
            font-size: 15px;
            outline: none;
        }

        /* AGENDA */
        .agenda-date-header {
            padding: 8px 16px;
            font-size: 11px;
            font-weight: bold;
            color: var(--primary);
            background: var(--surface);
            border-bottom: 1px solid var(--border);
            letter-spacing: 0.8px;
            text-transform: uppercase;
        }

        .agenda-node-row {
            display: flex;
            align-items: flex-start;
            padding: 12px 16px;
            border-bottom: 1px solid var(--border);
            gap: 10px;
            min-height: 52px;
        }

        /* MODAL */
        .modal-overlay {
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.75);
            z-index: 300;
            align-items: flex-end;
        }

        .modal-overlay.open { display: flex; }

        .modal-sheet {
            background: var(--surface);
            border-radius: 16px 16px 0 0;
            padding: 20px 16px 40px;
            width: 100%;
            max-height: 85vh;
            overflow-y: auto;
        }

        .modal-title {
            font-size: 17px;
            font-weight: bold;
            margin-bottom: 16px;
        }

        .modal-input {
            width: 100%;
            padding: 12px;
            border-radius: 10px;
            border: 1px solid var(--border);
            background: var(--surface2);
            color: var(--text);
            font-size: 15px;
            outline: none;
            margin-bottom: 10px;
        }

        .modal-row { display: flex; gap: 8px; margin-bottom: 10px; }
        .modal-row label { font-size: 12px; color: var(--text-dim); display: block; margin-bottom: 4px; }
        .modal-row .field { flex: 1; }

        .modal-actions { display: flex; gap: 8px; margin-top: 16px; }

        .btn {
            flex: 1; padding: 14px;
            border-radius: 10px; border: none;
            font-size: 15px; font-weight: bold; cursor: pointer;
        }

        .btn-primary { background: var(--primary); color: #000; }
        .btn-ghost   { background: var(--surface2); color: var(--text); }
        .btn-danger  { background: var(--danger); color: #fff; }
    </style>
</head>
<body>

<header>
    <div class="header-left">
        <div id="header-title">My Tasks</div>
        <div class="breadcrumb" id="breadcrumb"></div>
    </div>
    <button class="back-btn" onclick="goBack()" id="back-btn" hidden>&#8592; Back</button>
</header>

<!-- VIEWS -->
<div id="view-tasks" class="view active">
    <div class="sort-bar">
        <span>Sort:</span>
        <button class="sort-chip" id="sort-default" onclick="setSort('default')">Default</button>
        <button class="sort-chip active" id="sort-deadline" onclick="setSort('deadline')">&#9888; Deadline</button>
        <button class="sort-chip" id="sort-state" onclick="setSort('state')">State</button>
    </div>
    <ul id="tree-root"></ul>
    <div id="empty-tasks" class="empty-state" style="display:none;">No tasks yet.<br>Tap + to add one!</div>
</div>

<div id="view-agenda" class="view">
    <div id="agenda-list"></div>
    <div id="empty-agenda" class="empty-state" style="display:none;">No tasks scheduled today.</div>
</div>

<div id="view-search" class="view">
    <div class="search-bar">
        <input type="text" id="search-input" placeholder="Search tasks..." oninput="onSearch(this.value)">
    </div>
    <ul id="search-results"></ul>
    <div id="empty-search" class="empty-state" style="display:none;">No results found.</div>
</div>

<!-- FAB -->
<button class="fab" onclick="openCreateModal()" id="fab">+</button>

<!-- BOTTOM NAV -->
<nav class="bottom-nav">
    <button class="nav-btn active" id="nav-tasks" onclick="switchView('tasks')">
        <span class="icon">&#9776;</span>Tasks
    </button>
    <button class="nav-btn" id="nav-agenda" onclick="switchView('agenda')">
        <span class="icon">&#128197;</span>Agenda
    </button>
    <button class="nav-btn" id="nav-search" onclick="switchView('search')">
        <span class="icon">&#128269;</span>Search
    </button>
</nav>

<!-- CREATE/EDIT MODAL -->
<div class="modal-overlay" id="modal" onclick="closeModal(event)">
    <div class="modal-sheet">
        <div class="modal-title" id="modal-title">New Task</div>
        <input class="modal-input" id="modal-title-input" placeholder="Task title..." type="text">
        <textarea class="modal-input" id="modal-body-input" placeholder="Notes (optional)..." rows="3" style="resize:none;font-family:inherit;"></textarea>
        <div class="modal-row">
            <div class="field">
                <label>Scheduled</label>
                <input class="modal-input" id="modal-scheduled" type="date" style="margin:0;">
            </div>
            <div class="field">
                <label>Deadline</label>
                <input class="modal-input" id="modal-deadline" type="date" style="margin:0;">
            </div>
        </div>
        <div class="modal-row">
            <div class="field">
                <label>Repeater (e.g. +1w)</label>
                <input class="modal-input" id="modal-repeater" placeholder="+1d / +2w / +1m" style="margin:0;">
            </div>
        </div>
        <div class="modal-actions">
            <button class="btn btn-ghost" onclick="closeModal()">Cancel</button>
            <button class="btn btn-primary" id="modal-save-btn" onclick="saveModal()">Save</button>
        </div>
    </div>
</div>

<!-- DELETE CONFIRM MODAL -->
<div class="modal-overlay" id="delete-modal" onclick="closeDeleteModal(event)">
    <div class="modal-sheet">
        <div class="modal-title">Delete Task?</div>
        <p style="color:var(--text-dim);font-size:14px;margin-top:0;">This will also delete all subtasks. This cannot be undone.</p>
        <div class="modal-actions">
            <button class="btn btn-ghost" onclick="closeDeleteModal()">Cancel</button>
            <button class="btn btn-danger" onclick="confirmDelete()">Delete</button>
        </div>
    </div>
</div>

<script>
// ── STATE ──────────────────────────────────────────────────────────────────
let currentView = 'tasks';
let currentParentId = null;
let parentStack = [];
let modalMode = 'create';
let modalNodeId = null;
let deleteNodeId = null;
let searchDebounce = null;
let currentSort = 'deadline';
let cachedNodes = [];

const STATE_CYCLE = ['TODO', 'DOING', 'DONE', 'CANCELLED'];
const STATE_ORDER = { 'TODO': 0, 'DOING': 1, 'DONE': 2, 'CANCELLED': 3 };

// ── API ────────────────────────────────────────────────────────────────────
async function callPython(func, payload = {}) {
    const resStr = await webui.call(func, JSON.stringify(payload));
    const res = JSON.parse(resStr);
    if (!res.ok) throw new Error(res.error);
    return res.data;
}

// ── SORT ───────────────────────────────────────────────────────────────────
function setSort(mode) {
    currentSort = mode;
    document.querySelectorAll('.sort-chip').forEach(c => c.classList.remove('active'));
    document.getElementById('sort-' + mode).classList.add('active');
    renderNodes(cachedNodes);
}

function sortNodes(nodes) {
    const sorted = [...nodes];
    const FAR = '9999-99-99';

    if (currentSort === 'deadline') {
        sorted.sort((a, b) => {
            const da = a.deadline || FAR;
            const db = b.deadline || FAR;
            return da < db ? -1 : da > db ? 1 : 0;
        });
    } else if (currentSort === 'state') {
        sorted.sort((a, b) => STATE_ORDER[a.state] - STATE_ORDER[b.state]);
    } else {
        // default: by position
        sorted.sort((a, b) => a.position - b.position);
    }
    return sorted;
}

// ── VIEW SWITCHING ─────────────────────────────────────────────────────────
function switchView(view) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('view-' + view).classList.add('active');
    document.getElementById('nav-' + view).classList.add('active');
    currentView = view;
    document.getElementById('fab').style.display = view === 'tasks' ? 'flex' : 'none';
    if (view === 'agenda') loadAgenda();
}

// ── NAVIGATION ─────────────────────────────────────────────────────────────
function goBack() {
    if (parentStack.length === 0) return;
    parentStack.pop();
    const prev = parentStack.length > 0 ? parentStack[parentStack.length - 1] : null;
    currentParentId = prev ? prev.id : null;
    updateHeader();
    loadTasks();
}

function drillInto(nodeId, nodeTitle) {
    parentStack.push({ id: nodeId, title: nodeTitle });
    currentParentId = nodeId;
    updateHeader();
    loadTasks();
}

function updateHeader() {
    const title = document.getElementById('header-title');
    const breadcrumb = document.getElementById('breadcrumb');
    const backBtn = document.getElementById('back-btn');
    if (parentStack.length === 0) {
        title.textContent = 'My Tasks';
        breadcrumb.textContent = '';
        backBtn.hidden = true;
    } else {
        title.textContent = parentStack[parentStack.length - 1].title;
        breadcrumb.textContent = ['Root', ...parentStack.slice(0, -1).map(p => p.title)].join(' › ');
        backBtn.hidden = false;
    }
}

// ── LOAD & RENDER ──────────────────────────────────────────────────────────
async function loadTasks() {
    try {
        const nodes = await callPython('get_children', { parent_id: currentParentId });
        cachedNodes = nodes;
        renderNodes(nodes);
    } catch (err) {
        console.error('loadTasks error:', err);
    }
}

function renderNodes(nodes) {
    const root = document.getElementById('tree-root');
    root.innerHTML = '';
    const sorted = sortNodes(nodes);
    sorted.forEach(node => root.appendChild(createNodeElement(node)));
    document.getElementById('empty-tasks').style.display = sorted.length === 0 ? 'block' : 'none';
}

// ── NODE ELEMENT ───────────────────────────────────────────────────────────
function createNodeElement(node) {
    const today = new Date().toISOString().slice(0, 10);

    const li = document.createElement('li');
    li.id = 'node-' + node.id;

    const row = document.createElement('div');
    row.className = 'node-row';

    // Expand btn
    const expandBtn = document.createElement('button');
    expandBtn.className = 'expand-btn no-children';
    expandBtn.innerHTML = '&#9658;';

    // State badge (tap to cycle)
    const stateBadge = document.createElement('div');
    stateBadge.className = 'state-badge state-' + node.state;
    stateBadge.textContent = node.state;

    // Content area (tap to drill in)
    const content = document.createElement('div');
    content.className = 'node-content';

    const titleEl = document.createElement('div');
    titleEl.className = 'node-title' +
        (node.state === 'DONE' ? ' done' : node.state === 'CANCELLED' ? ' cancelled' : '');
    titleEl.textContent = node.title;

    const metaEl = document.createElement('div');
    metaEl.className = 'node-meta';
    if (node.scheduled) {
        metaEl.innerHTML += '<span class="meta-scheduled">&#128197; ' + node.scheduled.slice(0,10) + '</span>';
    }
    if (node.deadline) {
        const overdue = node.deadline.slice(0,10) < today && node.state !== 'DONE' && node.state !== 'CANCELLED';
        metaEl.innerHTML += '<span class="meta-deadline' + (overdue ? ' overdue' : '') + '">&#9888; ' + node.deadline.slice(0,10) + (overdue ? ' OVERDUE' : '') + '</span>';
    }
    if (node.repeater) {
        metaEl.innerHTML += '<span class="meta-repeater">&#8635; ' + node.repeater + '</span>';
    }

    content.appendChild(titleEl);
    if (node.scheduled || node.deadline || node.repeater) content.appendChild(metaEl);

    // Row action buttons: edit + delete
    const rowActions = document.createElement('div');
    rowActions.className = 'row-actions';

    const editBtn = document.createElement('button');
    editBtn.className = 'icon-btn edit-btn';
    editBtn.innerHTML = '&#9998;';
    editBtn.title = 'Edit';
    editBtn.onclick = (e) => { e.stopPropagation(); openEditModal(node); };

    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'icon-btn danger';
    deleteBtn.innerHTML = '&#128465;';
    deleteBtn.title = 'Delete';
    deleteBtn.onclick = (e) => { e.stopPropagation(); openDeleteModal(node.id); };

    rowActions.appendChild(editBtn);
    rowActions.appendChild(deleteBtn);

    // Children container
    const childrenContainer = document.createElement('ul');
    childrenContainer.style.display = 'none';

    // Check for children async
    setTimeout(async () => {
        try {
            const children = await callPython('get_children', { parent_id: node.id });
            if (children.length > 0) {
                expandBtn.classList.remove('no-children');
                sortNodes(children).forEach(c => childrenContainer.appendChild(createNodeElement(c)));
            }
        } catch {}
    }, 0);

    // Expand/collapse
    expandBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const open = childrenContainer.style.display === 'block';
        childrenContainer.style.display = open ? 'none' : 'block';
        expandBtn.innerHTML = open ? '&#9658;' : '&#9660;';
    });

    // Cycle state on badge tap
    stateBadge.addEventListener('click', async (e) => {
        e.stopPropagation();
        const idx = STATE_CYCLE.indexOf(node.state);
        const newState = STATE_CYCLE[(idx + 1) % STATE_CYCLE.length];
        const oldState = node.state;
        node.state = newState;

        stateBadge.className = 'state-badge state-' + newState;
        stateBadge.textContent = newState;
        titleEl.className = 'node-title' + (newState === 'DONE' ? ' done' : newState === 'CANCELLED' ? ' cancelled' : '');

        try {
            await callPython('update_node', { id: node.id, state: newState });
            if (newState === 'DONE' && node.repeater) {
                const updated = await callPython('process_repeater', { id: node.id });
                if (updated) {
                    node.state = updated.state;
                    stateBadge.className = 'state-badge state-' + updated.state;
                    stateBadge.textContent = updated.state;
                    titleEl.className = 'node-title';
                }
            }
        } catch {
            node.state = oldState;
            stateBadge.className = 'state-badge state-' + oldState;
            stateBadge.textContent = oldState;
            titleEl.className = 'node-title' + (oldState === 'DONE' ? ' done' : oldState === 'CANCELLED' ? ' cancelled' : '');
        }
    });

    // Long press to edit
    let pressTimer = null;
    row.addEventListener('touchstart', () => { pressTimer = setTimeout(() => openEditModal(node), 600); });
    row.addEventListener('touchend',   () => clearTimeout(pressTimer));
    row.addEventListener('touchmove',  () => clearTimeout(pressTimer));

    // Tap content to drill in
    content.addEventListener('click', () => drillInto(node.id, node.title));

    row.appendChild(expandBtn);
    row.appendChild(stateBadge);
    row.appendChild(content);
    row.appendChild(rowActions);

    li.appendChild(row);
    li.appendChild(childrenContainer);
    return li;
}

// ── AGENDA ─────────────────────────────────────────────────────────────────
async function loadAgenda() {
    const list = document.getElementById('agenda-list');
    list.innerHTML = '';
    const today = new Date().toISOString().slice(0, 10);
    try {
        const nodes = await callPython('get_agenda', { start_date: today, end_date: today });
        document.getElementById('empty-agenda').style.display = nodes.length === 0 ? 'block' : 'none';

        const header = document.createElement('div');
        header.className = 'agenda-date-header';
        header.textContent = 'Today — ' + today;
        list.appendChild(header);

        nodes.forEach(node => {
            const row = document.createElement('div');
            row.className = 'agenda-node-row';

            const badge = document.createElement('div');
            badge.className = 'state-badge state-' + node.state;
            badge.textContent = node.state;

            const content = document.createElement('div');
            content.className = 'node-content';
            content.innerHTML = '<div class="node-title">' + escapeHtml(node.title) + '</div>';

            const meta = document.createElement('div');
            meta.className = 'node-meta';
            if (node.scheduled) meta.innerHTML += '<span class="meta-scheduled">&#128197; ' + node.scheduled.slice(0,10) + '</span>';
            if (node.deadline)  meta.innerHTML += '<span class="meta-deadline">&#9888; ' + node.deadline.slice(0,10) + '</span>';
            content.appendChild(meta);

            row.appendChild(badge);
            row.appendChild(content);
            list.appendChild(row);
        });
    } catch (err) {
        console.error('agenda error:', err);
    }
}

// ── SEARCH ─────────────────────────────────────────────────────────────────
function onSearch(query) {
    clearTimeout(searchDebounce);
    const list = document.getElementById('search-results');
    const empty = document.getElementById('empty-search');
    if (!query.trim()) {
        list.innerHTML = '';
        empty.style.display = 'none';
        return;
    }
    searchDebounce = setTimeout(async () => {
        try {
            const nodes = await callPython('search_nodes', { query: query.trim() });
            list.innerHTML = '';
            empty.style.display = nodes.length === 0 ? 'block' : 'none';
            sortNodes(nodes).forEach(node => list.appendChild(createNodeElement(node)));
        } catch (err) {
            console.error('search error:', err);
        }
    }, 300);
}

// ── CREATE/EDIT MODAL ──────────────────────────────────────────────────────
function openCreateModal() {
    modalMode = 'create';
    modalNodeId = null;
    document.getElementById('modal-title').textContent = 'New Task';
    document.getElementById('modal-title-input').value = '';
    document.getElementById('modal-body-input').value = '';
    document.getElementById('modal-scheduled').value = '';
    document.getElementById('modal-deadline').value = '';
    document.getElementById('modal-repeater').value = '';
    document.getElementById('modal-save-btn').textContent = 'Create';
    document.getElementById('modal').classList.add('open');
    setTimeout(() => document.getElementById('modal-title-input').focus(), 100);
}

function openEditModal(node) {
    modalMode = 'edit';
    modalNodeId = node.id;
    document.getElementById('modal-title').textContent = 'Edit Task';
    document.getElementById('modal-title-input').value = node.title;
    document.getElementById('modal-body-input').value = node.body || '';
    document.getElementById('modal-scheduled').value = node.scheduled ? node.scheduled.slice(0,10) : '';
    document.getElementById('modal-deadline').value = node.deadline ? node.deadline.slice(0,10) : '';
    document.getElementById('modal-repeater').value = node.repeater || '';
    document.getElementById('modal-save-btn').textContent = 'Save';
    document.getElementById('modal').classList.add('open');
}

function closeModal(event) {
    if (event && event.target !== document.getElementById('modal')) return;
    document.getElementById('modal').classList.remove('open');
}

async function saveModal() {
    const title = document.getElementById('modal-title-input').value.trim();
    if (!title) return;

    const payload = {
        title,
        body:      document.getElementById('modal-body-input').value.trim(),
        scheduled: document.getElementById('modal-scheduled').value || null,
        deadline:  document.getElementById('modal-deadline').value || null,
        repeater:  document.getElementById('modal-repeater').value.trim() || null,
    };

    try {
        if (modalMode === 'create') {
            payload.parent_id = currentParentId;
            const newNode = await callPython('create_node', payload);
            cachedNodes.push(newNode);
            renderNodes(cachedNodes);
        } else {
            payload.id = modalNodeId;
            await callPython('update_node', payload);
            // Refresh full list to reflect updated sort order
            await loadTasks();
        }
        document.getElementById('modal').classList.remove('open');
    } catch (err) {
        alert('Failed to save: ' + err.message);
    }
}

// ── DELETE MODAL ───────────────────────────────────────────────────────────
function openDeleteModal(nodeId) {
    deleteNodeId = nodeId;
    document.getElementById('delete-modal').classList.add('open');
}

function closeDeleteModal(event) {
    if (event && event.target !== document.getElementById('delete-modal')) return;
    document.getElementById('delete-modal').classList.remove('open');
}

async function confirmDelete() {
    if (!deleteNodeId) return;
    try {
        await callPython('delete_node', { id: deleteNodeId });
        cachedNodes = cachedNodes.filter(n => n.id !== deleteNodeId);
        renderNodes(cachedNodes);
        document.getElementById('delete-modal').classList.remove('open');
    } catch (err) {
        alert('Failed to delete: ' + err.message);
    }
}

// ── UTILS ──────────────────────────────────────────────────────────────────
function escapeHtml(text) {
    return text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ── BOOT ───────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(loadTasks, 100);
});
</script>
</body>
</html>"""


def main():
    init_schema()

    window = webui.Window()

    window.bind("get_root_nodes",   rpc_get_root_nodes)
    window.bind("get_children",     rpc_get_children)
    window.bind("get_node",         rpc_get_node)
    window.bind("create_node",      rpc_create_node)
    window.bind("update_node",      rpc_update_node)
    window.bind("delete_node",      rpc_delete_node)
    window.bind("move_node",        rpc_move_node)
    window.bind("reorder_siblings", rpc_reorder_siblings)

    window.bind("search_nodes",     rpc_search_nodes)
    window.bind("get_agenda",       rpc_get_agenda)
    window.bind("process_repeater", rpc_process_repeater)
    window.bind("export_markdown",  rpc_export_markdown)

    window.show(HTML)
    webui.wait()


if __name__ == "__main__":
    main()