from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Node:
    id: int
    parent_id: Optional[int]
    title: str
    body: str
    state: str
    position: int
    scheduled: Optional[str]
    deadline: Optional[str]
    repeater: Optional[str]
    created_at: str
    updated_at: str

    def to_dict(self) -> dict:
        return asdict(self)

def row_to_node(row) -> Node:
    return Node(
        id=row["id"],
        parent_id=row["parent_id"],
        title=row["title"],
        body=row["body"],
        state=row["state"],
        position=row["position"],
        scheduled=row["scheduled"],
        deadline=row["deadline"],
        repeater=row["repeater"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
