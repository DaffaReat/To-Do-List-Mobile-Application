import json
from services import node_service as svc


def _ok(data) -> str:
    return json.dumps({"ok": True, "data": data})

def _err(msg) -> str:
    return json.dumps({"ok": False, "error": str(msg)})

def _parse(e) -> dict:
    try:
        raw = str(e.data)
        return json.loads(raw) if raw and raw.strip() not in ('', 'None') else {}
    except:
        return {}


def rpc_get_root_nodes(e) -> str:
    try:
        return _ok(svc.get_root_nodes())
    except Exception as ex:
        return _err(ex)

def rpc_get_children(e) -> str:
    try:
        data = _parse(e)
        return _ok(svc.get_children(data.get("parent_id")))
    except Exception as ex:
        return _err(ex)

def rpc_get_node(e) -> str:
    try:
        data = _parse(e)
        return _ok(svc.get_node(data["id"]))
    except Exception as ex:
        return _err(ex)

def rpc_create_node(e) -> str:
    try:
        data = _parse(e)
        return _ok(svc.create_node(
            title=data["title"],
            parent_id=data.get("parent_id"),
            body=data.get("body", ""),
            state=data.get("state", "TODO"),
            scheduled=data.get("scheduled"),
            deadline=data.get("deadline"),
            repeater=data.get("repeater"),
        ))
    except Exception as ex:
        return _err(ex)

def rpc_update_node(e) -> str:
    try:
        data = _parse(e)
        node_id = data.pop("id")
        return _ok(svc.update_node(node_id, **data))
    except Exception as ex:
        return _err(ex)

def rpc_delete_node(e) -> str:
    try:
        data = _parse(e)
        return _ok(svc.delete_node(data["id"]))
    except Exception as ex:
        return _err(ex)

def rpc_move_node(e) -> str:
    try:
        data = _parse(e)
        return _ok(svc.move_node(data["id"], data.get("new_parent_id")))
    except Exception as ex:
        return _err(ex)

def rpc_reorder_siblings(e) -> str:
    try:
        data = _parse(e)
        return _ok(svc.reorder_siblings(data.get("parent_id"), data["ordered_ids"]))
    except Exception as ex:
        return _err(ex)