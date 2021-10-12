from slither.core.cfg.node import Node
from slither.core.cfg.node import NodeType
from slither.slithir.operations import SolidityCall
from slither.slithir.operations.operation import Operation

from cfg.cfg_parser import generate_output_files
from cfg.cfg_parser.function_call_analyzers import get_call_site_root_and_leaves
from cfg.cfg_parser.state_variable_analyzer import extract_states_read_written, is_slith_ir_variable, \
    extract_ssa_read_write_vars, convert_read_write_vars
from cfg.dot.formatters import format_edge_with_label_and_color
from cfg.dot.output import output_merged, output_ssa_merged
from cfg.my_cfg.entry_exit_nodes import entry_node, exit_node
from cfg.my_cfg.my_edge import MyEdge
from cfg.my_cfg.my_graph import MyGraph
from cfg.my_cfg.utils import get_key_from_edge_node_ids
from cfg.utils import full_function_signature, full_node_id, get_node_function, get_non_ssa_node, get_ssa_node_position


def get_function_graph(function):
    vertices = set()
    edges = set()

    for node in function.nodes:

        vertices.add(node)

        if node.type == NodeType.IF:
            true_node = node.son_true
            if true_node:
                e = MyEdge(node, true_node)
                e._true_son = True
                edges.add(e)

            false_node = node.son_false
            if false_node:
                e = MyEdge(node, false_node)
                e._false_son = True
                edges.add(e)

        elif node.sons:
            for son in node.sons:
                e = MyEdge(node, son)
                edges.add(e)

        else:
            # no sons - leaf node
            pass

    return MyGraph(vertices, edges)


def get_function_ssa_graph(function):
    vertices = set()
    edges = set()

    for node in function.nodes:
        # if node.type != NodeType.ENTRYPOINT and \
        #         node.type != NodeType.OTHER_ENTRYPOINT and \
        #         node.type != NodeType.ENDIF and \
        #         node.type != NodeType.VARIABLE and \
        #         (node.irs_ssa is None or len(node.irs_ssa) == 0):
        #     raise Exception('unhandled scenario')

        if len(node.irs_ssa) > 0:
            first_ir_ssa = node.irs_ssa[0]
            vertices.add(first_ir_ssa)

            current_ir_ssa = first_ir_ssa
            if len(node.irs_ssa) > 1:
                for i in range(1, len(node.irs_ssa)):
                    next_ir_ssa = node.irs_ssa[i]
                    vertices.add(next_ir_ssa)
                    e = MyEdge(current_ir_ssa, next_ir_ssa)
                    edges.add(e)
                    current_ir_ssa = next_ir_ssa
        else:
            vertices.add(node)

        node_last_istr = get_node_last_instr(node)

        if node.type == NodeType.IF:
            true_node = node.son_true
            if true_node:
                node_first_istr = get_node_first_instr(true_node)
                e = MyEdge(node_last_istr, node_first_istr)
                e._true_son = True
                edges.add(e)

            false_node = node.son_false
            if false_node:
                node_first_istr = get_node_first_instr(false_node)
                e = MyEdge(node_last_istr, node_first_istr)
                e._false_son = True
                edges.add(e)

        elif node.sons:
            for son in node.sons:
                node_first_istr = get_node_first_instr(son)
                e = MyEdge(node_last_istr, node_first_istr)
                edges.add(e)

        else:
            # no sons - leaf node
            pass

    return MyGraph(vertices, edges)


def get_node_first_instr(node):
    node_first_instr = None
    if node.irs_ssa is None or len(node.irs_ssa) == 0:
        node_first_instr = node
    else:
        node_first_instr = node.irs_ssa[0]

    return node_first_instr


def get_node_last_instr(node):
    node_last_istr = None
    if len(node.irs_ssa) > 0:
        node_last_istr = node.irs_ssa[len(node.irs_ssa) - 1]
    else:
        node_last_istr = node

    return node_last_istr


def get_my_cfg_ssa_graph(my_graph, edge_instr):
    graph_nodes = []
    for node in my_graph._vertices:

        # f_node_id = full_node_id(node.function, node.node_id)
        f_node_id = full_node_id(node)

        node_type = None
        if isinstance(node, Operation):
            # if isinstance(node, Phi):
            #     node_type = node.__class__
            # else:
            #     node_type = node.type_str
            node_type = type(node).__name__

            label = 'Node Type: {} {}\n'.format(node_type, f_node_id)

            color = "black"

            label += 'SSA:\n{}\n'.format(node)

            if node.node.expression:
                if is_slith_ir_variable(node):
                    _ssa_vars_read = []
                    _ssa_vars_written = []
                    extract_ssa_read_write_vars(node, _ssa_vars_read, _ssa_vars_written)
                    state_variables_read, state_variables_written = convert_read_write_vars(_ssa_vars_read, _ssa_vars_written)

                    state_variables_read = [v.name for v in state_variables_read]
                    state_variables_written = [v.name for v in state_variables_written]

                    if len(state_variables_read) > 0:
                        label += '\nstate_vars_read: ' + ','.join(state_variables_read)
                        color = "red"

                    if len(state_variables_written) > 0:
                        label += '\nstate_vars_written: ' + ','.join(state_variables_written)
                        color = "red"

        elif isinstance(node, Node):
            node_type = str(node.type)

            label = 'Node Type: {} {}\n'.format(node_type, f_node_id)

            color = "black"

            if node.expression:
                label += 'EXPRESSION:\n{}\n'.format(node.expression)

                state_variables_read, state_variables_written = extract_states_read_written(node)

                state_variables_read = [v.name for v in state_variables_read]
                state_variables_written = [v.name for v in state_variables_written]

                if len(state_variables_read) > 0:
                    label += '\nstate_vars_read: ' + ','.join(state_variables_read)
                    color = "red"

                if len(state_variables_written) > 0:
                    label += '\nstate_vars_written: ' + ','.join(state_variables_written)
                    color = "red"
        else:
            raise Exception('unhandled scenario')

        graph_node_str = '"{}" [label="{}" color="{}"];\n'.format(full_node_id(node), label, color)
        graph_nodes.append((node, graph_node_str))

    graph_edges = []
    for e in my_graph._edges:

        # from_node_full_id = full_node_id(e._from_node.function, e._from_node.node_id)
        from_node_full_id = full_node_id(e._from_node)
        # to_node_full_id = full_node_id(e._to_node.function, e._to_node.node_id)
        to_node_full_id = full_node_id(e._to_node)

        if e._true_son or e._false_son:
            if e._true_son:
                label = "True"

                if edge_instr is not None:
                    edges_key = get_key_from_edge_node_ids(from_node_full_id, to_node_full_id)
                    if edges_key in edge_instr:
                        inc_str = edge_instr[edges_key]['instrumentation']
                        # label += "\ninstrument: " + '\n'.join(inc_str)
                        label += "\ninstrument: " + inc_str

                graph_edges.append(
                    format_edge_with_label_and_color(
                        from_node_full_id, to_node_full_id,
                        label=label, color="blue" if e._is_call_site else "black"))

            if e._false_son:
                label = "False"

                if edge_instr is not None:
                    edges_key = get_key_from_edge_node_ids(from_node_full_id, to_node_full_id)
                    if edges_key in edge_instr:
                        inc_str = edge_instr[edges_key]['instrumentation']
                        # label += "\ninstrument: " + '\n'.join(inc_str)
                        label += "\ninstrument: " + inc_str

                graph_edges.append(
                    format_edge_with_label_and_color(
                        from_node_full_id, to_node_full_id,
                        label=label, color="blue" if e._is_call_site else "black"))
        else:

            label = None
            if edge_instr is not None:
                edges_key = get_key_from_edge_node_ids(from_node_full_id, to_node_full_id)
                if edges_key in edge_instr:
                    inc_str = edge_instr[edges_key]['instrumentation']
                    # label = "\ninstrument: " + '\n'.join(inc_str)
                    label = "\ninstrument: " + inc_str

            graph_edges.append(
                format_edge_with_label_and_color(
                    from_node_full_id, to_node_full_id,
                    label=label, color="blue" if e._is_call_site else "black"))

    return graph_nodes, graph_edges


def get_my_cfg_graph(my_graph, edge_instr):
    graph_nodes = []
    for node in my_graph._vertices:

        # f_node_id = full_node_id(node.function, node.node_id)
        f_node_id = full_node_id(node)

        label = 'Node Type: {} {}\n'.format(str(node.type), f_node_id)

        color = "black"

        if node.expression:
            # print(node.expression)

            label += 'EXPRESSION:\n{}\n'.format(node.expression)

            state_variables_read, state_variables_written = extract_states_read_written(node)

            state_variables_read = [v.name for v in state_variables_read]
            state_variables_written = [v.name for v in state_variables_written]

            if len(state_variables_read) > 0:
                label += '\nstate_vars_read: ' + ','.join(state_variables_read)
                color = "red"

            if len(state_variables_written) > 0:
                label += '\nstate_vars_written: ' + ','.join(state_variables_written)
                color = "red"

        # if edge_incs is not None:
        #     for e in my_graph._edges:
        #         if e.from_node is entry_node and e.to_node is node:
        #             edges_key = get_key_from_edge(e)
        #             if edges_key in edge_incs:
        #                 inc_str = edge_incs[edges_key]['instrumentation']
        #                 label += "\ninstrument: " + '\n'.join(inc_str)

        # if node_incs is not None:
        #     if f_node_id in node_incs:
        #         inc_str = node_incs[f_node_id]['instrumentation']
        #         label += "\ninstrument: " + '\n'.join(inc_str)

        # graph_node_str = '"{}" [label="{}" color="{}"];\n'.format(full_node_id(node.function, node.node_id), label, color)
        graph_node_str = '"{}" [label="{}" color="{}"];\n'.format(full_node_id(node), label, color)
        graph_nodes.append((node, graph_node_str))

    graph_edges = []
    for e in my_graph._edges:

        # from_node_full_id = full_node_id(e._from_node.function, e._from_node.node_id)
        from_node_full_id = full_node_id(e._from_node)
        # to_node_full_id = full_node_id(e._to_node.function, e._to_node.node_id)
        to_node_full_id = full_node_id(e._to_node)

        if e._true_son or e._false_son:
            if e._true_son:
                label = "True"

                if edge_instr is not None:
                    edges_key = get_key_from_edge_node_ids(from_node_full_id, to_node_full_id)
                    if edges_key in edge_instr:
                        inc_str = edge_instr[edges_key]['instrumentation']
                        # label += "\ninstrument: " + '\n'.join(inc_str)
                        label += "\ninstrument: " + inc_str

                graph_edges.append(
                    format_edge_with_label_and_color(
                        from_node_full_id, to_node_full_id,
                        label=label, color="blue" if e._is_call_site else "black"))

            if e._false_son:
                label = "False"

                if edge_instr is not None:
                    edges_key = get_key_from_edge_node_ids(from_node_full_id, to_node_full_id)
                    if edges_key in edge_instr:
                        inc_str = edge_instr[edges_key]['instrumentation']
                        # label += "\ninstrument: " + '\n'.join(inc_str)
                        label += "\ninstrument: " + inc_str
                graph_edges.append(
                    format_edge_with_label_and_color(
                        from_node_full_id, to_node_full_id,
                        label=label, color="blue" if e._is_call_site else "black"))
        else:

            label = None
            if edge_instr is not None:
                edges_key = get_key_from_edge_node_ids(from_node_full_id, to_node_full_id)
                if edges_key in edge_instr:
                    inc_str = edge_instr[edges_key]['instrumentation']
                    # label = "\ninstrument: " + '\n'.join(inc_str)
                    label = "\ninstrument: " + inc_str

            graph_edges.append(
                format_edge_with_label_and_color(
                    from_node_full_id, to_node_full_id,
                    label=label, color="blue" if e._is_call_site else "black"))

    return graph_nodes, graph_edges


def get_contracts_graph(contracts):
    vertices = set()
    edges = set()

    for contract in contracts:
        for function in contract.functions + contract.modifiers:
            g = get_function_graph(function)
            vertices = vertices.union(g.vertices)
            edges = edges.union(g.edges)

    mg = MyGraph(vertices, edges)

    return mg


def get_contracts_ssa_graph(contracts):
    vertices = set()
    edges = set()

    for contract in contracts:
        for function in contract.functions + contract.modifiers:
            g = get_function_ssa_graph(function)
            vertices |= g.vertices
            edges |= g.edges

    mg = MyGraph(vertices, edges)

    return mg


def get_consolidated_contracts(contracts_ssa_graph_with_entry_exit):
    function_to_root_and_leaf_nodes = contracts_ssa_graph_with_entry_exit.get_function_to_root_and_leaf_nodes()
    contracts = contracts_ssa_graph_with_entry_exit.get_graph_grouped_by_contract_function()

    vertices = set()
    edges = set()
    all_processed_ssa_nodes = set()

    for contract_key in contracts:

        for function_ssa_graph_key in contracts[contract_key]:
            function_roots_leaves = function_to_root_and_leaf_nodes[function_ssa_graph_key]

            roots = function_roots_leaves['roots']

            main_ssa_root = get_main_ssa_root(roots)

            function_ssa_graph = contracts[contract_key][function_ssa_graph_key]

            consolidated_vertices = set()
            consolidated_edges = set()
            processed_ssa_nodes = set()
            get_consolidated_graph(function_ssa_graph, main_ssa_root, consolidated_vertices, consolidated_edges, processed_ssa_nodes, function_to_root_and_leaf_nodes)
            vertices |= consolidated_vertices
            edges |= consolidated_edges
            all_processed_ssa_nodes |= processed_ssa_nodes

    for v in contracts_ssa_graph_with_entry_exit.vertices:
        if v is entry_node or v is exit_node:
            continue
        if v not in all_processed_ssa_nodes:
            assert False

    mg = MyGraph(vertices, edges)
    mg = mg.get_new_graph_with_connected_entry_exit_nodes()

    for v in mg.vertices:
        assert not isinstance(v, Operation)

    for e in mg.edges:
        assert not isinstance(e.from_node, Operation)
        assert not isinstance(e.to_node, Operation)

    return mg


def get_main_ssa_root(ssa_roots):
    assert len(ssa_roots) > 0

    main_ssa_root = None
    for root in ssa_roots:
        main_ssa_root = root
        break

    if not isinstance(main_ssa_root, Operation):
        assert len(ssa_roots) == 1
        return main_ssa_root

    main_ssa_root = None
    for ssa_root in ssa_roots:
        assert isinstance(ssa_root, Operation)

        if ssa_root.node.node_id == 0:
            main_ssa_root = ssa_root

    assert main_ssa_root is not None

    return main_ssa_root


def get_call_site_calls_to_root_from_leaves_edges(contracts_graph_with_entry_exit):
    function_to_root_and_leaf_nodes = contracts_graph_with_entry_exit.get_function_to_root_and_leaf_nodes()

    call_site_edges = set()

    for e in contracts_graph_with_entry_exit.edges:
        if e.from_node is entry_node and e.to_node is exit_node:
            continue

        call_site_roots_and_leaves = list()

        if isinstance(e.from_node, Operation):
            if isinstance(e.from_node, SolidityCall):
                pass
            else:
                get_call_site_root_and_leaves(e.from_node, function_to_root_and_leaf_nodes, call_site_roots_and_leaves)
        # else:
        #     for ir in e.from_node.irs:
        #         get_call_site_root_and_leaves(ir, function_to_root_and_leaf_nodes, call_site_roots_and_leaves)

        for current_cs_root_and_leaves in call_site_roots_and_leaves:
            roots = current_cs_root_and_leaves['roots']
            leaves = current_cs_root_and_leaves['leaves']
            for root in roots:
                e_in = MyEdge(e.from_node, root)
                e_in._is_call_site = True
                call_site_edges.add(e_in)

                for l in leaves:
                    e_out = MyEdge(l, e.from_node)
                    e_out._related_to_call_site_edge_id = e_in.edge_id
                    call_site_edges.add(e_out)

    return call_site_edges


def get_consolidated_graph(function_ssa_graph, ssa_node, consolidated_vertices, consolidated_edges, processed_ssa_nodes, function_to_root_and_leaf_nodes):

    # we should deal only with first ssa_node in a node
    assert get_ssa_node_position(ssa_node) == 0

    if ssa_node in processed_ssa_nodes:
        return

    processed_ssa_nodes.add(ssa_node)

    # don't collect entry/exit nodes
    if ssa_node is exit_node:
        return

    non_ssa_node = get_non_ssa_node(ssa_node)
    assert non_ssa_node not in consolidated_vertices
    consolidated_vertices.add(non_ssa_node)

    # a node contains chained call_site_calls like: a(a(100))
    # node1(ssa_node1 -> ssa_node2.call_site_call -> ssa_node3 -> ssa_node4.call_site_call -> ssa_node5) -> node2()

    node_ssa_call_sites = get_node_ssa_call_sites(ssa_node, function_ssa_graph, function_to_root_and_leaf_nodes, processed_ssa_nodes)

    outer_most_call_site_roots_and_leaves = None
    e_in = None

    if len(node_ssa_call_sites) > 0:
        inner_most_call_site_roots_and_leaves = node_ssa_call_sites[0]
        inner_most_ssa_roots = inner_most_call_site_roots_and_leaves['roots']

        inner_most_main_ssa_root = get_main_ssa_root(inner_most_ssa_roots)
        non_ssa_inner_most_root_node = get_non_ssa_node(inner_most_main_ssa_root)
        assert non_ssa_node is not non_ssa_inner_most_root_node

        e_in = MyEdge(non_ssa_node, non_ssa_inner_most_root_node)
        e_in._is_call_site = True

        # consolidated_edges.add(e_in)
        add_to_set_with_check(e_in, consolidated_edges)

        if len(node_ssa_call_sites) == 1:
            outer_most_call_site_roots_and_leaves = inner_most_call_site_roots_and_leaves
        else:
            # len(node_ssa_call_sites) > 1
            outer_most_call_site_roots_and_leaves = node_ssa_call_sites[len(node_ssa_call_sites) - 1]

            current_call_site_roots_and_leaves = node_ssa_call_sites[0]
            i = 1
            while i < len(node_ssa_call_sites):

                current_ssa_leaves = current_call_site_roots_and_leaves['leaves']
                next_call_site_roots_and_leaves = node_ssa_call_sites[i]
                next_ssa_roots = next_call_site_roots_and_leaves['roots']
                next_ssa_main_root = get_main_ssa_root(next_ssa_roots)
                next_non_ssa_main_root = get_non_ssa_node(next_ssa_main_root)

                for ssa_l in current_ssa_leaves:
                    non_ssa_l = get_non_ssa_node(ssa_l)
                    assert non_ssa_l is not next_non_ssa_main_root

                    e_out = MyEdge(non_ssa_l, next_non_ssa_main_root)

                    # consolidated_edges.add(e_out)
                    add_to_set_with_check(e_out, consolidated_edges)

                current_call_site_roots_and_leaves = next_call_site_roots_and_leaves
                i = i + 1

    last_ssa_in_node = get_last_ssa_in_node(ssa_node, function_ssa_graph)

    outgoing_edges = set()
    for e in function_ssa_graph.edges:
        if e.from_node is last_ssa_in_node and e.to_node is not exit_node:
            assert get_ssa_node_position(e.to_node) == 0
            non_ssa_from_node = get_non_ssa_node(e.from_node)
            non_ssa_to_node = get_non_ssa_node(e.to_node)
            assert non_ssa_from_node is not non_ssa_to_node
            outgoing_edges.add(e)

    for e in outgoing_edges:
        non_ssa_from_node = get_non_ssa_node(e.from_node)
        non_ssa_to_node = get_non_ssa_node(e.to_node)

        if outer_most_call_site_roots_and_leaves is not None:
            outer_ssa_leaves = outer_most_call_site_roots_and_leaves['leaves']
            for l in outer_ssa_leaves:
                non_ssa_l = get_non_ssa_node(l)
                if non_ssa_l is non_ssa_to_node:
                    assert False

                e_out = MyEdge(non_ssa_l, non_ssa_to_node)
                e_out._true_son = e._true_son
                e_out._false_son = e._false_son
                e_out._related_to_call_site_edge_id = e_in.edge_id

                # consolidated_edges.add(e_out)
                add_to_set_with_check(e_out, consolidated_edges)
        else:
            e_out = MyEdge(non_ssa_from_node, non_ssa_to_node)
            e_out._true_son = e._true_son
            e_out._false_son = e._false_son

            # consolidated_edges.add(e_out)
            add_to_set_with_check(e_out, consolidated_edges)

        get_consolidated_graph(function_ssa_graph, e.to_node, consolidated_vertices, consolidated_edges, processed_ssa_nodes, function_to_root_and_leaf_nodes)


def get_last_ssa_in_node(first_ssa_in_node, ssa_graph_with_entry_exit):
    assert get_ssa_node_position(first_ssa_in_node) == 0

    last_ssa_node = first_ssa_in_node

    next_ssa_in_node = get_next_ssa_in_node(first_ssa_in_node, ssa_graph_with_entry_exit)
    while next_ssa_in_node is not None:
        last_ssa_node = next_ssa_in_node
        next_ssa_in_node = get_next_ssa_in_node(next_ssa_in_node, ssa_graph_with_entry_exit)

    if last_ssa_node is None:
        last_ssa_node = first_ssa_in_node

    return last_ssa_node


def get_next_ssa_in_node(ssa_node, ssa_graph_with_entry_exit):
    next_ssa_node = None
    for e in ssa_graph_with_entry_exit.edges:

        if e.from_node is ssa_node:

            non_ssa_from_node = get_non_ssa_node(e.from_node)
            non_ssa_to_node = get_non_ssa_node(e.to_node)

            if non_ssa_from_node is non_ssa_to_node:
                next_ssa_node = e.to_node
                break

    return next_ssa_node


def get_node_ssa_call_sites(ssa_node, ssa_graph_with_entry_exit, function_to_root_and_leaf_nodes, processed_ssa_nodes):

    call_site_roots_and_leaves = list()

    if not isinstance(ssa_node, Operation):
        return call_site_roots_and_leaves

    assert get_ssa_node_position(ssa_node) == 0

    get_call_site_roots_and_leaves(ssa_node, function_to_root_and_leaf_nodes, call_site_roots_and_leaves)

    next_ssa_node = get_next_ssa_in_node(ssa_node, ssa_graph_with_entry_exit)
    while next_ssa_node is not None:
        assert next_ssa_node not in processed_ssa_nodes
        processed_ssa_nodes.add(next_ssa_node)

        get_call_site_roots_and_leaves(next_ssa_node, function_to_root_and_leaf_nodes, call_site_roots_and_leaves)
        next_ssa_node = get_next_ssa_in_node(next_ssa_node, ssa_graph_with_entry_exit)

    return call_site_roots_and_leaves


def add_to_set_with_check(e, set_):
    # if isinstance(e.to_node, Condition):
    #     x=3
    #
    # if isinstance(e.from_node, InternalCall):
    #     x=3
    #
    # if isinstance(e.from_node, Index):
    #     x=3

    for ee in set_:
        if ee.from_node is e.from_node and ee.to_node is e.to_node and e._true_son == ee._true_son and e._false_son == ee._false_son:
            raise CyclicReferenceException('cyclic reference')

    set_.add(e)


class CyclicReferenceException(Exception):
    pass


class FunctionNotInstrumentedException(Exception):
    pass


def get_call_site_roots_and_leaves(ssa_node, function_to_root_and_leaf_nodes, call_site_roots_and_leaves):
    assert isinstance(ssa_node, Operation)

    if isinstance(ssa_node, SolidityCall):
        pass
    else:
        get_call_site_root_and_leaves(ssa_node, function_to_root_and_leaf_nodes, call_site_roots_and_leaves)


def output_my_cfg_graph(contracts_graph, edge_instr, filename):

    if not generate_output_files:
        return

    #contracts_graphs = contracts_graph.get_graph_grouped_by_contract_function()

    graph_nodes, all_graph_edges = get_my_cfg_graph(contracts_graph, edge_instr)

    #entry_exit_set = set()
    grouped_nodes = {}
    for g_node in graph_nodes:
        node = g_node[0]
        node_str = g_node[1]

        if node is entry_node or node is exit_node:
            #entry_exit_set.add(node)
            continue

        function = node.function
        contract = function.contract

        if contract not in grouped_nodes:
            grouped_nodes[contract] = {}

        if function not in grouped_nodes[contract]:
            grouped_nodes[contract][function] = set()

        grouped_nodes[contract][function].add(node_str)


    contract_sub_graphs = []

    for contract in grouped_nodes:
        contract_name = contract.name

        function_sub_graphs = []
        for function in grouped_nodes[contract]:
            graph_nodes = grouped_nodes[contract][function]
            full_function_sig = full_function_signature(function)
            function_sub_graphs.append((full_function_sig, graph_nodes))

        contract_sub_graphs.append((contract_name, function_sub_graphs))

    output_merged(filename, contract_sub_graphs, all_graph_edges)


def output_my_cfg_ssa_graph(contracts_graph, edge_instr, filename):

    if not generate_output_files:
        return

    graph_nodes, all_graph_edges = get_my_cfg_ssa_graph(contracts_graph, edge_instr)

    node_to_ssa = {}
    non_ssa_nodes = set()
    for g_node in graph_nodes:
        node = g_node[0]
        node_str = g_node[1]

        if node is entry_node or node is exit_node:
            continue

        if isinstance(node, Operation):
            if node.node not in node_to_ssa:
                node_to_ssa[node.node] = list()

            ir_ssa_sig_list = node_to_ssa[node.node]
            ir_ssa_sig_list.append(node_str)
        else:
            non_ssa_nodes.add(node)

    grouped_nodes = {}
    for node in node_to_ssa:

        if node is entry_node or node is exit_node:
            continue

        # in the special case where the node is an InternalCall, the function is that of the CALLED function.
        # the general behaviour is that the function is that of the CALLING function
        function = get_node_function(node)
        contract = function.contract

        if contract not in grouped_nodes:
            grouped_nodes[contract] = {}

        if function not in grouped_nodes[contract]:
            grouped_nodes[contract][function] = {}

        if node in grouped_nodes[contract][function]:
            assert False

        grouped_nodes[contract][function][node] = node_to_ssa[node]

    for node in non_ssa_nodes:
        if node is entry_node or node is exit_node:
            continue

        # in the special case where the node is an InternalCall, the function is that of the CALLED function.
        # the general behaviour is that the function is that of the CALLING function
        function = get_node_function(node)
        contract = function.contract

        if contract not in grouped_nodes:
            grouped_nodes[contract] = {}

        if function not in grouped_nodes[contract]:
            grouped_nodes[contract][function] = {}

        if node in grouped_nodes[contract][function]:
            assert False

        grouped_nodes[contract][function][node] = None
    # for g_node in graph_nodes:
    #     node = g_node[0]
    #
    #     if node is entry_node or node is exit_node:
    #         continue
    #
    #     # in the special case where the node is an InternalCall, the function is that of the CALLED function.
    #     # the general behaviour is that the function is that of the CALLING function
    #     function = get_node_function(node)
    #     contract = function.contract
    #
    #     if contract not in grouped_nodes:
    #         grouped_nodes[contract] = {}
    #
    #     if function not in grouped_nodes[contract]:
    #         grouped_nodes[contract][function] = {}
    #
    #     if isinstance(node, Operation):
    #         if node.node in grouped_nodes[contract][function]:
    #             assert True
    #         grouped_nodes[contract][function][node.node] = node_to_ssa[node.node]
    #     else:
    #         grouped_nodes[contract][function][node] = None

    contract_sub_graphs = []

    for contract in grouped_nodes:
        contract_name = contract.name

        function_sub_graphs = []
        for function in grouped_nodes[contract]:
            graph_nodes = grouped_nodes[contract][function]

            full_function_sig = full_function_signature(function)
            function_sub_graphs.append((full_function_sig, graph_nodes))

        contract_sub_graphs.append((contract_name, function_sub_graphs))

    output_ssa_merged(filename, contract_sub_graphs, all_graph_edges)





