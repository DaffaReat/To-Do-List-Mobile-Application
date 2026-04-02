import re
from datetime import datetime, timedelta
from typing import Optional, List

from database.connection import db
from models.node import Node, row_to_node
from repositories.node_repository import get_node_by_id, update_node, get_subtree


# ── 1. FTS5 SEARCH ────────────────────────────────────────────────────────────

def search_nodes(query: str) -> List[Node]:
    """
    Perform a full-text search across node titles and bodies using FTS5.
    Results are ordered by relevance (rank).
    """
    # SQLite FTS5 uses a special MATCH operator. We join back to the main 
    # table to get the full node data.
    sql = """
        SELECT n.* FROM nodes n
        JOIN nodes_fts f ON n.id = f.rowid
        WHERE nodes_fts MATCH ?
        ORDER BY rank
    """
    rows = db().execute(sql, (query,)).fetchall()
    return [row_to_node(r) for r in rows]


# ── 2. AGENDA QUERIES ─────────────────────────────────────────────────────────

def get_agenda(start_date: str, end_date: str) -> List[Node]:
    """
    Fetch nodes that are scheduled or have a deadline within a specific date range.
    Expects ISO-8601 date strings (e.g., '2026-04-01').
    """
    sql = """
        SELECT * FROM nodes 
        WHERE (scheduled BETWEEN ? AND ?) 
           OR (deadline BETWEEN ? AND ?)
        ORDER BY COALESCE(scheduled, deadline) ASC
    """
    rows = db().execute(sql, (start_date, end_date, start_date, end_date)).fetchall()
    return [row_to_node(r) for r in rows]


# ── 3. REPEATER LOGIC ─────────────────────────────────────────────────────────

def process_repeater(node_id: int) -> Optional[Node]:
    """
    Advances the scheduled/deadline dates based on the repeater interval 
    (e.g., '+1d', '+2w') and resets the state to 'TODO'.
    """
    node = get_node_by_id(node_id)
    if not node or not node.repeater or node.state != 'DONE':
        return node

    # Parse repeater string like "+1d", "+2w", "+1m", "+1y"
    match = re.match(r'\+(\d+)([dwmy])', node.repeater.strip().lower())
    if not match:
        return node

    amount = int(match.group(1))
    unit = match.group(2)

    def advance_date(date_str: Optional[str]) -> Optional[str]:
        if not date_str:
            return None
        
        # Parse the date (assuming format YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
        fmt = "%Y-%m-%dT%H:%M:%SZ" if "T" in date_str else "%Y-%m-%d"
        try:
            dt = datetime.strptime(date_str[:19] + ("Z" if "Z" in date_str else ""), fmt)
        except ValueError:
            dt = datetime.strptime(date_str[:10], "%Y-%m-%d")

        # Advance based on unit
        if unit == 'd':
            dt += timedelta(days=amount)
        elif unit == 'w':
            dt += timedelta(weeks=amount)
        elif unit == 'm':
            dt += timedelta(days=amount * 30) # Approximation for months
        elif unit == 'y':
            dt += timedelta(days=amount * 365) # Approximation for years
            
        return dt.strftime(fmt)

    new_scheduled = advance_date(node.scheduled)
    new_deadline = advance_date(node.deadline)

    # Update the node: reset to TODO and apply new dates
    return update_node(
        node_id=node.id, 
        state='TODO', 
        scheduled=new_scheduled, 
        deadline=new_deadline
    )


# ── 4. EXPORT ─────────────────────────────────────────────────────────────────

def export_subtree_to_markdown(node_id: int) -> str:
    """
    Exports a node and all of its descendants into a formatted Markdown list.
    """
    nodes = get_subtree(node_id)
    if not nodes:
        return ""

    # Group nodes by parent_id for easy traversal
    children_map = {}
    for n in nodes:
        children_map.setdefault(n.parent_id, []).append(n)

    lines = []

    def build_markdown(current_node: Node, depth: int):
        indent = "  " * depth
        checkbox = "[x]" if current_node.state == "DONE" else "[ ]"
        
        # Format the main node line
        line = f"{indent}- {checkbox} **{current_node.title}**"
        
        # Append metadata if it exists
        meta = []
        if current_node.scheduled: meta.append(f"📅 {current_node.scheduled}")
        if current_node.deadline: meta.append(f"🚨 {current_node.deadline}")
        if current_node.repeater: meta.append(f"🔁 {current_node.repeater}")
        if meta:
            line += f" ({', '.join(meta)})"
            
        lines.append(line)

        # Append body text if it exists
        if current_node.body:
            body_indent = "  " * (depth + 1)
            for body_line in current_node.body.split('\n'):
                lines.append(f"{body_indent}> {body_line}")

        # Recursively process children
        children = children_map.get(current_node.id, [])
        # Sort by position to maintain the user's custom order
        children.sort(key=lambda x: x.position) 
        for child in children:
            build_markdown(child, depth + 1)

    # The first node in get_subtree is the root we requested
    root_node = next(n for n in nodes if n.id == node_id)
    build_markdown(root_node, 0)

    return "\n".join(lines)