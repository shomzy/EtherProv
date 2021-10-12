import sys
from collections import defaultdict

from cfg.my_cfg.my_edge import MyEdge
from cfg.utils import full_node_id, get_parents, get_exit, get_entry, get_outgoing_edges, get_incoming_edges, \
    get_children

INT_MIN = -sys.maxsize - 1


def verify_graph(vertices, graph):
    num_entry = 0
    num_exit = 0

    for v in vertices:
        parents = get_parents(v, graph)
        if len(parents) == 0:
            num_entry = num_entry + 1
        children = get_children(v, graph)
        if len(children) == 0:
            num_exit = num_exit + 1

    if num_entry != 1 and num_exit != 1:
        raise Exception("No unique entry and exit to cfg")


def dfs_find_back_edges(node, graph: list, color: defaultdict, back_edges: list):
    color[node] = 1
    outgoing_edges = get_outgoing_edges(node, graph)
    for e in outgoing_edges:
        to_node = e.to_node
        if color[to_node] != 0:
            if color[to_node] == 1:
                back_edges.append(e)
        else:
            dfs_find_back_edges(to_node, graph, color, back_edges)

    color[node] = 2


def topological_sort(vertices, graph):
    num_incoming = defaultdict(int)
    for to_node in vertices:
        incoming = get_incoming_edges(to_node, graph)
        num_incoming[to_node] = len(incoming)

    sort = list()
    for n in vertices:
        if num_incoming[n] == 0:
            sort.append(n)

    i = 0
    while i < len(sort):
        to_remove = sort[i]
        children = get_children(to_remove, graph)
        for c in children:
            num_edges = num_incoming[c]
            num_edges = num_edges - 1
            num_incoming[c] = num_edges
            if num_edges == 0:
                sort.append(c)
        i = i + 1

    return sort


def generate_vals(sort, vertices, graph, entry):
    val = defaultdict(int)
    num_paths = defaultdict(int)

    for n in reversed(sort):
        outgoing_edges = get_outgoing_edges(n, graph)
        if len(outgoing_edges) == 0:
            # this is the exit node
            num_paths[n] = 1
        else:
            num_paths[n] = 0
            for e in outgoing_edges:
                val[e] = num_paths[n]
                to_block = e.to_node
                num_paths[n] = num_paths[n] + num_paths[to_block]

    return val


def exists_path(u, v, tree, visited) -> bool:
    if u is v:
        return True

    visited.add(u)
    for e in tree:
        next = None
        if e.to_node is u:
            next = e.from_node
        elif e.from_node is u:
            next = e.to_node

        if next is not None:
            if next not in visited:
                if exists_path(next, v, tree, visited):
                    return True

    return False


def gen_max_spanning_tree(graph):
    tree = set()

    for e in graph:
        u = e.from_node
        v = e.to_node

        visited = set()
        if exists_path(u, v, tree, visited) == False:
            tree.add(e)

    return tree


def get_inc(v, u, vals, tree, visited) -> int:
    if v is u:
        return 0

    inc = INT_MIN
    visited.add(v)
    for e in tree:
        next = None
        if e.to_node is v:
          next = e.from_node
        elif e.from_node is v:
          next = e.to_node

        if next is not None:

            if next not in visited:
                next_inc = get_inc(next, u, vals, tree, visited)
                if next_inc != INT_MIN:
                    val = vals[e]

                    if e.to_node is v:
                        val = -val
                    inc = next_inc + val
                    break

    return inc


def generate_incs(graph, vals, tree) -> dict:
    incs = defaultdict(int)

    for e in graph:

        if e not in tree:
            u = e.from_node
            v = e.to_node
            visited = set()
            inc = get_inc(v, u, vals, tree, visited)
            if inc == INT_MIN:
                raise Exception("Unable to compute inc for chord")
            inc += vals[e]
            incs[e] = inc

    return incs


def dfs_path_incs(u, graph, incs, inc, on_path, entry, exit) -> int:

    new_string = on_path + "," + str(full_node_id(u))
    outgoing_edges = get_outgoing_edges(u, graph)
    if len(outgoing_edges) == 0:
        print(new_string, " : ", inc)
        return 1
    else:
        num_paths = 0
        for e in outgoing_edges:
            new_inc = inc + incs[e]
            if e.back_edge_entry_mapping is not None:
                num_paths += dfs_path_incs(e.to_node, graph, incs, incs[e], "Loop head at -> ", entry, exit)
            elif e.back_edge_exit_mapping is not None:
                num_paths += 1
                print(new_string, " loop up to ", full_node_id(e.back_edge_exit_mapping.to_node), " : ", new_inc)
            else:
                num_paths += dfs_path_incs(e.to_node, graph, incs, new_inc, new_string, entry, exit)

        return num_paths


def extract_efficient_path_profiling_incs(extended_contracts_graph_with_entry_exit):

    graph = extended_contracts_graph_with_entry_exit.edges
    vertices = extended_contracts_graph_with_entry_exit.vertices

    verify_graph(vertices, graph)

    entry = get_entry(vertices, graph)
    exit = get_exit(vertices, graph)

    print("Entry: ", str(entry.node_id), " , Exit: ", str(exit.node_id))

    color = defaultdict(int)
    back_edges = list()
    dfs_find_back_edges(entry, graph, color, back_edges)

    print("back edges:")
    for e in back_edges:
        print(full_node_id(e.from_node), " - ", full_node_id(e.to_node))

    g_minus_back_plus_loop = list()
    for e in graph:
        back_edge = None
        for be in back_edges:
            if e is be:
                back_edge = be
                break

        if back_edge is not None:

            entry_to_head = MyEdge(entry, e.to_node)
            entry_to_head.back_edge_entry_mapping = e
            g_minus_back_plus_loop.append(entry_to_head)

            tail_to_exit = MyEdge(e.from_node, exit)
            tail_to_exit.back_edge_exit_mapping = e
            g_minus_back_plus_loop.append(tail_to_exit)

        else:
            g_minus_back_plus_loop.append(e)

    print("g_minus_back_plus_loop:")
    for e in g_minus_back_plus_loop:
        print(full_node_id(e.from_node), "-", full_node_id(e.to_node))

    sort = topological_sort(vertices, g_minus_back_plus_loop)
    print("sort:")
    for n in sort:
        print(full_node_id(n))

    vals = generate_vals(sort, vertices, g_minus_back_plus_loop, entry)

    print("vals:")
    for item in vals.items():
        e = item[0]
        val = item[1]
        print(full_node_id(e.from_node), "-", full_node_id(e.to_node), ":", val)

    g_minus_back_plus_loop_plus_ete = list()
    exit_to_entry = MyEdge(exit, entry)
    vals[exit_to_entry] = 0
    g_minus_back_plus_loop_plus_ete.append(exit_to_entry)
    for e in g_minus_back_plus_loop:
        g_minus_back_plus_loop_plus_ete.append(e)

    tree = gen_max_spanning_tree(g_minus_back_plus_loop_plus_ete)

    print("max spanning tree edges:")
    for e in tree:
        print(full_node_id(e.from_node), "-", full_node_id(e.to_node))

    incs = generate_incs(g_minus_back_plus_loop_plus_ete, vals, tree)

    print("incs:")
    for i in incs.items():
        e = i[0]
        inc = i[1]
        print(full_node_id(e.from_node), "-", full_node_id(e.to_node), ":", inc)

    print("Paths to sums:")
    num_paths = dfs_path_incs(entry, g_minus_back_plus_loop, incs, 0, "", entry, exit)
    print("Num paths: ", num_paths)

    roots_leaves_orphans = extended_contracts_graph_with_entry_exit.get_roots_leaves_orphans()

    for v in roots_leaves_orphans['roots'].union(roots_leaves_orphans['orphans']):
        for e in graph:
            if e.from_node is entry and e.to_node is v:
                if e not in incs:
                    incs[e] = 0

    for v in roots_leaves_orphans['leaves'].union(roots_leaves_orphans['orphans']):
        for e in graph:
            if e.from_node is v and e.to_node is exit:
                if e not in incs:
                    incs[e] = 0

    return back_edges, g_minus_back_plus_loop, incs


def dfs_paths_extractor(u, g_minus_back_plus_loop, back_edges, incs, inc, paths, current_path):

    outgoing_edges = get_outgoing_edges(u, g_minus_back_plus_loop)
    if len(outgoing_edges) == 0:
        paths[inc] = {
            'is_loop_path': False,
            'path': current_path
        }

    else:

        for e in outgoing_edges:
            new_inc = inc + incs[e]

            if e.back_edge_entry_mapping is not None:
                new_current_path = list()
                new_current_path.append(e)

                dfs_paths_extractor(e.to_node, g_minus_back_plus_loop, back_edges, incs, incs[e], paths, new_current_path)

            elif e.back_edge_exit_mapping is not None:
                new_current_path = list()
                new_current_path.extend(current_path)
                new_current_path.append(e.back_edge_exit_mapping)

                paths[new_inc] = {
                    'is_loop_path': True,
                    'path': new_current_path
                }

            else:
                new_current_path = list()
                new_current_path.extend(current_path)
                new_current_path.append(e)

                dfs_paths_extractor(e.to_node, g_minus_back_plus_loop, back_edges, incs, new_inc, paths, new_current_path)

