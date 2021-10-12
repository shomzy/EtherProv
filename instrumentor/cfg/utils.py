import errno
import glob
import os
import sys

from slither.core.declarations import Contract, SolidityVariableComposed, SolidityVariable
from slither.core.source_mapping.source_mapping import SourceMapping
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.variable import Variable
from slither.slithir.operations import LibraryCall
from slither.slithir.operations.operation import Operation
from slither.slithir.variables import TemporaryVariable, StateIRVariable, TupleVariableSSA, LocalIRVariable, Constant
from slither.slithir.variables.variable import SlithIRVariable

from cfg.my_cfg.entry_exit_nodes import ENTRY_NODE_ID, EXIT_NODE_ID, entry_node, exit_node


def write_line_to_file(line_data, file_name, write_attr):
    write_to_file(file_name, write_attr, line_data+"\n")


def write_to_file(file_path, attribute, text):
    with open(file_path, attribute) as myfile:
        myfile.write(text)


def read_full_file(file_path):
    file_data = None
    with open(file_path, 'r') as file:
        file_data = file.read()
    return file_data


def append_line_to_file(file_path, text):
    with open(file_path, "a") as myfile:
        myfile.write(text + "\n")


def delete_directory_files(glob_path):
    files = glob.glob(glob_path)
    for f in files:
        os.remove(f)


def get_hash_of_list_items(list_):
    list_str = str(list_)
    hash_ = hash(list_str)
    return hash_
    #return str(list_)


def get_contract_state_variable_full_id(contract, state_var):
    return f'{contract.name}#{str(state_var.name)}'


def get_contract_full_id(contract):
    return f'{contract.name}'


def get_contract_full_function_parameter_id(function, parameter_name):
    return f'{full_function_signature(function)}#{parameter_name}'


def full_node_id(node) -> str:
    if node is entry_node:
        f_node_id = "ENTRY"
        return f_node_id
    elif node is exit_node:
        f_node_id = "EXIT"
        return f_node_id

    if isinstance(node, Operation):
        # function = node.node.function
        function = get_node_function(node.node)
        node_id = node.node.node_id
        for i in range(0, len(node.node.irs_ssa)):
            if node is node.node.irs_ssa[i]:
                composed = __compose_full_node_id(function, node_id)
                return f'{composed}#{i}'
        raise Exception('unhandled scenario')

    function = get_node_function(node)
    return compose_full_node_id(function, node.node_id)


def get_ssa_node_position(ssa_node):

    position = 0
    if isinstance(ssa_node, Operation):
        non_ssa_node = get_non_ssa_node(ssa_node)
        for i in range(0, len(non_ssa_node.irs_ssa)):
            if ssa_node is non_ssa_node.irs_ssa[i]:
                position = i
                break

    return position


def get_non_ssa_node(node):
    non_ssa_node = None
    if isinstance(node, Operation):
        non_ssa_node = node.node
    else:
        non_ssa_node = node
    return non_ssa_node


def full_variable_id(node, variable) -> str:
    if not isinstance(variable, (Variable, SolidityVariable, Contract)):
        raise Exception('unhandled scenario')

    variable_name = get_variable_unique_name(node, variable)

    contract_name = None
    if isinstance(variable, StateVariable):
        if isinstance(node, Contract):
            contract_name = node.name
        elif isinstance(node, Operation):
            contract_name = node.node.function.contract.name
        else:
            contract_name = node.function.contract.name

        if isinstance(variable, StateIRVariable):
            return f'{contract_name}#{variable_name}'
        #return variable.canonical_name
        return f'{contract_name}#{variable_name}'

    elif isinstance(node, Operation):
        contract_name = node.node.function.contract.name
    else:
        contract_name = node.function.contract.name

    if isinstance(node, Operation):
        return f'{contract_name}#{variable_name}'

    if isinstance(variable, SolidityVariableComposed):
        return variable_name

    #f_node_id = full_node_id(node)
    # line = variable.source_mapping['lines'][0]
    # col = variable.source_mapping['starting_column']
    #f_variable_id = f'{f_node_id}_{variable_name}_{line}_{col}'
    # f_variable_id = f'{contract_name}_{variable_name}_{line}_{col}'
    f_variable_id = f'{contract_name}#{variable_name}'
    return f_variable_id


def get_variable_unique_name(node, variable):
    if not isinstance(variable, (Variable, SolidityVariable, Contract)):
        assert False

    # if isinstance(variable, (SolidityVariableComposed)):
    #     x=3

    variable_name = None
    if isinstance(variable, Constant):
        pos = None
        if isinstance(node, Operation):
            for i in range(0, len(node.read)):
                if node.read[i] is variable:
                    pos = i
                    break
        # elif isinstance(node, SolidityCall):
        #     for i in range(0, len(node.arguments)):
        #         if node.arguments[i] is variable:
        #             pos = i
        #             break
        # elif isinstance(node, Operation):
        #     for i in range(0, len(node.variables)):
        #         if node.variables[i] is variable:
        #             pos = i
        #             break
        else:
            raise Exception('unhandled scenario')

        assert pos is not None
        variable_name = f'c#{variable.value}#{pos}'
    elif isinstance(variable, StateVariable):
        return variable.name
    elif isinstance(variable, SlithIRVariable):
        variable_name = variable.ssa_name
    elif isinstance(variable, TemporaryVariable):
        variable_name = variable.name
    elif isinstance(variable, Contract):
        # library call result assignment
        assert isinstance(node, LibraryCall)
        variable_name = f'LibraryCall#{full_function_signature(node.function)}'
    else:
        variable_name = variable.name

    if isinstance(variable, Contract):
        return variable_name

    if isinstance(variable, SourceMapping) and variable.source_mapping is not None:
        line = variable.source_mapping['lines'][0]
        col = variable.source_mapping['starting_column']
        variable_name = f'{variable_name}#{line}#{col}'
        return variable_name

    if isinstance(variable, (StateIRVariable, TupleVariableSSA, LocalIRVariable)):
        # TemporaryVariableSSA is not handled since its non_ssa_version is an ssa
        # ReferenceVariableSSA is not handled here since it doesnt have a source mapping
        assert variable.non_ssa_version is not None

        # can happen in Tuples
        # todo - need to support tuples
        if variable.non_ssa_version.source_mapping is None:
            assert False

        line = variable.non_ssa_version.source_mapping['lines'][0]
        col = variable.non_ssa_version.source_mapping['starting_column']
        variable_name = f'{variable_name}#{line}#{col}'
        return variable_name

    if isinstance(variable, SolidityVariableComposed):
        return variable_name

    if isinstance(variable, Constant):
        assert isinstance(node, Operation)

        line = node.node.source_mapping['lines'][0]
        col = node.node.source_mapping['starting_column']
        variable_name = f'{variable_name}#{line}#{col}'
        return variable_name

    if isinstance(variable, SolidityVariable) and variable.name in ["this","now"]:
        return variable.name

    f_function_sig = compose_function_signature_from_function(variable.function)
    variable_name = f'{f_function_sig}#{variable_name}'
    return variable_name


def get_variable_name(variable):
    if not isinstance(variable, (Variable, SolidityVariable, Contract)):
        assert False

    if variable_has_ssa_name(variable):
        return variable.ssa_name

    return variable.name


def variable_has_ssa_name(variable):
    if not isinstance(variable, (Variable, SolidityVariable, Contract)):
        assert False

    return isinstance(variable, (SlithIRVariable, StateIRVariable, LocalIRVariable))


def get_visibility(ssa_variable):
    visibility = None
    if isinstance(ssa_variable, Variable):
        visibility = ssa_variable.visibility
    return visibility


def get_is_const(ssa_variable):
    is_const = False
    if isinstance(ssa_variable, Constant):
        is_const = True
    # elif isinstance(ssa_variable, Variable):
    #     is_const = ssa_variable.is_constant

    return is_const


def get_is_storage(ssa_variable):
    is_storage = False
    if isinstance(ssa_variable, LocalVariable):
        is_storage = ssa_variable.is_storage
    elif isinstance(ssa_variable, StateVariable):
        is_storage = True
    return is_storage


def __compose_full_node_id(function, node_id) -> str:
    if function is None and node_id == ENTRY_NODE_ID:
        return 'ENTRY'
    if function is None and node_id == EXIT_NODE_ID:
        return 'EXIT'

    f_sig = full_function_signature(function)
    return f'{f_sig}#{node_id}'


def compose_full_node_id(function, node_id):
    composed = __compose_full_node_id(function, node_id)
    return f'{composed}#0'


# in the special case where the node is an ir_ssa call i.e. InternalCall, the function property points to the CALLED
# function. the general behavior is that the function is that of the CALLING function
def get_node_function(node):
    if isinstance(node, Operation):
        function = node.node.function
    else:
        function = node.function
    return function


def full_function_signature(function) -> str:
    function_name, parameters, _ = function.signature

    function_name = function_name.replace("slitherConstructorVariables", "constructor")
    sig = compose_full_function_signature(function.contract.name, function_name, parameters)

    # print (sig)
    return sig


def compose_full_function_signature(contract_name_str, function_name_str, parameters):
    sig = f'{contract_name_str}#{function_name_str}' + ('#' + '#'.join(parameters) if len(parameters) > 0 else '')
    return sig


def full_non_contract_function(f_name, args):
    sig = f'{f_name}' + '(' + (','.join(args) if len(args) > 0 else '') + ')'
    return sig


def compose_function_signature_from_function(function):
    function_name, parameters, _ = function.signature
    sig = f'{function_name}' + ('#' + '#'.join(parameters) if len(parameters) > 0 else '')
    return sig


def get_parents(node, graph) -> list:
    incoming_edges = get_incoming_edges(node, graph)

    parents = list()
    for e in incoming_edges:
        parents.append(e.from_node)

    return parents


def get_children(node, graph) -> list:
    outgoing_edges = get_outgoing_edges(node, graph)

    children = list()
    for e in outgoing_edges:
        children.append(e.to_node)

    return children


def get_incoming_edges(node, graph: list) -> list:
    incoming_edges = list()
    for e in graph:
        if e.to_node is node:
            incoming_edges.append(e)

    return incoming_edges


def get_outgoing_edges(node, graph: list) -> list:
    outgoing_edges = list()
    for e in graph:
        if e.from_node is node:
            outgoing_edges.append(e)

    # this will ensure the loop detection will be according to the code flow and not arbitrary, which can cause
    # incorrect instrumentation
    selector = lambda t: t.to_node
    sort_by_source_position(outgoing_edges, selector)

    return outgoing_edges


def get_entry(vertices, graph):
    for n in vertices:
        parents = get_parents(n, graph)
        if len(parents) == 0:
            return n
    raise Exception("No entry block for cfg")


def get_exit(vertices, graph):
    for n in vertices:
        children = get_children(n, graph)
        if len(children) == 0:
            return n
    raise Exception("No exit block for cfg")


def get_sorted(sons):
    sons_sorted = []
    for son in sons:
        pos = son.source_mapping['start'] + son.source_mapping['length']
        sons_sorted.append((pos, son))
    sons_sorted.sort(key=lambda t: t[0], reverse=False)
    sons_sorted = [v[1] for v in sons_sorted]
    return sons_sorted


def sort_by_source_position(l, node_selector):
    l.sort(key=lambda t: get_node_source_position(node_selector(t)), reverse=True)


def get_node_source_position(node):

    if isinstance(node, Operation):
        # should not get here since we are working on the consolidated graph
        assert False

        # node_node_pos = node.node.source_mapping['start'] + node.node.source_mapping['length']
        # irs_ssa_length = len(node.node.irs_ssa)
        # for i in range(0, irs_ssa_length):
        #     if node is node.node.irs_ssa[i]:
        #         node_node_pos_delta = i/irs_ssa_length
        #         return node_node_pos_delta + node_node_pos
        # raise Exception('unsupported scenario')
    else:
        if node.source_mapping is None:
            return sys.maxsize

        node_pos = node.source_mapping['start'] + node.source_mapping['length']
        return node_pos



