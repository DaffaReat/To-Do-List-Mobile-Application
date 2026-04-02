import webui
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

def main():
    init_schema()

    window = webui.window()

    window.bind("get_root_nodes",   rpc_get_root_nodes)
    window.bind("get_children",     rpc_get_children)
    window.bind("get_node",         rpc_get_node)
    window.bind("create_node",      rpc_create_node)
    window.bind("update_node",      rpc_update_node)
    window.bind("delete_node",      rpc_delete_node)
    window.bind("move_node",        rpc_move_node)
    window.bind("reorder_siblings", rpc_reorder_siblings)

    window.show("frontend/index.html")
    webui.wait()

if __name__ == "__main__":
    main()