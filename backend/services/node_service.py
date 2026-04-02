from repositories import node_repository as repo
from typing import Optional


def create_node(title: str, parent_id: Optional[int] = None, **kwargs) -> dict:
    if parent_id is not None:
        parent = repo.get_node_by_id(parent_id)
        if not parent:
            raise ValueError(f"Parent node {parent_id} does not exist")
    node = repo.create_node(title=title, parent_id=parent_id, **kwargs)
    return node.to_dict()

def get_children(parent_id: Optional[int]) -> list[dict]:
    return [n.to_dict() for n in repo.get_children(parent_id)]

def get_root_nodes() -> list[dict]:
    return [n.to_dict() for n in repo.get_root_nodes()]

def get_node(node_id: int) -> dict:
    node = repo.get_node_by_id(node_id)
    if not node:
        raise ValueError(f"Node {node_id} not found")
    return node.to_dict()

def update_node(node_id: int, **kwargs) -> dict:
    node = repo.get_node_by_id(node_id)
    if not node:
        raise ValueError(f"Node {node_id} not found")
    updated = repo.update_node(node_id, **kwargs)
    return updated.to_dict()

def delete_node(node_id: int) -> dict:
    """Cascade delete — returns deleted IDs for frontend cleanup."""
    node = repo.get_node_by_id(node_id)
    if not node:
        raise ValueError(f"Node {node_id} not found")
    deleted_ids = repo.cascade_delete_node(node_id)
    return {"deleted_ids": deleted_ids}

def move_node(node_id: int, new_parent_id: Optional[int]) -> dict:
    """Reparent with cycle-check: can't move a node into its own subtree."""
    if new_parent_id is not None:
        subtree_ids = repo.get_subtree_ids(node_id)
        if new_parent_id in subtree_ids:
            raise ValueError("Cannot move a node into its own subtree (cycle detected)")
        parent = repo.get_node_by_id(new_parent_id)
        if not parent:
            raise ValueError(f"Target parent {new_parent_id} does not exist")

    updated = repo.reparent_node(node_id, new_parent_id)
    return updated.to_dict()

def reorder_siblings(parent_id: Optional[int], ordered_ids: list[int]) -> dict:
    repo.reorder_siblings(parent_id, ordered_ids)
    return {"ok": True}
