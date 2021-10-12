from slither.core.variables.state_variable import StateVariable
from slither.slithir.operations import (Index, OperationWithLValue, PhiCallback, Phi,
                                        Member)
from slither.slithir.variables import (ReferenceVariable, LocalIRVariable, StateIRVariable)


def _convert_ssa(v):
    if isinstance(v, StateIRVariable):
        contract = v.contract
        non_ssa_var = contract.get_state_variable_from_name(v.name)
        return non_ssa_var
    assert isinstance(v, LocalIRVariable)
    function = v.function
    non_ssa_var = function.get_local_variable_from_name(v.name)
    return non_ssa_var


def extract_states_read_written(node):

   # only in expression
   # assert node.expression

    _ssa_vars_read = []
    _ssa_vars_written = []
    for ir in node.irs_ssa:
        if not is_slith_ir_variable(ir):
            continue

        extract_ssa_read_write_vars(ir, _ssa_vars_read, _ssa_vars_written)

    state_variables_read, state_variables_written = convert_read_write_vars(_ssa_vars_read, _ssa_vars_written)

    return state_variables_read, state_variables_written


def convert_read_write_vars(_ssa_vars_read, _ssa_vars_written):
    _ssa_vars_read = list(set(_ssa_vars_read))
    _ssa_state_vars_read = [v for v in _ssa_vars_read if isinstance(v, StateVariable)]
    # _ssa_local_vars_read = [v for v in _ssa_vars_read if isinstance(v, LocalVariable)]
    vars_read = [_convert_ssa(x) for x in _ssa_vars_read]
    _vars_read = [v for v in vars_read]
    _state_vars_read = [v for v in _vars_read if isinstance(v, StateVariable)]
    # _local_vars_read = [v for v in _vars_read if isinstance(v, LocalVariable)]
    _ssa_vars_written = list(set(_ssa_vars_written))
    _ssa_state_vars_written = [v for v in _ssa_vars_written if isinstance(v, StateVariable)]
    # _ssa_local_vars_written = [v for v in _ssa_vars_written if isinstance(v, LocalVariable)]
    vars_written = [_convert_ssa(x) for x in _ssa_vars_written]
    _vars_written = [v for v in vars_written]
    _state_vars_written = [v for v in _vars_written if isinstance(v, StateVariable)]
    # _local_vars_written = [v for v in _vars_written if isinstance(v, LocalVariable)]
    state_variables_read = [v for v in _state_vars_read]
    state_variables_written = [v for v in _state_vars_written]
    # print("state_variables_read: " + str(state_variables_read))
    # print("state_variables_written: " + str(state_variables_written))
    return state_variables_read, state_variables_written


def extract_ssa_read_write_vars(ir, _ssa_vars_read, _ssa_vars_written):
    if not isinstance(ir, (Phi, Index, Member)):
        _ssa_vars_read += [v for v in ir.read if isinstance(v, (StateIRVariable, LocalIRVariable))]
        for var in ir.read:
            if isinstance(var, (ReferenceVariable)):
                origin = var.points_to_origin
                if isinstance(origin, (StateIRVariable, LocalIRVariable)):
                    _ssa_vars_read.append(origin)

    elif isinstance(ir, (Member, Index)):
        if isinstance(ir.variable_right, (StateIRVariable, LocalIRVariable)):
            _ssa_vars_read.append(ir.variable_right)
        if isinstance(ir.variable_right, (ReferenceVariable)):
            origin = ir.variable_right.points_to_origin
            if isinstance(origin, (StateIRVariable, LocalIRVariable)):
                _ssa_vars_read.append(origin)
    if isinstance(ir, OperationWithLValue):
        var = ir.lvalue
        if isinstance(var, (ReferenceVariable)):
            var = var.points_to_origin
        # Only store non-slithIR variables
        if var and isinstance(var, (StateIRVariable, LocalIRVariable)):
            _ssa_vars_written.append(var)


def is_slith_ir_variable(ir):

    is_slith_ir_variable = True

    if isinstance(ir, (PhiCallback)):
        is_slith_ir_variable = False
    if isinstance(ir, OperationWithLValue):
        var = ir.lvalue
        if isinstance(var, (ReferenceVariable)):
            var = var.points_to_origin

        if var and isinstance(var, (StateIRVariable, LocalIRVariable)):
            if isinstance(ir, (PhiCallback)):
                is_slith_ir_variable = False

    return is_slith_ir_variable


