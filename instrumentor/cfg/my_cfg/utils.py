from cfg.utils import full_node_id


def populate_reachable_nodes(node, edges, reachable_nodes_from_entry):
    reachable_nodes_from_entry.add(node)

    for e in edges:
        if e.from_node is node:
            if e.to_node not in reachable_nodes_from_entry:
                populate_reachable_nodes(e.to_node, edges, reachable_nodes_from_entry)


def get_key_from_edge(e):
    # from_node_full_id = full_node_id(e.from_node.function, e.from_node.node_id)
    from_node_full_id = full_node_id(e.from_node)
    # to_node_full_id = full_node_id(e.to_node.function, e.to_node.node_id)
    to_node_full_id = full_node_id(e.to_node)
    edges_key = hash(from_node_full_id + '|' + to_node_full_id)
    return edges_key


def get_key_from_edge_node_ids(from_node_full_id, to_node_full_id):
    edges_key = hash(from_node_full_id + '|' + to_node_full_id)
    return edges_key
