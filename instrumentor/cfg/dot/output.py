from cfg.utils import full_node_id


def output_merged(filename, contract_sub_graphs, all_edges):
    if not filename.endswith('.dot'):
        filename += '.dot'
    if filename == ".dot":
        filename = "all_contracts_merged.dot"

    sanitizied_edge = set()
    sanitized_function_names = set()

    for e in all_edges:
        check_sanitize_uniqueness(e, sanitizied_edge)

    with open(filename, 'w', encoding='utf8') as f:

        all_contracts_sub_graphs = []
        for contract_functions_sub_graphs in contract_sub_graphs:
            contract_name = contract_functions_sub_graphs[0]
            functions_sub_graphs = contract_functions_sub_graphs[1]

            contract_sub_graph = []
            for function_sub_graph in functions_sub_graphs:
                function_name = function_sub_graph[0]
                check_sanitize_uniqueness(function_name, sanitized_function_names)

                f_sub_graph = function_sub_graph[1]

                content = 'subgraph cluster_' + function_name + ' {\n' + \
                          'label = "[' + function_name + ']" \n' + \
                          '\n'.join(f_sub_graph) + \
                          '\n}'
                contract_sub_graph.append(content)

            content = 'subgraph cluster_' + contract_name + '  {\n' + \
                      'label = "[' + contract_name + ']" \n' + \
                      '\n'.join(contract_sub_graph) + \
                      '\n}'
            all_contracts_sub_graphs.append(content)

        content = 'strict digraph {\n' + \
                  '\n'.join(all_contracts_sub_graphs) + '\n' + \
                  '\n'.join(all_edges) + \
                  '\n}'

        content = sanitize_graph_string(content)
        f.write(content)


def output_ssa_merged(filename, contract_sub_graphs, all_edges):
    if not filename.endswith('.dot'):
        filename += '.dot'
    if filename == ".dot":
        filename = "all_contracts_merged.dot"

    sanitizied_edge = set()
    sanitized_nodes = set()
    sanitized_function_names = set()

    for e in all_edges:
        check_sanitize_uniqueness(e, sanitizied_edge)


    with open(filename, 'w', encoding='utf8') as f:

        all_contracts_sub_graphs = []
        for contract_functions_sub_graphs in contract_sub_graphs:
            contract_name = contract_functions_sub_graphs[0]
            functions_sub_graphs = contract_functions_sub_graphs[1]

            contract_sub_graph = []
            for function_sub_graph in functions_sub_graphs:
                function_name = function_sub_graph[0]
                check_sanitize_uniqueness(function_name, sanitized_function_names)

                f_sub_graph = function_sub_graph[1]

                nodes_sub_graph = []
                for node in f_sub_graph:
                    node_sig = full_node_id(node)
                    check_sanitize_uniqueness(node_sig, sanitized_nodes)

                    ir_ssa_sig_list = f_sub_graph[node]
                    if ir_ssa_sig_list is not None and len(ir_ssa_sig_list) > 0:

                        content = 'subgraph cluster_' + node_sig + ' {\n' + \
                                  'label = "[' + str(node) + ']" \n' + \
                                  '\n'.join(ir_ssa_sig_list) + \
                                  '\n}'
                    else:
                        lbl = node_sig + '\n' + str(node)
                        content = f'"{node_sig}" [label="{lbl}"];\n'
                    nodes_sub_graph.append(content)

                content = 'subgraph cluster_' + function_name + ' {\n' + \
                          'label = "[' + function_name + ']" \n' + \
                          '\n'.join(nodes_sub_graph) + \
                          '\n}'
                contract_sub_graph.append(content)

            content = 'subgraph cluster_' + contract_name + '  {\n' + \
                      'label = "[' + contract_name + ']" \n' + \
                      '\n'.join(contract_sub_graph) + \
                      '\n}'
            all_contracts_sub_graphs.append(content)

        content = 'strict digraph {\n' + \
                  '\n'.join(all_contracts_sub_graphs) + '\n' + \
                  '\n'.join(all_edges) + \
                  '\n}'

        content = sanitize_graph_string(content)
        f.write(content)


def check_sanitize_uniqueness(s, sanitized_set):
    sanitized_s = s.replace('#', '_')
    if sanitized_s in sanitized_set:
        raise SanitizeUniquenessException('sanitize uniqueness mismatch')
    sanitized_set.add(sanitized_s)


class SanitizeUniquenessException(Exception):
    pass


def sanitize_graph_string(s):
    s = s.replace('#', '_')
    return s


