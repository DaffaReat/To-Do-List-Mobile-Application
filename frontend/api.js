// api.js
// A wrapper for the Python WebUI bridge

async function callPython(functionName, payload = {}) {
    try {
        // WebUI expects the payload to be a JSON string, as seen in node_rpc.py
        const responseString = await webui.call(functionName, JSON.stringify(payload));
        const response = JSON.parse(responseString);

        if (!response.ok) {
            console.error(`Backend Error in ${functionName}:`, response.error);
            throw new Error(response.error);
        }

        return response.data;
    } catch (err) {
        console.error("WebUI Bridge Error:", err);
        throw err;
    }
}

export const OrgAPI = {
    // Read
    getRootNodes: () => callPython('get_root_nodes'),
    getChildren: (parentId) => callPython('get_children', { parent_id: parentId }),
    getNode: (id) => callPython('get_node', { id }),

    // Create & Update
    createNode: (title, parentId = null, extra = {}) => {
        return callPython('create_node', { title, parent_id: parentId, ...extra });
    },
    updateNode: (id, updates) => {
        // updates can be { state: "DONE" }, { title: "New Title" }, etc.
        return callPython('update_node', { id, ...updates });
    },

    // Delete & Move
    deleteNode: (id) => callPython('delete_node', { id }),
    moveNode: (id, newParentId) => callPython('move_node', { id, new_parent_id: newParentId }),
    reorderSiblings: (parentId, orderedIds) => callPython('reorder_siblings', { parent_id: parentId, ordered_ids: orderedIds })
};
