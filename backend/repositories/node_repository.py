from database.connection import db
from models.node import Node, row_to_node
from typing import Optional


# ── CREATE ────────────────────────────────────────────────────────────────────

def create_node(
    title: str,
    parent_id: Optional[int] = None,
    body: str = "",
    state: str = "TODO",
    scheduled: Optional[str] = None,
    deadline: Optional[str] = None,
    repeater: Optional[str] = None,
) -> Node:
    conn = db()
    cur = conn.execute(
        "SELECT COALESCE(MAX(position), -1) + 1 FROM nodes WHERE parent_id IS ?",
        (parent_id,)
    )
    position = cur.fetchone()[0]

    cur = conn.execute(
        """INSERT INTO nodes (parent_id, title, body, state, position, scheduled, deadline, repeater)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (parent_id, title, body, state, position, scheduled, deadline, repeater)
    )
    conn.commit()
    return get_node_by_id(cur.lastrowid)


# ── READ ──────────────────────────────────────────────────────────────────────

def get_node_by_id(node_id: int) -> Optional[Node]:
    row = db().execute(
        "SELECT * FROM nodes WHERE id = ?", (node_id,)
    ).fetchone()
    return row_to_node(row) if row else None

def get_children(parent_id: Optional[int]) -> list[Node]:
    """Immediate children only — for lazy loading in the frontend."""
    rows = db().execute(
        "SELECT * FROM nodes WHERE parent_id IS ? ORDER BY position ASC",
        (parent_id,)
    ).fetchall()
    return [row_to_node(r) for r in rows]

def get_root_nodes() -> list[Node]:
    """Top-level nodes (parent_id IS NULL)."""
    return get_children(None)

def get_subtree_ids(node_id: int) -> list[int]:
    """
    Returns node_id + all descendant IDs via recursive CTE.
    Used for cascade delete and reparenting cycle-check.
    """
    rows = db().execute("""
        WITH RECURSIVE subtree(id) AS (
            SELECT id FROM nodes WHERE id = ?
            UNION ALL
            SELECT n.id FROM nodes n
            INNER JOIN subtree s ON n.parent_id = s.id
        )
        SELECT id FROM subtree
    """, (node_id,)).fetchall()
    return [r["id"] for r in rows]

def get_subtree(node_id: int) -> list[Node]:
    """Full subtree as flat list — for export or bulk ops."""
    ids = get_subtree_ids(node_id)
    if not ids:
        return []
    placeholders = ",".join("?" * len(ids))
    rows = db().execute(
        f"SELECT * FROM nodes WHERE id IN ({placeholders}) ORDER BY parent_id, position",
        ids
    ).fetchall()
    return [row_to_node(r) for r in rows]


# ── UPDATE ────────────────────────────────────────────────────────────────────

def update_node(
    node_id: int,
    title: Optional[str] = None,
    body: Optional[str] = None,
    state: Optional[str] = None,
    scheduled: Optional[str] = None,
    deadline: Optional[str] = None,
    repeater: Optional[str] = None,
) -> Optional[Node]:
    fields, values = [], []
    if title     is not None: fields.append("title = ?");     values.append(title)
    if body      is not None: fields.append("body = ?");      values.append(body)
    if state     is not None: fields.append("state = ?");     values.append(state)
    if scheduled is not None: fields.append("scheduled = ?"); values.append(scheduled)
    if deadline  is not None: fields.append("deadline = ?");  values.append(deadline)
    if repeater  is not None: fields.append("repeater = ?");  values.append(repeater)

    if not fields:
        return get_node_by_id(node_id)

    values.append(node_id)
    db().execute(
        f"UPDATE nodes SET {', '.join(fields)} WHERE id = ?", values
    )
    db().commit()
    return get_node_by_id(node_id)

def reparent_node(node_id: int, new_parent_id: Optional[int]) -> Optional[Node]:
    """Move node to a new parent. Position resets to end of new parent's children."""
    cur = db().execute(
        "SELECT COALESCE(MAX(position), -1) + 1 FROM nodes WHERE parent_id IS ?",
        (new_parent_id,)
    )
    new_position = cur.fetchone()[0]
    db().execute(
        "UPDATE nodes SET parent_id = ?, position = ? WHERE id = ?",
        (new_parent_id, new_position, node_id)
    )
    db().commit()
    return get_node_by_id(node_id)

def reorder_siblings(parent_id: Optional[int], ordered_ids: list[int]):
    """Reassign position values for siblings after a drag-reorder."""
    conn = db()
    for i, node_id in enumerate(ordered_ids):
        conn.execute(
            "UPDATE nodes SET position = ? WHERE id = ? AND parent_id IS ?",
            (i, node_id, parent_id)
        )
    conn.commit()


# ── DELETE ────────────────────────────────────────────────────────────────────

def delete_node_by_id(node_id: int):
    """Delete a single node row. FTS cleanup handled by trigger."""
    db().execute("DELETE FROM nodes WHERE id = ?", (node_id,))
    db().commit()

def cascade_delete_node(node_id: int) -> list[int]:
    """
    Delete a node and ALL its descendants atomically.
    Returns the list of deleted IDs so the frontend can clean up its state.
    """
    ids = get_subtree_ids(node_id)
    if not ids:
        return []

    conn = db()
    placeholders = ",".join("?" * len(ids))
    conn.execute(f"DELETE FROM nodes WHERE id IN ({placeholders})", ids)
    conn.commit()
    return ids
