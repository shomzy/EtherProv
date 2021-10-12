from slither.core.cfg.node import NodeType
from slither.core.declarations import (Contract, Enum, Function,
                                       SolidityFunction, SolidityVariable,
                                       Structure, SolidityVariableComposed)
from slither.core.solidity_types.type import Type
from slither.slithir.operations import (HighLevelCall, LowLevelCall, Send,
                                        Transfer, NewContract, InternalCall, Operation, OperationWithLValue, Index,
                                        SolidityCall, Balance, Phi)
from slither.slithir.variables import (Constant, LocalIRVariable,
                                       ReferenceVariable, ReferenceVariableSSA,
                                       StateIRVariable,
                                       TemporaryVariableSSA, TupleVariableSSA)
from slither.utils.type import export_return_type_from_variable

from cfg.cfg_parser.state_variable_analyzer import extract_states_read_written
from cfg.my_cfg.entry_exit_nodes import entry_node, exit_node
from cfg.utils import full_function_signature, get_contract_state_variable_full_id, get_contract_full_id, full_node_id, \
    get_contract_full_function_parameter_id, \
    full_variable_id, \
    get_variable_name, get_is_storage, get_is_const, get_visibility
from souffle.souffle_relations import append_query_line_from_dic


def populate_static_ssa_non_contract_function_call(batch_id, slither, souffle_query_relations):
    # static_ssa_non_contract_function_call
    for contract in slither.contracts:

        if contract.is_interface:
            raise Exception('contract %s. interface is not supported yet' % (str(contract.name)))

        for function in contract.functions + contract.modifiers:
            # if function.is_constructor_variables:
            #     continue
            for node in function.nodes:
                for ir in node.irs_ssa:
                    function_name = None
                    if isinstance(ir, SolidityCall):
                        function_name = ir.function.name
                    elif isinstance(ir, LowLevelCall):
                        assert isinstance(ir.function_name, Constant)
                        function_name = ir.function_name.name
                    else:
                        continue

                    d = {
                        'batch_id': str(batch_id),
                        'static_ssa_node_id': full_node_id(ir),
                        'name': function_name
                    }
                    append_query_line_from_dic(d, 'static_ssa_non_contract_function_call', souffle_query_relations)


def populate_static_ssa_node(batch_id, contracts_ssa_graph_with_entry_exit, slither, souffle_query_relations):
    # static_ssa_node
    for contract in slither.contracts:

        if contract.is_interface:
            raise Exception('contract %s. interface is not supported yet' % (str(contract.name)))

        for function in contract.functions + contract.modifiers:
            # if function.is_constructor_variables:
            #     continue
            # x=3
            for node in function.nodes:
                if not node.irs_ssa:
                    add_static_ssa_node(batch_id, node, contracts_ssa_graph_with_entry_exit, souffle_query_relations)
                for ir in node.irs_ssa:
                    add_static_ssa_node(batch_id, ir, contracts_ssa_graph_with_entry_exit, souffle_query_relations)


def populate_static_path(batch_id, paths, souffle_query_relations):
    # static_path
    for path_item in paths.items():
        path_id = path_item[0]
        path = path_item[1]
        path_path = path['path']

        for e in path_path:
            d = {
                'batch_id': str(batch_id),
                'path_id': str(path_id),
                'static_edge_id': str(e.edge_id),
            }
            append_query_line_from_dic(d, 'static_path', souffle_query_relations)

    #extract_full_read_write_variables(paths, souffle_query_relations)

    populate_static_path_first_read_last_written_state_parameter(batch_id, paths, souffle_query_relations)


def populate_static_path_first_read_last_written_state_parameter(batch_id, paths, souffle_query_relations):
    # static_path_first_read_last_written_state_parameter
    running_id = 0
    for path_item in paths.items():
        path_id = path_item[0]
        path = path_item[1]

        path_path = path['path']
        first_read_states, last_write_states = path_first_read_last_write_states_extractor(path_path, entry_node,
                                                                                           exit_node)

        for v in first_read_states:
            d = {
                'batch_id': str(batch_id),
                'path_first_read_last_written_state_parameter_id': str(running_id),
                'static_path_id': str(path_id),
                'static_contract_state_parameter_id': get_contract_state_variable_full_id(v.contract, v),
                'first_read_or_last_written': 'first_read'
            }
            append_query_line_from_dic(d, 'static_path_first_read_last_written_state_parameter',
                                       souffle_query_relations)

            running_id = running_id + 1

        for v in last_write_states:
            d = {
                'batch_id': str(batch_id),
                'path_first_read_last_written_state_parameter_id': str(running_id),
                'static_path_id': str(path_id),
                'static_contract_state_parameter_id': get_contract_state_variable_full_id(v.contract, v),
                'first_read_or_last_written': 'last_written'
            }
            append_query_line_from_dic(d, 'static_path_first_read_last_written_state_parameter',
                                       souffle_query_relations)

            running_id = running_id + 1




def populate_static_edge(batch_id, consolidated_contracts, souffle_query_relations):
    # static_edge
    for e in consolidated_contracts.edges:
        from_static_node_id = full_node_id(e.from_node)
        to_static_node_id = full_node_id(e.to_node)

        d = {
            'batch_id': str(batch_id),
            'edge_id': str(e.edge_id),
            'from_static_node_id': from_static_node_id,
            'to_static_node_id': to_static_node_id,
        }
        append_query_line_from_dic(d, 'static_edge', souffle_query_relations)


def populate_static_ssa_edge(batch_id, contracts_ssa_graph_with_entry_exit, souffle_query_relations):
    for e in contracts_ssa_graph_with_entry_exit.edges:
        d = {
            'batch_id': str(batch_id),
            'ssa_edge_id': str(e.edge_id),
            'from_static_ssa_node_id': full_node_id(e.from_node),
            'to_static_ssa_node_id': full_node_id(e.to_node),
            'is_to_call_site': str(e._is_call_site),
            'related_to_call_site_edge_id': str(
                e._related_to_call_site_edge_id) if e._related_to_call_site_edge_id is not None else 'NULL'
        }
        append_query_line_from_dic(d, 'static_ssa_edge', souffle_query_relations)


def populate_static_ssa_variable_related(batch_id, slither, souffle_query_relations):
    # static_variable
    # static_ssa_node_variable
    # static_ssa_node_operation_with_l_value
    # static_ssa_node_index
    # static_ssa_function_return_variable
    # static_ssa_node_read_variable
    ssa_processed_variables = set()
    processed_variables = set()
    for contract in slither.contracts:

        if contract.is_interface:
            raise Exception('contract %s. interface is not supported yet' % (str(contract.name)))

        for function in contract.functions + contract.modifiers:
            # if function.is_constructor_variables:
            #     continue
            for node in function.nodes:
                for ir in node.irs_ssa:

                    if isinstance(ir, OperationWithLValue) and ir.lvalue:

                        # lvalue data
                        add_node_and_ssa_variable(batch_id, ir, ir.lvalue, ssa_processed_variables, processed_variables,
                                                  souffle_query_relations)

                        d = {
                            'batch_id': str(batch_id),
                            'static_ssa_node_id': full_node_id(ir),
                            'lvalue_static_ssa_node_variable_id': full_variable_id(ir, ir.lvalue),
                        }
                        append_query_line_from_dic(d, 'static_ssa_node_operation_with_l_value', souffle_query_relations)

                        if isinstance(ir.lvalue, ReferenceVariable):
                            if ir.lvalue.points_to:
                                # add_ssa_right_variables_data(ir.lvalue.points_to, ssa_processed_variables, processed_variables, souffle_query_relations)
                                add_node_and_ssa_variable(batch_id, ir, ir.lvalue.points_to, ssa_processed_variables,
                                                          processed_variables, souffle_query_relations)
                    add_ssa_right_variables_data(batch_id, ir, ssa_processed_variables, processed_variables,
                                                 souffle_query_relations)


def populate_static_node(batch_id, slither, souffle_query_relations):
    # static_node
    for contract in slither.contracts:

        if contract.is_interface:
            raise Exception('contract %s. interface is not supported yet' % (str(contract.name)))

        for function in contract.functions + contract.modifiers:

            # if function.is_constructor_variables:
            #     continue

            for node in function.nodes:
                d = {
                    # 'node_id': full_node_id(function, node.node_id),
                    'batch_id': str(batch_id),
                    'node_id': full_node_id(node),
                    'static_function_id': full_function_signature(function),
                    'type': str(node.type),
                    'expression': str(node.expression),
                    # 'static_true_branch_ssa_node_id': full_node_id(node.son_true) if node.son_true else 'NULL',
                    # 'static_false_branch_ssa_node_id': full_node_id(node.son_false) if node.son_true else 'NULL'
                }
                append_query_line_from_dic(d, 'static_node', souffle_query_relations)


def populate_static_function_parameter(batch_id, slither, souffle_query_relations):
    # static_function_parameter
    for contract in slither.contracts:

        if contract.is_interface:
            raise Exception('contract %s. interface is not supported yet' % (str(contract.name)))

        for function in contract.functions + contract.modifiers:

            if function.is_constructor_variables:
                continue

            if function.parameters:

                parameter_order_index = 0
                for parameter in function.parameters:
                    # return_types = [str(x.type) for x in function.returns]
                    # function_solidity_str = (" " * indent) + \
                    #                         ("function " if function.name != "constructor" else "") + str(function.name) + \
                    #                         "(" + ", ".join(parameters) + ") " + function.visibility + \
                    #                         (" view " if function.view else (" pure " if function.pure else " ")) + \
                    #                         ("returns (" + ", ".join(return_types) + ")" if len(return_types) > 0 else "") + \
                    #                         " {"

                    d = {
                        'batch_id': str(batch_id),
                        'function_parameter_id': get_contract_full_function_parameter_id(function, parameter.name),
                        'static_function_id': full_function_signature(function),
                        'order_index': str(parameter_order_index),
                        'solidity_type': str(parameter.type),
                        'name': parameter.name,
                    }
                    append_query_line_from_dic(d, 'static_function_parameter', souffle_query_relations)

                    parameter_order_index = parameter_order_index + 1


def populate_static_function(batch_id, slither, souffle_query_relations):
    # static_function
    for contract in slither.contracts:

        if contract.is_interface:
            raise Exception('contract %s. interface is not supported yet' % (str(contract.name)))

        for function in contract.functions + contract.modifiers:

            if function.is_constructor_variables:
                continue

            function_type = "regular"
            if function.name == "constructor":
                function_type = "constructor"

            static_entry_node_id = None
            for node in function.nodes:
                if node.node_id == 0:
                    # static_entry_node_id = full_node_id(function, node.node_id)
                    static_entry_node_id = full_node_id(node)
                    break

            if static_entry_node_id is None:
                assert False
                print('empty function: '+function.full_name + ' source_mapping: ' + function.source_mapping)
                continue

            d = {
                'batch_id': str(batch_id),
                'function_id': full_function_signature(function),
                'static_contract_id': get_contract_full_id(contract),
                'name': function.name,
                'type': function_type,
                'static_entry_node_id': static_entry_node_id,
                'is_payable': str(function.payable),
                'visibility': str(function.visibility)
            }
            append_query_line_from_dic(d, 'static_function', souffle_query_relations)


def populate_static_contract_state_parameter(batch_id, slither, souffle_query_relations):
    # static_contract_state_parameter
    for contract in slither.contracts:

        if contract.is_interface:
            raise Exception('contract %s. interface is not supported yet' % (str(contract.name)))

        for state_var in contract.state_variables_ordered:
            # state_var_str = " " * indent + str(state_var.type) + " " + str(state_var.visibility) + \
            #                 (" constant " if state_var.is_constant else " ") + str(state_var.name) + \
            #                 (" = " + str(state_var.expression) if state_var.initialized else "") + ";"

            d = {
                'batch_id': str(batch_id),
                'contract_state_parameter_id': full_variable_id(contract, state_var),
                'static_contract_id': get_contract_full_id(contract),
                'solidity_type': str(export_return_type_from_variable(state_var)),
                'name': state_var.name,
                'initial_value': str(state_var.expression) if state_var.initialized else 'NULL'
            }
            append_query_line_from_dic(d, 'static_contract_state_parameter', souffle_query_relations)


def populate_static_contract(batch_id, slither, souffle_query_relations):
    # static_contract
    for contract in slither.contracts:
        if contract.is_interface:
            raise Exception('contract %s. interface is not supported yet' % (str(contract.name)))

        d = {
            'batch_id': str(batch_id),
            'contract_id': get_contract_full_id(contract),
            'contract_name': contract.name,
            'is_signature_only': str(contract.is_signature_only())
        }
        append_query_line_from_dic(d, 'static_contract', souffle_query_relations)


def add_static_ssa_node(batch_id, ir, contracts_ssa_graph_with_entry_exit, souffle_query_relations):
    call_value = None
    static_node_id = None

    if isinstance(ir, Operation):
        if isinstance(ir, (Send, Transfer, HighLevelCall, LowLevelCall, NewContract)):
            if ir.call_value is not None:
                call_value = full_variable_id(ir, ir.call_value)
        static_node_id = full_node_id(ir.node)
    else:
        static_node_id = full_node_id(ir)

    # todo - consider removing is_true_branch, is_false_branch
    next_static_ssa_nodes = list()
    for e in contracts_ssa_graph_with_entry_exit.edges:
        if e.from_node is ir:
            if e._true_son:
                i = {
                    'to_node': e.to_node,
                    'is_true_branch': True,
                    'is_false_branch': False,
                }
                next_static_ssa_nodes.append(i)

            if e._false_son:
                i = {
                    'to_node': e.to_node,
                    'is_true_branch': False,
                    'is_false_branch': True,
                }
                next_static_ssa_nodes.append(i)

            if not e._true_son and not e._false_son:
                i = {
                    'to_node': e.to_node,
                    'is_true_branch': False,
                    'is_false_branch': False,
                }
                next_static_ssa_nodes.append(i)

    for i in next_static_ssa_nodes:
        to_node = i['to_node']
        next_static_ssa_node_id = full_node_id(to_node)
        is_true_branch = i['is_true_branch']
        is_false_branch = i['is_false_branch']

        d = {
            'batch_id': str(batch_id),
            'ssa_node_id': full_node_id(ir),
            'static_node_id': static_node_id,
            'type': type(ir).__name__,
            'expression': str(ir),
            'call_value': call_value if call_value is not None else 'NULL',
            'next_static_ssa_node_id': next_static_ssa_node_id,
            'is_true_branch': str(is_true_branch),
            'is_false_branch': str(is_false_branch)
        }
        append_query_line_from_dic(d, 'static_ssa_node', souffle_query_relations)


def path_first_read_last_write_states_extractor(path_path, entry, exit):
    # a should have at least ENTRY -> NodeType.ENTRY_NODE -> EXIT
    assert len(path_path) > 1

    first_read_states = set()
    last_write_states = set()

    for e in path_path:
        assert e.from_node is not exit
        if e.from_node is not entry:
            if e.from_node.type == NodeType.ENTRYPOINT:
                # ENTRYPOINT contains all accessed state_variables data in function
                continue

            state_variables_read, state_variables_written = get_node_read_write_states(e.from_node, entry, exit)
            if len(state_variables_read) == 0 and len(state_variables_written) == 0:
                continue

            update_first_read_last_written_states(state_variables_read, state_variables_written, first_read_states,
                                                  last_write_states)

    return first_read_states, last_write_states


def update_first_read_last_written_states(state_variables_read, state_variables_written, first_read_states,
                                          last_write_states):
    # intersec = state_variables_read.intersection(state_variables_written)
    # if len(intersec) > 1:
    #     raise Exception('we support only one state that is both written and read in the same node at most once')
    # elif len(intersec) == 1:
    #     # for example state1 = state1 + var
    #     for sv in intersec:
    #         if sv in first_read_states:
    #             # do nothing, state is read again
    #             pass
    #
    #         elif sv in last_write_states:
    #             # state was read after it was written with another value, do nothing
    #             pass
    #
    #         else:
    #             # new state read, record it
    #             first_read_states.add(sv)
    for sv in state_variables_read:
        if sv in first_read_states:
            # do nothing, state is read again
            pass

        elif sv in last_write_states:
            # state was read after it was written with another value, do nothing
            pass

        else:
            # new state read, record it
            first_read_states.add(sv)
    for sv in state_variables_written:
        if sv in first_read_states:
            # state was written after it was read, record it
            last_write_states.add(sv)

        elif sv in last_write_states:
            # state was rewritten do nothing
            pass

        else:
            # new state write, record it
            last_write_states.add(sv)


def get_node_read_write_states(node, entry, exit):
    state_variables_read = set()
    state_variables_written = set()

    if node is not entry and node is not exit:
        state_variables_read, state_variables_written = extract_states_read_written(node)
        state_variables_read = set(state_variables_read)
        state_variables_written = set(state_variables_written)

    return state_variables_read, state_variables_written


def add_node_and_ssa_variable(batch_id, ir, ssa_variable, ssa_processed_variables, processed_variables, souffle_query_relations):
    # if isinstance(ssa_variable, Constant):
    #     x=3

    variable = None
    if not isinstance(variable, SolidityVariableComposed) and can_convert_variable_to_non_ssa(ssa_variable):
        variable = ssa_variable.non_ssa_version
        variable_name = get_variable_name(variable)
        ssa_variable_name = get_variable_name(ssa_variable)
        if variable_name == ssa_variable_name:
            variable = None

    # variable = convert_variable_to_non_ssa(ssa_variable)
    # variable_name = get_variable_name(variable)
    # ssa_variable_name = get_variable_name(ssa_variable)
    # if variable_name == ssa_variable_name and not isinstance(variable, SolidityVariableComposed):

    if variable is not None:
        if isinstance(ssa_variable, Constant):
            assert False
        if variable not in processed_variables:
            processed_variables.add(variable)
            # f_variable_id = full_variable_id(ir.node, variable)
            # if f_variable_id not in processed_variables:
            #     add_node_variable(ir.node, variable, lvalue, souffle_query_relations)
            #     processed_variables.add(f_variable_id)
            add_node_variable(batch_id, ir, variable, ssa_variable, souffle_query_relations)

    if isinstance(ssa_variable, Constant):
        add_ssa_node_variable(batch_id, ir, ssa_variable, variable, souffle_query_relations)
    else:
        if ssa_variable not in ssa_processed_variables:
            ssa_processed_variables.add(ssa_variable)
            add_ssa_node_variable(batch_id, ir, ssa_variable, variable, souffle_query_relations)


def convert_variable_to_non_ssa(v):
    if isinstance(v, (LocalIRVariable, StateIRVariable, TemporaryVariableSSA, ReferenceVariableSSA, TupleVariableSSA)):
        return v.non_ssa_version
    assert isinstance(v, (Constant, SolidityVariable, Contract, Enum, SolidityFunction, Structure, Function, Type))
    return v


def can_convert_variable_to_non_ssa(v):
    if isinstance(v, (LocalIRVariable, StateIRVariable, TemporaryVariableSSA, ReferenceVariableSSA, TupleVariableSSA)):
        return True
    assert isinstance(v, (Constant, SolidityVariable, Contract, Enum, SolidityFunction, Structure, Function, Type))
    return False


def add_ssa_node_variable(batch_id, ir, ssa_variable, variable, souffle_query_relations):
    ssa_node_variable_id = full_variable_id(ir, ssa_variable)

    # if isinstance(ssa_variable, Constant):
    #     running_id = constant_to_running_id[ssa_variable.value]
    #     constant_to_running_id[ssa_variable.value] = constant_to_running_id[ssa_variable.value] + 1
    #     ssa_node_variable_id = f'{ssa_node_variable_id}_{running_id}'

    # if not isinstance(ir, Operation):
    #     assert False
    # f_function_sig = compose_function_signature_from_function(ir.function)
    # variable_name = f'{f_function_sig}_{variable_name}'
    # return variable_name

    f_node_variable_id = None
    if variable is not None:
        f_node_variable_id = full_variable_id(ir.node, variable)

    points_to_ssa_node_variable_id = None
    if isinstance(ssa_variable, ReferenceVariable):
        if isinstance(ir, Balance):
            contract_name = ir.node.function.contract.name
            points_to_ssa_node_variable_id = f'{contract_name}#this#balance'
        elif isinstance(ir, Phi):
            func_sig = full_function_signature(ir.node.function)
            points_to_ssa_node_variable_id = f'Phi#{func_sig}'
        else:
            points_to_ssa_node_variable_id = full_variable_id(ir, ssa_variable.points_to)

    is_storage = False
    is_const = False
    visibility = None

    # if not isinstance(ir, (Phi, PhiCallback)):
    is_storage = get_is_storage(ssa_variable)
    is_const = get_is_const(ssa_variable)
    visibility = get_visibility(ssa_variable)

    ssa_variable_name = get_variable_name(ssa_variable)

    # ssa_variable_left_ssa_node_variable_id = None
    # if isinstance(variable, Index):
    #     ssa_variable_left_ssa_node_variable_id = full_variable_id(ir, variable.variable_left)

    # is_call_value = False
    # if isinstance(ir, (Send, Transfer, HighLevelCall, LowLevelCall, NewContract)):
    #     if ir.call_value is ssa_variable:
    #         is_call_value = True

    d = {
        'batch_id': str(batch_id),
        'ssa_node_variable_id': ssa_node_variable_id,
        'static_node_variable_id': f_node_variable_id if f_node_variable_id is not None else 'NULL',
        'name': ssa_variable_name,
        'solidity_type': str(export_return_type_from_variable(ssa_variable)) if not isinstance(ssa_variable, (Contract)) else 'Function',
        'expression': str(ssa_variable),
        'points_to': points_to_ssa_node_variable_id if points_to_ssa_node_variable_id else 'NULL',
        'is_storage': str(is_storage),
        'is_const': str(is_const),
        'visibility': visibility if visibility else 'NULL',
        # 'is_call_value': str(is_call_value)
        # 'static_left_ssa_node_variable_id': ssa_variable_left_ssa_node_variable_id if ssa_variable_left_ssa_node_variable_id is not None else 'NULL',
    }
    append_query_line_from_dic(d, 'static_ssa_node_variable', souffle_query_relations)


def add_node_variable(batch_id, ir, variable, ssa_variable, souffle_query_relations):
    assert isinstance(ir, Operation)
    node = ir.node
    variable_id = full_variable_id(node, variable)

    is_storage = False
    is_const = False
    visibility = None

    # if not isinstance(ir, (Phi, PhiCallback)):
    is_storage = get_is_storage(ssa_variable)
    is_const = get_is_const(ssa_variable)
    visibility = get_visibility(ssa_variable)

    # ssa_variable_left_ssa_node_variable_id = None
    # if isinstance(variable, Index):
    #     ssa_variable_left_ssa_node_variable_id = full_variable_id(ir, variable.variable_left)

    d = {
        'batch_id': str(batch_id),
        'variable_id': variable_id,
        'static_contract_id': get_contract_full_id(node.function.contract),
        'static_function_id': full_function_signature(node.function),
        'name': variable.name,
        'solidity_type': str(export_return_type_from_variable(variable)),
        'is_storage': str(is_storage),
        'is_const': str(is_const),
        'visibility': visibility if visibility else 'NULL',
        'expression': str(variable),
    }
    append_query_line_from_dic(d, 'static_variable', souffle_query_relations)


def add_ssa_right_variables_data(batch_id, ir, ssa_processed_variables, processed_variables, souffle_query_relations):
    if isinstance(ir, Index):
        add_node_and_ssa_variable(batch_id, ir, ir.variable_left, ssa_processed_variables, processed_variables,
                                  souffle_query_relations)

        # variable_right = None
        # if not isinstance(ir.variable_right, Constant):
        add_node_and_ssa_variable(batch_id, ir, ir.variable_right, ssa_processed_variables, processed_variables,
                                  souffle_query_relations)
        variable_right = full_variable_id(ir, ir.variable_right)

        d = {
            'batch_id': str(batch_id),
            'static_ssa_node_id': full_node_id(ir),
            'variable_left_static_ssa_node_variable_id': full_variable_id(ir, ir.variable_left),
            'variable_right_static_ssa_node_variable_id': variable_right if variable_right else 'NULL',
        }
        append_query_line_from_dic(d, 'static_ssa_node_index', souffle_query_relations)

    elif isinstance(ir, InternalCall):
        function_return_variables_ssa = ir.function.return_values_ssa
        for i in range(0, len(function_return_variables_ssa)):
            f_return_var_ssa = function_return_variables_ssa[i]
            add_node_and_ssa_variable(batch_id, ir, f_return_var_ssa, ssa_processed_variables, processed_variables,
                                      souffle_query_relations)

            d = {
                'batch_id': str(batch_id),
                'static_ssa_node_id': full_node_id(ir),
                'static_ssa_node_variable_id': full_variable_id(ir, f_return_var_ssa),
                'order': str(i),
            }
            append_query_line_from_dic(d, 'static_ssa_function_return_variable', souffle_query_relations)

    # elif isinstance(ir, StateIRVariable):
    #     if ir not in ssa_processed_variables:
    #         ssa_processed_variables.add(ir)
    #         add_ssa_node_variable(ir, ir, None, souffle_query_relations)
    else:
        ssa_read_variables = ir.read
        for i in range(0, len(ssa_read_variables)):
            read_variable_ssa = ssa_read_variables[i]

            # if isinstance(read_variable_ssa, Constant):
            #     x = 3

            add_node_and_ssa_variable(batch_id, ir, read_variable_ssa, ssa_processed_variables, processed_variables,
                                      souffle_query_relations)

            d = {
                'batch_id': str(batch_id),
                'static_ssa_node_id': full_node_id(ir),
                'static_ssa_node_variable_id': full_variable_id(ir, read_variable_ssa),
                'order': str(i),
            }
            append_query_line_from_dic(d, 'static_ssa_node_read_variable', souffle_query_relations)
