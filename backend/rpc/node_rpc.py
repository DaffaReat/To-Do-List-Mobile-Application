"""
Thin RPC layer — every function maps 1:1 to a webui.call() from the frontend.
All functions accept/return plain JSON-serializable strings.
Error responses are always: {"ok": false, "error": "<message>"}
"""
import json
from services import node_service as svc


def _ok(data) -> str:
    return json.dumps({"ok": True, "data": data})

def _err(msg) -> str:
    return json.dumps({"ok": False, "error": str(msg)})


def rpc_get_root_nodes(_) -> str:
    try:
        return _ok(svc.get_root_nodes())
    except Exception as e:
        return _err(e)

def rpc_get_children(payload: str) -> str:
    try:
        data = json.loads(payload)
        return _ok(svc.get_children(data.get("parent_id")))
    except Exception as e:
        return _err(e)

def rpc_get_node(payload: str) -> str:
    try:
        data = json.loads(payload)
        return _ok(svc.get_node(data["id"]))
    except Exception as e:
        return _err(e)

def rpc_create_node(payload: str) -> str:
    try:
        data = json.loads(payload)
        return _ok(svc.create_node(
            title=data["title"],
            parent_id=data.get("parent_id"),
            body=data.get("body", ""),
            state=data.get("state", "TODO"),
            scheduled=data.get("scheduled"),
            deadline=data.get("deadline"),
            repeater=data.get("repeater"),
        ))
    except Exception as e:
        return _err(e)

def rpc_update_node(payload: str) -> str:
    try:
        data = json.loads(payload)
        node_id = data.pop("id")
        return _ok(svc.update_node(node_id, **data))
    except Exception as e:
        return _err(e)

def rpc_delete_node(payload: str) -> str:
    try:
        data = json.loads(payload)
        return _ok(svc.delete_node(data["id"]))
    except Exception as e:
        return _err(e)

def rpc_move_node(payload: str) -> str:
    try:
        data = json.loads(payload)
        return _ok(svc.move_node(data["id"], data.get("new_parent_id")))
    except Exception as e:
        return _err(e)

def rpc_reorder_siblings(payload: str) -> str:
    try:
        data = json.loads(payload)
        return _ok(svc.reorder_siblings(data.get("parent_id"), data["ordered_ids"]))
    except Exception as e:
        return _err(e)
