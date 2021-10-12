from enum import IntEnum

from slither.core.cfg.node import NodeType
from slither.core.solidity_types import MappingType, ArrayType

from SolidityCodeInstrumenter import instr_placeholder_str
from cfg.my_cfg.entry_exit_nodes import exit_node, entry_node
from cfg.my_cfg.utils import get_key_from_edge
from cfg.utils import get_sorted, compose_full_node_id, get_children, get_non_ssa_node


class InstrumentationTypeEnum(IntEnum):
    other = 0
    init = 1
    edge_counter = 2
    back_edge = 3
    path_counter = 4
    path_flush = 4


# formatters
def instruments_format_with_semicolon_at_the_end(instruments):
    if len(instruments) == 0:
        return ''
    else:
        return ';'.join(instruments) + ';'


def instruments_format_end_of_statement_before_semicolon(instruments):
    if len(instruments) == 0:
        return ''
    else:
        return ';' + (';').join(instruments)


def instruments_format_empty_string_separated(instruments):
    return ''.join(instruments)


def instruments_format_inside_condition(instruments):
    try:
        if len(instruments) == 0:
            return ''
        else:
            str = '||'.join(instruments) + '||'
    except Exception as e:
       assert False

    return str


def get_instrumentation_location_before(node):
    if node is None:
        return None

    line = None
    col = None

    if node.type in [NodeType.ENTRYPOINT, NodeType.IFLOOP]:
        # should never get here
        assert False

    elif node.type in [NodeType.EXPRESSION, NodeType.IF, NodeType.RETURN, NodeType.CONTINUE, NodeType.BREAK, NodeType.THROW, NodeType.VARIABLE, NodeType.ASSEMBLY]:
        lines = node.source_mapping['lines']
        line = lines[0]
        col = node.source_mapping['starting_column']

    elif node.type in [NodeType.ENDIF, NodeType.ENDLOOP]:
        col = node.source_mapping['ending_column'] - 1
        lines = node.source_mapping['lines']
        line = lines[len(lines) - 1]

    # a loop usually consists of STARTLOOP (i=0) -> IFLOOP (i<x) -> ENDLOOP
    # before STARTLOOP will return the column before the start of the loop construct: for... while...
    # same as IFLOOP
    elif node.type == NodeType.STARTLOOP:
        lines = node.source_mapping['lines']
        line = lines[0]
        col = node.source_mapping['starting_column']

    # elif node.type == NodeType.ASSEMBLY:
    #     raise Exception('unknown scenario')

    else:
        raise Exception('unknown scenario')

    return line, col


def get_instrumentation_location_after(node):
    if node is None:
        return None

    line = None
    col = None

    if node.type in [NodeType.RETURN, NodeType.CONTINUE, NodeType.BREAK, NodeType.IF, NodeType.IFLOOP, NodeType.STARTLOOP]:
        # should never get here
        assert False

    elif node.type in [NodeType.EXPRESSION, NodeType.VARIABLE]:
        lines = node.source_mapping['lines']
        line = lines[0]
        col = node.source_mapping['ending_column']

    elif node.type == NodeType.ENTRYPOINT:
        lines = node.source_mapping['lines']
        line = lines[0]
        col = node.source_mapping['starting_column'] + 1

    elif node.type in [NodeType.ENDIF, NodeType.ENDLOOP, NodeType.ASSEMBLY]:
        lines = node.source_mapping['lines']
        line = lines[len(lines) - 1]
        col = node.source_mapping['ending_column']

    # elif node.type == NodeType.ASSEMBLY:
    #     raise Exception('unknown scenario')

    else:
        raise Exception('unknown scenario')

    return line, col


def get_code_instrumentation_location(e, graph, related_nodes_map):
    from_node = e.from_node
    to_node = e.to_node

    # print(from_node,to_node)

    line = None
    col = None
    instruments_formatter = None

    if to_node is exit_node:
        if from_node.type in [NodeType.RETURN, NodeType.THROW]:
            line, col = get_instrumentation_location_before(from_node)
            instruments_formatter = instruments_format_with_semicolon_at_the_end

        elif from_node.type in [NodeType.ENDIF, NodeType.ENDLOOP, NodeType.ENTRYPOINT, NodeType.ASSEMBLY]:
            line, col = get_instrumentation_location_after(from_node)
            instruments_formatter = instruments_format_with_semicolon_at_the_end

        elif from_node.type in [NodeType.EXPRESSION, NodeType.VARIABLE]:
            line, col = get_instrumentation_location_after(from_node)
            instruments_formatter = instruments_format_end_of_statement_before_semicolon

        else:
            raise Exception('unknown scenario')

    elif from_node is entry_node:
        if to_node.type in [NodeType.ENTRYPOINT]:
            line, col = get_instrumentation_location_after(to_node)
            instruments_formatter = instruments_format_with_semicolon_at_the_end

        elif to_node.type in [NodeType.ENDIF]:
            # edge case. happens on constructor variables initialization
            line, col = get_instrumentation_location_before(to_node)
            instruments_formatter = instruments_format_with_semicolon_at_the_end

        elif to_node.type in [NodeType.IF]:
            # edge case. happens on constructor variables initialization
            # todo - changed this so the instrumentation will not be inside the if condition from:
            # line, col = get_instrumentation_location_before(to_node)
            # instruments_formatter = instruments_format_before
            # todo - to:
            line, col = get_instrumentation_location_after(from_node)
            instruments_formatter = instruments_format_inside_condition

        elif to_node.type in [NodeType.EXPRESSION, NodeType.VARIABLE]:
            # edge case. happens on constructor variables initialization
            line, col = get_instrumentation_location_before(to_node)
            instruments_formatter = instruments_format_with_semicolon_at_the_end

        elif to_node.type in [NodeType.IFLOOP, NodeType.STARTLOOP]:
            # a loop usually consists of STARTLOOP (i=0) -> IFLOOP (i<x) -> ENDLOOP
            col, line, instruments_formatter = to_node_is_start_or_loop_condition(e, related_nodes_map)

        else:
            raise Exception('unknown scenario')

    elif from_node is not entry_node and to_node is not exit_node:
        if from_node.type == NodeType.IF:
            # the following scenario occures when the false if body is empty.
            # it relies on the preprocessing that ensures there is always a false if body to instrument:
            # if (a) {} is converted to if (a) {} else { }
            if to_node.type in [NodeType.ENDIF, NodeType.EXPRESSION, NodeType.RETURN, NodeType.VARIABLE, NodeType.THROW]:
                line, col = get_instrumentation_location_before(to_node)
                instruments_formatter = instruments_format_with_semicolon_at_the_end
            elif to_node.type in [NodeType.IF]:
                line, col = get_instrumentation_location_before(to_node)
                instruments_formatter = instruments_format_inside_condition
            elif to_node.type in [NodeType.ENTRYPOINT]:
                line, col = get_instrumentation_location_after(to_node)
                instruments_formatter = instruments_format_with_semicolon_at_the_end
            elif to_node.type in [NodeType.IFLOOP, NodeType.STARTLOOP]:
                # a loop usually consists of STARTLOOP (i=0) -> IFLOOP (i<x) -> ENDLOOP
                col, line, instruments_formatter = to_node_is_start_or_loop_condition(e, related_nodes_map)
            else:
                raise Exception('unknown scenario')

        elif from_node.type == NodeType.ENDIF:
            if to_node.type in [NodeType.ASSEMBLY, NodeType.EXPRESSION, NodeType.VARIABLE]:
                line, col = get_instrumentation_location_before(to_node)
                instruments_formatter = instruments_format_with_semicolon_at_the_end
            elif to_node.type in [NodeType.ASSEMBLY, NodeType.EXPRESSION, NodeType.VARIABLE, NodeType.IF, NodeType.RETURN, NodeType.ENDIF, NodeType.ENDLOOP]:
                line, col = get_instrumentation_location_after(from_node)
                instruments_formatter = instruments_format_with_semicolon_at_the_end
            elif to_node.type in [NodeType.IFLOOP, NodeType.STARTLOOP]:
                # a loop usually consists of STARTLOOP (i=0) -> IFLOOP (i<x) -> ENDLOOP
                col, line, instruments_formatter = to_node_is_start_or_loop_condition(e, related_nodes_map)
            else:
                raise Exception('unknown scenario')

        elif from_node.type in [NodeType.RETURN, NodeType.CONTINUE, NodeType.BREAK]:
            line, col = get_instrumentation_location_before(from_node)
            instruments_formatter = instruments_format_with_semicolon_at_the_end

        elif from_node.type == NodeType.IFLOOP:
            if to_node.type in [NodeType.IFLOOP, NodeType.STARTLOOP]:
                # a loop usually consists of STARTLOOP (i=0) -> IFLOOP (i<x) -> ENDLOOP
                col, line, instruments_formatter = to_node_is_start_or_loop_condition(e, related_nodes_map)
            elif to_node.type in [NodeType.ENDLOOP]:
                line, col = get_instrumentation_location_after(to_node)
                instruments_formatter = instruments_format_with_semicolon_at_the_end
            elif to_node.type in [NodeType.IF]:
                line, col = get_instrumentation_location_before(to_node)
                instruments_formatter = instruments_format_inside_condition
            elif to_node.type in [NodeType.EXPRESSION, NodeType.VARIABLE]:
                line, col = get_instrumentation_location_before(to_node)
                instruments_formatter = instruments_format_with_semicolon_at_the_end
            else:
                raise Exception('unknown scenario')

        elif from_node.type == NodeType.STARTLOOP:
            if to_node.type in [NodeType.IFLOOP, NodeType.STARTLOOP]:
                # a loop usually consists of STARTLOOP (i=0) -> IFLOOP (i<x) -> ENDLOOP
                col, line, instruments_formatter = to_node_is_start_or_loop_condition(e, related_nodes_map)
            elif to_node.type in [NodeType.ENDLOOP]:
                line, col = get_instrumentation_location_after(to_node)
                instruments_formatter = instruments_format_with_semicolon_at_the_end
            elif to_node.type in [NodeType.IF]:
                line, col = get_instrumentation_location_before(to_node)
                instruments_formatter = instruments_format_inside_condition
            elif to_node.type in [NodeType.EXPRESSION, NodeType.VARIABLE]:
                line, col = get_instrumentation_location_before(to_node)
                instruments_formatter = instruments_format_with_semicolon_at_the_end
            else:
                raise Exception('unknown scenario')

        elif from_node.type == NodeType.ENTRYPOINT:
            if to_node.type in [NodeType.IF, NodeType.EXPRESSION, NodeType.RETURN, NodeType.VARIABLE, NodeType.ASSEMBLY]:
                # todo - changed this so the instrumentation will not be inside the if condition from:
                # line, col = get_instrumentation_location_before(to_node)
                # instruments_formatter = instruments_format_before
                # todo - to:
                line, col = get_instrumentation_location_after(from_node)
                instruments_formatter = instruments_format_with_semicolon_at_the_end
            elif to_node.type in [NodeType.IFLOOP, NodeType.STARTLOOP]:
                # a loop usually consists of STARTLOOP (i=0) -> IFLOOP (i<x) -> ENDLOOP
                col, line, instruments_formatter = to_node_is_start_or_loop_condition(e, related_nodes_map)
            else:
                raise Exception('unknown scenario')

        elif from_node.type == NodeType.EXPRESSION:
            if to_node.type in [NodeType.ENTRYPOINT]:

                line, col = get_instrumentation_location_before(from_node)
                instruments_formatter = instruments_format_with_semicolon_at_the_end
            elif to_node.type in [NodeType.IF, NodeType.ENDIF, NodeType.ENDLOOP, NodeType.EXPRESSION,NodeType.RETURN, NodeType.VARIABLE]:
                line, col = get_instrumentation_location_after(from_node)
                instruments_formatter = instruments_format_end_of_statement_before_semicolon
            elif to_node.type in [NodeType.IFLOOP, NodeType.STARTLOOP]:
                # a loop usually consists of STARTLOOP (i=0) -> IFLOOP (i<x) -> ENDLOOP
                col, line, instruments_formatter = to_node_is_start_or_loop_condition(e, related_nodes_map)
            else:
                raise Exception('unknown scenario')

        elif from_node.type == NodeType.ENDLOOP:
            if to_node.type in [NodeType.ENDIF, NodeType.ENDLOOP]:
                line, col = get_instrumentation_location_after(from_node)
                instruments_formatter = instruments_format_with_semicolon_at_the_end
            elif to_node.type in [NodeType.IFLOOP, NodeType.STARTLOOP]:
                # a loop usually consists of STARTLOOP (i=0) -> IFLOOP (i<x) -> ENDLOOP
                col, line, instruments_formatter = to_node_is_start_or_loop_condition(e, related_nodes_map)
            elif to_node.type in [NodeType.RETURN, NodeType.CONTINUE, NodeType.BREAK, NodeType.EXPRESSION, NodeType.VARIABLE]:
                line, col = get_instrumentation_location_before(to_node)
                instruments_formatter = instruments_format_with_semicolon_at_the_end
            else:
                raise Exception('unknown scenario')

        elif from_node.type == NodeType.VARIABLE:
            if to_node.type in [NodeType.ENDIF, NodeType.ENDLOOP, NodeType.RETURN, NodeType.CONTINUE,
                                NodeType.BREAK, NodeType.EXPRESSION, NodeType.VARIABLE, NodeType.IF, NodeType.ENTRYPOINT]:
                line, col = get_instrumentation_location_after(from_node)
                instruments_formatter = instruments_format_end_of_statement_before_semicolon
            elif to_node.type in [NodeType.IFLOOP, NodeType.STARTLOOP]:
                # a loop usually consists of STARTLOOP (i=0) -> IFLOOP (i<x) -> ENDLOOP
                col, line, instruments_formatter = to_node_is_start_or_loop_condition(e, related_nodes_map)
            else:
                raise Exception('unknown scenario')

        # elif to_node.type in [NodeType.RETURN, NodeType.CONTINUE, NodeType.BREAK]:
        #     line, col = get_instrumentation_location_before(to_node)
        #     instruments_formatter = instruments_format_before



        # elif to_node.type in [NodeType.EXPRESSION, NodeType.VARIABLE]:
        #     line, col = get_instrumentation_location_before(to_node)
        #     instruments_formatter = instruments_format_before

        # elif to_node.type == NodeType.IF:
        #     # todo - changed this so the instrumentation will not be inside the if condition from:
        #     # line, col = get_instrumentation_location_before(to_node)
        #     # instruments_formatter = instruments_format_before
        #     # todo - to:
        #     if from_node.type in [NodeType.IF]:
        #         line, col = get_instrumentation_location_before(to_node)
        #         instruments_formatter = instruments_format_inside_condition
        #     elif from_node.type in [NodeType.VARIABLE]:
        #         line, col = get_instrumentation_location_after(from_node)
        #         instruments_formatter = instruments_format_after
        #     else:
        #         raise Exception('unhandled scenario')

        # elif to_node.type == NodeType.ENTRYPOINT:
        #     # callsite calls
        #     if from_node.type == NodeType.VARIABLE:
        #         # init variable with function call like in the case of a smart contract initialization with a constructor
        #         line, col = get_instrumentation_location_before(from_node)
        #         instruments_formatter = instruments_format_before
        #
        #     elif from_node.type == NodeType.EXPRESSION:
        #         # call a function without using its return value
        #         line, col = get_instrumentation_location_before(from_node)
        #         instruments_formatter = instruments_format_before
        #
        #     else:
        #         raise Exception('unhandled scenario')

        elif from_node.type == NodeType.VARIABLE:
            if to_node.type in [NodeType.ASSEMBLY]:
                line, col = get_instrumentation_location_after(from_node)
                instruments_formatter = instruments_format_with_semicolon_at_the_end
            elif to_node.type in [NodeType.IFLOOP, NodeType.STARTLOOP]:
                # a loop usually consists of STARTLOOP (i=0) -> IFLOOP (i<x) -> ENDLOOP
                col, line, instruments_formatter = to_node_is_start_or_loop_condition(e, related_nodes_map)
            else:
                raise Exception('unknown scenario')

        elif from_node.type in [NodeType.THROW, NodeType.CONTINUE, NodeType.BREAK, NodeType.RETURN]:
            line, col = get_instrumentation_location_before(from_node)
            instruments_formatter = instruments_format_with_semicolon_at_the_end

        else:
            raise Exception('unknown scenario')

    else:
        raise Exception('unknown scenario')

    return line, col, instruments_formatter


def to_node_is_start_or_loop_condition(e, related_nodes_map):
    to_node = e.to_node

    if to_node.type == NodeType.IFLOOP:
        start_loop_node = related_nodes_map['if_to_start_loop'][to_node]
    else:
        start_loop_node = to_node
    # scenario 1 - before the first loop. this scenario is identified by a non-backedge leading to IFLOOP.
    # need to instrument before the loop construct.
    if e._re_init is None:
        # end_loop_node = get_end_loop_node(to_node, graph)
        line, col = get_instrumentation_location_before(start_loop_node)
        instruments_formatter = instruments_format_with_semicolon_at_the_end

    # scenario 2 - before every consecutive loop. this scenario is identified by a backedge leading to IFLOOP.
    # need to implement before ENDLOOP
    else:
        # an increment inside a for loop. find the for loop end details for instrumentation
        # end_loop_node = get_end_loop_node(to_node, graph)

        end_loop_node = related_nodes_map['start_to_end_loop'][start_loop_node]

        line, col = get_instrumentation_location_before(end_loop_node)
        instruments_formatter = instruments_format_with_semicolon_at_the_end
    return col, line, instruments_formatter


def get_if_loop_node(to_node, graph):
    sons = get_children(to_node, graph)
    assert len(sons) < 3
    sorted_sons = get_sorted(sons)

    if_loop_node = None
    for s in sorted_sons:
        if s.type == NodeType.IFLOOP:
            if_loop_node = s
            break

    assert if_loop_node is not None

    return if_loop_node


def get_code_instrumentations(sol_instr, instrumented_edges, graph):
    related_nodes_map = get_related_nodes_map(graph)

    code_instrumentations = {}
    for e in instrumented_edges:

        edges_key = get_key_from_edge(e)

        if edges_key in code_instrumentations:
            # should not get here
            assert False

        instr_str = None
        inc_type = None
        node = None

        if e.from_node is entry_node:
            # instr_str = f'r = {inc}'
            assert e._init is not None and e._inc is None and e._re_init is None

            if e._init != 0:
                instr_str = [sol_instr.instr.get_solidity_init_all_transaction_data(e._init)]
                inc_type = InstrumentationTypeEnum.init
                contract = e.to_node.function.contract
                node = e.to_node

        elif e.to_node is exit_node:
            # instr_str = [f'path_counter[r + {inc}]++']
            assert e._init is None and e._inc is not None and e._re_init is None

            instr_str = [sol_instr.instr.get_solidity_inc_transaction_path_count_and_flush(e._inc)]
            inc_type = InstrumentationTypeEnum.path_counter
            contract = e.from_node.function.contract
            node = e.from_node

        else:
            assert e._init is None and e._inc is not None

            if e._re_init is not None:
                # instr_path_counter_str = f'path_counter[r + {inc}]++'
                instr_path_counter_inc_str = sol_instr.instr.get_solidity_inc_transaction_path_count_and_flush(e._inc)

                # instr_path_counter_reset_str = f'r = {reset}'
                instr_path_counter_reset_str = sol_instr.instr.get_solidity_reset_counter(e._re_init)

                instr_str = [instr_path_counter_inc_str, instr_path_counter_reset_str]
                inc_type = InstrumentationTypeEnum.back_edge
                contract = e.from_node.function.contract
                node = e.from_node

            else:
                if e._inc != 0:
                    # instr_str = f'r += {inc}'
                    instr_str = [sol_instr.instr.get_solidity_inc_counter(e._inc)]
                    inc_type = InstrumentationTypeEnum.edge_counter
                    contract = e.from_node.function.contract
                    node = e.from_node

        if instr_str is not None and len(instr_str) > 0:
            # line, col, instruments_formatter = get_instrumentation_details(e, graph)

            # todo if the to node is an if condition need to add the instrumentation after the from node
            # otherwise the instrumentation will be inserted inside the if statement before the if condition
            line, col, instruments_formatter = get_code_instrumentation_location(e, graph, related_nodes_map)

            formatted_instr_str = get_formatted_instr_str(instr_str, instruments_formatter)

            code_instrumentations[edges_key] = {
                'instrumentation': formatted_instr_str,
                'type': inc_type,
                'line': line,
                'col': col,
                'contract': contract,
                'node': node,
                #'instruments_formatter': instruments_formatter
            }

    return code_instrumentations


def get_related_nodes_map(graph):
    vertices = set()
    for e in graph:
        if e.to_node is entry_node or e.to_node is exit_node:
            continue
        vertices.add(e.to_node)

    related_nodes = {}
    for v in vertices:
        if v.type in [NodeType.STARTLOOP, NodeType.ENDLOOP]:
            non_ssa_node = get_non_ssa_node(v)
            lines = non_ssa_node.source_mapping['lines']
            contract_name = non_ssa_node.function.contract.name
            last_line = lines[len(lines) - 1]
            last_col = non_ssa_node.source_mapping['ending_column']
            key = (contract_name, last_line, last_col)
            if key not in related_nodes:
                related_nodes[key] = {
                    'start_loop': None,
                    'if_loop': None,
                    'end_loop': None,
                }
            if v.type == NodeType.STARTLOOP:
                assert related_nodes[key]['start_loop'] is None
                related_nodes[key]['start_loop'] = v

                if_loop_node = get_if_loop_node(v, graph)
                related_nodes[key]['if_loop'] = if_loop_node

            elif v.type == NodeType.ENDLOOP:
                assert related_nodes[key]['end_loop'] is None
                related_nodes[key]['end_loop'] = v

    related_nodes_map = {
        'start_to_end_loop': {},
        'end_to_start_loop': {},
        'start_to_if_loop': {},
        'if_to_start_loop': {},
    }

    for rn in related_nodes.values():
        start_loop = rn['start_loop']
        end_loop = rn['end_loop']
        if_loop = rn['if_loop']

        related_nodes_map['start_to_end_loop'][start_loop] = end_loop
        related_nodes_map['end_to_start_loop'][end_loop] = start_loop
        related_nodes_map['start_to_if_loop'][start_loop] = if_loop
        related_nodes_map['if_to_start_loop'][if_loop] = start_loop

    return related_nodes_map


def get_formatted_instr_str(instr_str, instruments_formatter):
    formatted_instr = instruments_formatter(instr_str)
    return formatted_instr


def add_path_counter_instrumentation_placeholder(node_instr, slither, added_instrumentation_id):
    contract_to_functions = get_contract_to_functions(slither)

    for item in contract_to_functions.items():
        contract = item[0]
        contract_functions = item[1]

        # contract should have functions
        if len(contract_functions) > 0:

            col, line = get_first_function_pos(contract_functions)

            # pick random function for full node id
            # f_node_id = full_node_id(contract.functions[0], added_instrumentation_id[0])
            f_node_id = compose_full_node_id(contract.functions[0], added_instrumentation_id[0])

        elif len(contract.state_variables) > 0:
            some_state_var = contract.state_variables[0]
            line = int(some_state_var.source_mapping['lines'][0])
            col = int(some_state_var.source_mapping['starting_column'])
            f_node_id = f'PathCounter#{added_instrumentation_id[0]}'
        else:
            raise Exception('unhandled scenario')

        added_instrumentation_id[0] = added_instrumentation_id[0] - 1

        if f_node_id in node_instr:
            assert False

        instrumentation_str = instr_placeholder_str

        formatted_instr_str = get_formatted_instr_str([instrumentation_str], instruments_format_with_semicolon_at_the_end)

        node_instr[f_node_id] = {
            # 'instrumentation': [instrumentation_str],
            'instrumentation': formatted_instr_str,
            'type': InstrumentationTypeEnum.other,
            'line': line,
            'col': col,
            'contract': contract,
            'node': None,
            # 'instruments_formatter': instruments_format_before
        }


def get_first_function_pos(contract_functions):
    sorted_contract_functions = get_sorted(contract_functions)
    first_contract_function = sorted_contract_functions[0]
    lines = first_contract_function.source_mapping['lines']
    line = lines[0]
    col = first_contract_function.source_mapping['starting_column']
    return col, line


def get_contract_to_functions(slither):
    contract_to_functions = {}
    for contract in slither.contracts:
        if contract not in contract_to_functions:
            contract_to_functions[contract] = list()

        for function in contract.functions:
            if function.is_constructor_variables:
                continue

            contract_to_functions[contract].append(function)
    return contract_to_functions


def add_additional_code_instrumentation(batch_id, slither):

    added_instrumentation_id = [-1]
    additional_code_instrumentation = {}

    # add_path_counter_contract_variable_instrumentation(additional_code_instrumentation, slither, added_instrumentation_id)
    add_path_counter_instrumentation_placeholder(additional_code_instrumentation, slither, added_instrumentation_id)

    # todo unremark
    # add_state_variables_getters_instrumentation(added_instrumentation_id, additional_code_instrumentation, slither)

    add_batch_id_getter_instrumentation(batch_id, additional_code_instrumentation, slither, added_instrumentation_id)

    return additional_code_instrumentation


def add_batch_id_getter_instrumentation(batch_id, node_instr, slither, added_instrumentation_id):
    contract_to_functions = get_contract_to_functions(slither)

    for item in contract_to_functions.items():
        contract = item[0]
        contract_functions = item[1]

        # contract should have functions
        if len(contract_functions) > 0:

            col, line = get_first_function_pos(contract_functions)

            # pick random function for full node id
            # f_node_id = full_node_id(contract.functions[0], added_instrumentation_id[0])
            f_node_id = compose_full_node_id(contract.functions[0], added_instrumentation_id[0])

        elif len(contract.state_variables) > 0:
            some_state_var = contract.state_variables[0]
            line = int(some_state_var.source_mapping['lines'][0])
            col = int(some_state_var.source_mapping['starting_column'])
            f_node_id = f'BatchIdentifier#{added_instrumentation_id[0]}'
        else:
            raise Exception('unhandled scenario')

        added_instrumentation_id[0] = added_instrumentation_id[0] - 1

        if f_node_id in node_instr:
            assert False

        instr_str = f'function get_batch_id() external view returns (uint256) {{ return {batch_id}; }}'
        instr_list = [instr_str]

        instrumentation_str = '\n' + '\n'.join(instr_list) + '\n' * 2

        formatted_instr_str = get_formatted_instr_str([instrumentation_str], instruments_format_empty_string_separated)

        node_instr[f_node_id] = {
            # 'instrumentation': [instrumentation_str],
            'instrumentation': formatted_instr_str,
            'type': InstrumentationTypeEnum.other,
            'line': line,
            'col': col,
            'contract': contract,
            'node': None,
            # 'instruments_formatter': instruments_format_before
        }


def add_state_variables_getters_instrumentation(added_instrumentation_id, node_instr, slither):
    contract_to_state_variables = {}
    for contract in slither.contracts:
        state_variables = contract.state_variables

        filtered_state_variables = set()
        for state_variable in state_variables:
            if isinstance(state_variable.type, MappingType):
                # todo check mapping
                #raise Exception("mapping type not supported yet")
                a=1

            filtered_state_variables.add(state_variable)

        contract_to_state_variables[contract] = filtered_state_variables

    for contract in slither.contracts:
        contract_state_vars = contract_to_state_variables[contract]
        if len(contract_state_vars) == 0:
            continue

        contract_state_vars = get_sorted(contract_state_vars)
        first_contract_state_var = contract_state_vars[0]

        lines = first_contract_state_var.source_mapping['lines']
        line = lines[0]
        col = first_contract_state_var.source_mapping['starting_column']

        # pick random function for full node id
        # f_node_id = full_node_id(contract.functions[0], added_instrumentation_id[0])
        f_node_id = compose_full_node_id(contract.functions[0], added_instrumentation_id[0])
        added_instrumentation_id[0] = added_instrumentation_id[0] - 1

        assert f_node_id not in node_instr

        instr_list = []
        for state_variable in contract_to_state_variables[contract]:
            return_type = None
            if isinstance(state_variable.type, MappingType) or isinstance(state_variable.type, ArrayType):
                return_type = f'{state_variable.type} memory'
            else:
                return_type = state_variable.type

            instr_str = f'function get_state_{state_variable.name}() external view returns ({return_type}) {{ return {state_variable.name}; }}'
            instr_list.append(instr_str)

        instrumentation_str = '\n' + '\n'.join(instr_list) + '\n' * 2

        formatted_instr_str = get_formatted_instr_str([instrumentation_str], instruments_format_empty_string_separated)

        node_instr[f_node_id] = {
            # 'instrumentation': [instrumentation_str],
            'instrumentation': formatted_instr_str,
            'type': InstrumentationTypeEnum.other,
            'line': line,
            'col': col,
            'contract': contract,
            'node': None,
            #'instruments_formatter': instruments_format_empty_string_separated
        }


def get_aggregated_instrumentation(code_instrumentation):
    instr_groups = {}
    for instr in code_instrumentation:
        contract = instr['contract']
        line = instr['line']
        col = instr['col']

        key = str(contract) + '_' + str(line) + '_' + str(col)
        instr_group = None
        if key not in instr_groups:
            instr_group = list()
            instr_groups[key] = instr_group
        else:
            instr_group = instr_groups[key]

        instr_group.append(instr)

    # in the case there are several instrumentations sort them by operational locations
    for instr_group in instr_groups.values():
        instr_group.sort(key=lambda t: int(t['type']), reverse=False)
        # instr_group_types = [instr['type'] for instr in instr_group]
        # if any(t is InstrumentationTypeEnum.path_flush for t in instr_group_types):
        #     pass

    code_instrumentation = list()
    for instr_group in instr_groups.values():

        agg_instrumentation = {
            'instr_group_line': instr_group[0]['line'],
            'instr_group_col': instr_group[0]['col'],
            'instr_group_contract': instr_group[0]['contract'],
            'aggregated_instrumentation': list(),
        }

        #assert all(x['instruments_formatter'] is instr_group[0]['instruments_formatter'] for x in instr_group)

        for instr in instr_group:
            agg_instrumentation['aggregated_instrumentation'].append(instr['instrumentation'])

        code_instrumentation.append(agg_instrumentation)

    for agg_instrumentation in code_instrumentation:
        aggregated_instrumentation = agg_instrumentation['aggregated_instrumentation']
        agg_instrumentation['aggregated_instrumentation'] = '\n'.join(aggregated_instrumentation)

    code_instrumentation.sort(key=(lambda t: (t['instr_group_line'], t['instr_group_col'])), reverse=False)
    return code_instrumentation
