import json
from services import node_service as svc


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


def rpc_get_root_nodes(e) -> None:
    try:
        e.return_string(_ok(svc.get_root_nodes()))
    except Exception as ex:
        e.return_string(_err(ex))

def rpc_get_children(e) -> None:
    try:
        data = _parse(e)
        e.return_string(_ok(svc.get_children(data.get("parent_id"))))
    except Exception as ex:
        e.return_string(_err(ex))

def rpc_get_node(e) -> None:
    try:
        data = _parse(e)
        e.return_string(_ok(svc.get_node(data["id"])))
    except Exception as ex:
        e.return_string(_err(ex))

def rpc_create_node(e) -> None:
    try:
        data = _parse(e)
        e.return_string(_ok(svc.create_node(
            title=data["title"],
            parent_id=data.get("parent_id"),
            body=data.get("body", ""),
            state=data.get("state", "TODO"),
            scheduled=data.get("scheduled"),
            deadline=data.get("deadline"),
            repeater=data.get("repeater"),
        )))
    except Exception as ex:
        e.return_string(_err(ex))

def rpc_update_node(e) -> None:
    try:
        data = _parse(e)
        node_id = data.pop("id")
        e.return_string(_ok(svc.update_node(node_id, **data)))
    except Exception as ex:
        e.return_string(_err(ex))

def rpc_delete_node(e) -> None:
    try:
        data = _parse(e)
        e.return_string(_ok(svc.delete_node(data["id"])))
    except Exception as ex:
        e.return_string(_err(ex))

def rpc_move_node(e) -> None:
    try:
        data = _parse(e)
        e.return_string(_ok(svc.move_node(data["id"], data.get("new_parent_id"))))
    except Exception as ex:
        e.return_string(_err(ex))

def rpc_reorder_siblings(e) -> None:
    try:
        data = _parse(e)
        e.return_string(_ok(svc.reorder_siblings(data.get("parent_id"), data["ordered_ids"])))
    except Exception as ex:
        e.return_string(_err(ex))