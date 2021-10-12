from cfg.my_cfg.entry_exit_nodes import entry_node, exit_node
from cfg.my_cfg.my_edge import MyEdge
from cfg.utils import full_node_id, get_node_function, get_non_ssa_node


class MyGraph:

    def __init__(self, vertices, edges):
        self._vertices = vertices
        self._edges = edges

    @property
    def vertices(self):
        return self._vertices

    @property
    def edges(self):
        return self._edges

    def get_graph_grouped_by_contract_function(self):
        contracts_graphs = {}

        for v in self._vertices:
            # function = v.function
            function = get_node_function(v)
            contract = function.contract

            if contract not in contracts_graphs:
                contracts_graphs[contract] = {}

            if function not in contracts_graphs[contract]:
                contracts_graphs[contract][function] = {
                    'vertices': set(),
                    'edges': set()
                }

            contracts_graphs[contract][function]['vertices'].add(v)

        for e in self._edges:
            # function = e.from_node.function
            function = get_node_function(e.from_node)
            contract = function.contract

            if contract not in contracts_graphs or function not in contracts_graphs[contract]:
                raise Exception('edge node contains a function not present in vertices')

            contracts_graphs[contract][function]['edges'].add(e)

        for c in contracts_graphs:
            for f in contracts_graphs[c]:
                g = contracts_graphs[c][f]
                contracts_graphs[c][f] = MyGraph(g['vertices'], g['edges'])

        return contracts_graphs

    def get_new_graph_with_connected_entry_exit_nodes(self):
        roots_leaves_orphans = self.get_roots_leaves_orphans()

        new_edges = set()
        for e in self._edges:
            new_edges.add(e)

        new_vertices = set()
        new_vertices.add(entry_node)
        new_vertices.add(exit_node)
        for v in self._vertices:
            new_vertices.add(v)

        for v in roots_leaves_orphans['roots'].union(roots_leaves_orphans['orphans']):
            e = MyEdge(entry_node, v)
            new_edges.add(e)

        for v in roots_leaves_orphans['leaves'].union(roots_leaves_orphans['orphans']):
            e = MyEdge(v, exit_node)
            new_edges.add(e)

        new_graph = MyGraphWithExitEntry(new_vertices, new_edges)

        return new_graph

    def get_orphans_and_leaves(self):
        parents = set()

        for e in self._edges:
            parents.add(e.from_node)

        orphans_and_leaves = self._vertices - parents

        return orphans_and_leaves

    def get_orphans_and_roots(self):
        dependents = set()

        for e in self._edges:
            dependents.add(e.to_node)

        orphans_and_roots = self._vertices - dependents

        return orphans_and_roots

    def get_roots_leaves_orphans(self):
        orphans_and_roots = self.get_orphans_and_roots()
        orphans_and_leaves = self.get_orphans_and_leaves()

        orphans = orphans_and_roots.intersection(orphans_and_leaves)
        roots = orphans_and_roots - orphans
        leaves = orphans_and_leaves - orphans

        return {'roots': roots,
                'leaves': leaves,
                'orphans': orphans}


class MyGraphWithExitEntry:
    def __init__(self, vertices, edges):
        self._vertices = vertices
        self._edges = edges

        if entry_node not in self._vertices and exit_node not in self._vertices:
            raise Exception('graph doesnt contain entry/exit nodes')

    @property
    def vertices(self):
        return self._vertices

    @property
    def edges(self):
        return self._edges

    def get_unreachable_nodes(self):
        all_v = self._vertices
        reachable_v = set()
        for e in self._edges:
            reachable_v.add(e.to_node)

        unreachable_nodes = all_v - reachable_v

        entry_exit_nodes = set()
        entry_exit_nodes.add(entry_node)
        entry_exit_nodes.add(exit_node)
        unreachable_nodes = unreachable_nodes - entry_exit_nodes

        return unreachable_nodes

    def get_function_to_root_and_leaf_nodes(self):
        roots_to_leaves = self.__get_roots_to_leaves_and_orphans()

        l = []
        function_to_root_and_leaf_nodes = {}
        for r_l in roots_to_leaves:
            root = r_l[0]
            leaves = r_l[1]

            # if isinstance(root, Operation):
            #     root_node = root.node
            # else:
            #     root_node = root

            # todo point ENTRY to all constructors (if not already pointed) to cover the case where a contract
            # can be created by deployment. The alternative is when it is created by another contract and its path is
            # already covered. In addition point ENTRY to all external function since they can be called from outside
            # the contract
            non_ssa_root = get_non_ssa_node(root)

            # a function can have many roots the entry to the function is the true root with node_id 0.
            # the other roots seem to be dead/unreachable code
            if non_ssa_root.node_id != 0:
                # s = full_node_id(root_node.function, root_node.node_id)
                s = full_node_id(root)
                s += " lines:" + str(non_ssa_root.source_mapping['lines'])
                l.append(s)

            # function = root_node.function
            function = get_node_function(root)
            if function not in function_to_root_and_leaf_nodes:
                function_to_root_and_leaf_nodes[function] = {
                    'roots': set(),
                    'leaves': set()
                }

            function_to_root_and_leaf_nodes[function]['roots'].add(root)
            function_to_root_and_leaf_nodes[function]['leaves'] = function_to_root_and_leaf_nodes[function]['leaves'].union(leaves)

        print('unreachable code in:' + '\n'.join(l))

        return function_to_root_and_leaf_nodes

    def get_graph_grouped_by_contract_function(self):
        contracts_graphs = {}

        for v in self._vertices:
            if v is entry_node or v is exit_node:
                continue

            # function = v.function
            function = get_node_function(v)
            contract = function.contract

            if contract not in contracts_graphs:
                contracts_graphs[contract] = {}

            if function not in contracts_graphs[contract]:
                contracts_graphs[contract][function] = {
                    'vertices': set(),
                    'edges': set()
                }

            contracts_graphs[contract][function]['vertices'].add(v)

        for e in self._edges:

            assert e.from_node is not exit_node

            if e.from_node is entry_node:
                continue

            # function = e.from_node.function
            function = get_node_function(e.from_node)
            contract = function.contract

            if contract not in contracts_graphs or function not in contracts_graphs[contract]:
                raise Exception('edge node contains a function not present in vertices')

            contracts_graphs[contract][function]['edges'].add(e)

        for c in contracts_graphs:
            for f in contracts_graphs[c]:
                g = contracts_graphs[c][f]

                found_exit_node = False
                for e in g['edges']:
                    assert e.from_node is not entry_node and e.from_node is not exit_node
                    assert e.to_node is not entry_node

                    if e.to_node is exit_node:
                        found_exit_node = True

                if found_exit_node:
                    # leaf edges should point only to exit node
                    g['vertices'].add(exit_node)

                contracts_graphs[c][f] = MyGraph(g['vertices'], g['edges'])

        return contracts_graphs

    def __get_roots_to_leaves_and_orphans(self):
        roots_to_leaves = list()

        if len(self._vertices) == 0:
            return roots_to_leaves

        roots = self.get_orphans_and_roots()

        for r in roots:
            leaves = set()
            processed = set()
            self.__get_node_to_leaves_and_orphans(r, leaves, processed)
            roots_to_leaves.append((r, leaves))

        return roots_to_leaves

    def __get_node_to_leaves_and_orphans(self, node, leaves, processed):

        if node in processed:
            return

        processed.add(node)

        if node is exit_node:
            return

        for e in self._edges:
            if e.from_node is node:
                if e.from_node is not entry_node and e.to_node is exit_node:
                    leaves.add(node)
                else:
                    self.__get_node_to_leaves_and_orphans(e.to_node, leaves, processed)



    def reset_entry_exit_node_connections(self):

        vertices = set()
        for v in self._vertices:
            if v is not entry_node and v is not exit_node:
                vertices.add(v)

        edges = set()
        for e in self._edges:
            if e.from_node is not entry_node and e.to_node is not exit_node:
                edges.add(e)

        new_graph = MyGraph(vertices, edges)
        new_graph = new_graph.get_new_graph_with_connected_entry_exit_nodes()

        self._vertices = new_graph.vertices
        self._edges = new_graph.edges

    def get_orphans_and_roots(self):
        orphans_and_roots = set()

        if len(self._vertices) == 0:
            return orphans_and_roots

        for e in self._edges:
            if e.from_node is entry_node and e.to_node is not exit_node:
                orphans_and_roots.add(e.to_node)

        return orphans_and_roots

    def get_orphans_and_leaves(self):
        orphans_and_leaves = set()

        if len(self._vertices) == 0:
            return orphans_and_leaves

        for e in self._edges:
            if e.from_node is not entry_node and e.to_node is exit_node:
                orphans_and_leaves.add(e.from_node)

        return orphans_and_leaves

    def get_roots_leaves_orphans(self):
        orphans_and_roots = self.get_orphans_and_roots()
        orphans_and_leaves = self.get_orphans_and_leaves()

        orphans = orphans_and_roots.intersection(orphans_and_leaves)
        roots = orphans_and_roots - orphans
        leaves = orphans_and_leaves - orphans

        return {'roots': roots,
                'leaves': leaves,
                'orphans': orphans}



