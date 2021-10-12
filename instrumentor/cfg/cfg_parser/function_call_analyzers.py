import slither.slithir.convert as slithirConverter
from slither.slithir.operations import (InternalCall, HighLevelCall, InternalDynamicCall,
                                        LowLevelCall, NewContract, SolidityCall)

from cfg.utils import full_function_signature, compose_full_function_signature


def get_constructor_dest_in_out_extended(function_to_root_and_leaf_nodes, contract_name_str, function_name_str, args_strs) -> (str, str):
    #dst_f_sig = contract_name_str + '_' + function_name_str + ('_' + '_'.join(args_strs) if len(args_strs) > 0 else '')
    dst_f_sig = compose_full_function_signature(contract_name_str, function_name_str, args_strs)

    for item in function_to_root_and_leaf_nodes.items():
        function = item[0]
        item_dst_f_sig = full_function_signature(function)
        if item_dst_f_sig == dst_f_sig:
            root_and_leaves_nodes = item[1]
            return root_and_leaves_nodes

    raise Exception('unhandled scenario')


def get_call_site_root_and_leaves(ir, function_to_root_and_leaf_nodes, dest_full_function_sig):
    if isinstance(ir, (InternalCall, InternalDynamicCall, HighLevelCall, SolidityCall)):
        if ir.function not in function_to_root_and_leaf_nodes:
            assert False
        dest_full_function_sig.append(function_to_root_and_leaf_nodes[ir.function])
    elif isinstance(ir, NewContract):
        args = slithirConverter.convert_arguments(ir.arguments)
        args = [a[0] for a in args if a[0] != 'uint256']
        #args = [a for a in args]
        dest_full_function_sig.append(
            get_constructor_dest_in_out_extended(function_to_root_and_leaf_nodes,
                                                 str(ir.contract_name),
                                                 'constructor',
                                                 args))
    elif isinstance(ir, LowLevelCall):
        # do nothing for low level calls such as _receiver.call(ether_amount)
        # since this is not a call to a user function
        pass

        # args = slithirConverter.convert_arguments(ir.arguments)
        # args = [a[0] for a in args if len(a) > 0 and a[0] != 'uint256']
        # #args = [a for a in args]
        # dest_full_function_sig.append(
        #     get_constructor_dest_in_out_extended(function_to_root_and_leaf_nodes,
        #                                          str(ir.destination),
        #                                          str(ir.function_name),
        #                                          args))



