import json
import logging
import os
import pathlib
import shutil

from slither import Slither
from slither.core.declarations.function import FunctionType
from slither.slithir.operations import Operation, OperationWithLValue
from slither.slithir.variables import (TupleVariableSSA)
from web3 import Web3

from SolidityCodeInstrumenter import SolidityCodeInstrumenter
from cfg.cfg_parser.parseCFG import output_my_cfg_graph, get_contracts_graph, \
    get_contracts_ssa_graph, output_my_cfg_ssa_graph, get_consolidated_contracts, \
    get_call_site_calls_to_root_from_leaves_edges, CyclicReferenceException
from cfg.dot.output import SanitizeUniquenessException
from cfg.efficientPathProfiling import extract_efficient_path_profiling_incs, dfs_paths_extractor
from cfg.my_cfg.entry_exit_nodes import entry_node, exit_node
from cfg.my_cfg.instrumentation import write_instrumented_files
from cfg.my_cfg.instrumentation.preparation import add_additional_code_instrumentation, get_code_instrumentations, \
    get_aggregated_instrumentation
from cfg.my_cfg.instrumentation.source_code_injection import inject_code_instrumentation_to_source_code
from cfg.my_cfg.my_edge import MyEdge
from cfg.my_cfg.my_graph import MyGraphWithExitEntry, MyGraph
from cfg.my_cfg.utils import populate_reachable_nodes
from cfg.utils import write_to_file, get_node_function, full_node_id
from pre_processing import preprocess_contracts
from souffle.souffle_relations import get_souffle_query_relations_metadata
from static_analysis.graph_data_population import populate_static_contract, populate_static_contract_state_parameter, \
    populate_static_function, populate_static_function_parameter, populate_static_node, \
    populate_static_ssa_variable_related, populate_static_ssa_non_contract_function_call, populate_static_ssa_edge, \
    populate_static_ssa_node, populate_static_edge, populate_static_path
from utils import mkdir_p, parse_args, get_output_path, slitherfy_file

logging.basicConfig()
logging.getLogger("Slither").setLevel(logging.INFO)
logging.getLogger("Printers").setLevel(logging.INFO)


# mark dead code
def get_unreachable_nodes_from_entries(contracts_graph_with_entry_exit):
    reachable_nodes_from_entries = set()
    roots = contracts_graph_with_entry_exit.get_orphans_and_roots()

    for root in roots:

        if isinstance(root, Operation):
            root_node = root.node
        else:
            root_node = root

        if root_node.node_id == 0:
            reachable_nodes = set()
            populate_reachable_nodes(root, contracts_graph_with_entry_exit._edges, reachable_nodes)
            reachable_nodes_from_entries = reachable_nodes_from_entries.union(reachable_nodes)

    entry_exit_nodes_set = set()
    entry_exit_nodes_set.add(entry_node)
    entry_exit_nodes_set.add(exit_node)

    unreachable_nodes_from_entries = contracts_graph_with_entry_exit.vertices - reachable_nodes_from_entries - entry_exit_nodes_set

    return unreachable_nodes_from_entries


# mark dummy code
def get_contract_constructor_variables_nodes(contracts_graph_with_entry_exit):
    contructor_variables_nodes = set()

    for v in contracts_graph_with_entry_exit.vertices:
        if v is not entry_node and v is not exit_node:
            # function = v.function
            function = get_node_function(v)

            if function.is_constructor_variables:
                contructor_variables_nodes.add(v)

    return contructor_variables_nodes


def main():
    souffle_query_relations = get_souffle_query_relations_metadata()

    # create fresh souffle output files
    for r in souffle_query_relations:
        write_to_file(souffle_query_relations[r]['file_path'], 'w', '')

    work_dir = pathlib.Path().resolve()
    work_dir = f'{work_dir.parent}/{work_dir.name}'

    walk_dir_ = work_dir + "/instrumentor/contracts/other/temp/temp/contracts"
    # walk_dir_ = work_dir + "/instrumentor/contracts/other/temp/compiler_0.4.24/Runs/compiler_0.4.24_versioned/4/0.4.24/contracts"

    preprocessed_dir = walk_dir_ + "_preprocess/"
    not_supported_dir = walk_dir_ + "_not_supported/"
    path_counter_dir = work_dir + "/instrumentor/contracts/PathCounter/"
    # path_counter_path = f'{path_counter_dir}0.4.24/PathCounter.sol'

    ganache_url = "http://127.0.0.1:7546"
    web3 = Web3(Web3.HTTPProvider(ganache_url))
    web3.eth.defaultAccount = web3.eth.accounts[0]

    change_files_extension_to_sol(walk_dir_)

    process_not_supported(not_supported_dir, walk_dir_)

    preprocess(preprocessed_dir, not_supported_dir, walk_dir_)

    logs_dir = f'{walk_dir_}_logs'
    if not os.path.isdir(logs_dir):
        mkdir_p(logs_dir)

    preprocessed_walk_dir = preprocessed_dir

    print('walk_dir = ' + preprocessed_walk_dir)
    preprocessed_walk_dir = os.path.abspath(preprocessed_walk_dir)
    print('walk_dir (absolute) = ' + os.path.abspath(preprocessed_walk_dir))

    batch_id = 0
    log_ = {}
    for root, subdirs, files in os.walk(preprocessed_walk_dir):
        for filename in files:
            batch_id += 1
            file_name = os.path.join(root, filename)

            if file_name not in log_:
                log_[file_name] = {}

            log_file_name = log_[file_name]

            # if '0xc07f78bd412c53af2fabc56bbda107b718c6cd9d.Test' not in file_name:
            #     continue

            print('file_name = ' + file_name)

            # uninstrumented_dir = get_output_dir_ext_path(file_name, "_not_instrumented", preprocessed_walk_dir)
            # if os.path.isdir(uninstrumented_dir):
            #     continue
            #
            # mkdir_p(uninstrumented_dir)
            # uninstrumented_log_dir = f'{uninstrumented_dir}log_files'
            # mkdir_p(uninstrumented_log_dir)

            instr_dir = get_output_dir_ext_path(file_name, "_instrumented", preprocessed_walk_dir)
            if os.path.isdir(instr_dir):
                continue

            mkdir_p(instr_dir)
            mkdir_p(f'{instr_dir}/graphs')
            instr_sol_dir = f'{instr_dir}instrumented_sol'
            mkdir_p(instr_sol_dir)

            instr_contracts_details = {}
            try:
                slither = slitherfy_file(file_name)

                paths, sol_instr = process_contracts(batch_id, souffle_query_relations, slither, instr_dir,
                                                     path_counter_dir, instr_contracts_details)
                # process_path_counter_contract(instr_contracts_details, instr_sol_dir, web3)
                # path_counter_contract = get_path_counter_contract(instr_contracts_details, web3)

                # get all contracts' compile data from all instrumented sol files
                for _, _, fs in os.walk(instr_sol_dir):
                    for f in fs:
                        if f == 'PathCounter.sol':
                            continue

                        instr_sol_file = f'{instr_sol_dir}/{f}'

                        sol_instr.add_path_counter_logic_instrumentation(instr_sol_file)
                        # inject_path_counter_address(path_counter_contract.address, instr_sol_file)

                        slither_instr = slitherfy_file(instr_sol_file)
                        slither_uninstr = slitherfy_file(file_name)
                        for contract_name in slither_instr.crytic_compile.contracts_names:
                            if contract_name == 'PathCounter':
                                continue

                            if contract_name in instr_contracts_details:
                                if 'abi' in instr_contracts_details[contract_name] or 'bytecode' in \
                                        instr_contracts_details[contract_name]:
                                    # contract already processed
                                    continue
                            else:
                                raise DependentContractsException('unhandled scenario')

                            instr_contracts_details[contract_name]['abi'] = slither_instr.crytic_compile.abi(
                                contract_name)
                            instr_contracts_details[contract_name][
                                'bytecode'] = slither_instr.crytic_compile.bytecode_init(contract_name)

                            if contract_name not in log_file_name:
                                log_file_name[contract_name] = {
                                    'not_instr': {
                                        'runtime_byte_size': None,
                                        'constructor': None,
                                        'fallback': None,
                                        'functions': []
                                    },
                                    'instr': {
                                        'path_statements_contain_loop': sol_instr.path_statements_contain_loop,
                                        'runtime_byte_size': None,
                                        'constructor': None,
                                        'fallback': None,
                                        'functions': []
                                    }
                                }

                            log_contract = log_file_name[contract_name]

                            uninstr_bytecode_runtime = slither_uninstr.crytic_compile.bytecode_runtime(contract_name)
                            log_contract['not_instr']['runtime_byte_size'] = len(uninstr_bytecode_runtime)

                            instr_bytecode_runtime = slither_instr.crytic_compile.bytecode_runtime(contract_name)
                            log_contract['instr']['runtime_byte_size'] = len(instr_bytecode_runtime)

                            instr_contract_details = instr_contracts_details[contract_name]

                            # get constructor params from instr contract details
                            params_values = []
                            if instr_contract_details['constructor'] is not None:
                                params_values = get_params_values_('constructor',
                                                                   instr_contract_details['constructor']['params'],
                                                                   instr_contract_details, web3)

                            # deploy uninstr contract
                            uninstr_abi = slither_uninstr.crytic_compile.abi(contract_name)
                            uninstr_bytecode = slither_uninstr.crytic_compile.bytecode_init(contract_name)
                            uninstr_contract = web3.eth.contract(abi=uninstr_abi, bytecode=uninstr_bytecode)
                            tx_hash = uninstr_contract.constructor(*params_values).transact()
                            tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
                            uninstr_contractAddress = tx_receipt.contractAddress

                            log_contract['not_instr']['constructor'] = {
                                'err': None,
                                'gas': tx_receipt['gasUsed']
                            }

                            # deploy instr contract
                            instr_contract = web3.eth.contract(abi=instr_contract_details['abi'],
                                                               bytecode=instr_contract_details['bytecode'])
                            tx_hash = instr_contract.constructor(*params_values).transact()
                            tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)

                            log_contract['instr']['constructor'] = {
                                'err': None,
                                'gas': tx_receipt['gasUsed']
                            }

                            # if there is a constructor make sure events were generated
                            if instr_contract_details['constructor'] is not None:
                                # make sure constructor paths was generated
                                path_ids = extract_path_ids_from_log(instr_contract)
                                nodes, contains_loop = extract_paths_data(path_ids, paths)

                                if len(nodes) > 0:
                                    log_contract['not_instr']['constructor']['path_statements_count'] = len(nodes)
                                    log_contract['not_instr']['constructor']['contains_loop'] = contains_loop
                                else:
                                    log_contract['instr']['constructor']['gas'] = None
                                    log_contract['instr']['constructor']['err'] = 'no path generation'
                                    log_contract['not_instr']['constructor']['path_statements_count'] = None
                                    log_contract['not_instr']['constructor']['contains_loop'] = None

                            instr_contract_details['address'] = tx_receipt.contractAddress

                            instr_contract = web3.eth.contract(address=instr_contract_details['address'],
                                                               abi=instr_contract_details['abi'])
                            uninstr_contract = web3.eth.contract(address=uninstr_contractAddress, abi=uninstr_abi)

                            # run all callable functions in instrumented contract
                            for fun_details in instr_contract_details['functions']:
                                fun_name = fun_details['name']
                                # fun_params = fun_details['params']
                                # params_values = get_params_values_(fun_name, fun_params, instr_contract_details, web3)
                                execute_contract_command(uninstr_contract, instr_contract, instr_contract_details,
                                                         fun_name,
                                                         fun_details, instr_contract, paths, web3, log_contract)

                            if instr_contract_details['fallback'] is not None:
                                # params_values = get_params_values_('fallback', instr_contract_details['fallback']['params'], instr_contract_details, web3)
                                fun_details = instr_contract_details['fallback']
                                execute_contract_command(uninstr_contract, instr_contract, instr_contract_details,
                                                         'fallback',
                                                         fun_details, instr_contract, paths, web3, log_contract)


            except CyclicReferenceException as e:
                d_name = 'contains_cyclic_reference'
                handle_processing_error(d_name, file_name, instr_dir, log_, not_supported_dir, walk_dir_)
            except SanitizeUniquenessException as e:
                d_name = 'contains_sanitize_uniqueness_contraint'
                handle_processing_error(d_name, file_name, instr_dir, log_, not_supported_dir, walk_dir_)
            except DependentContractsException as e:
                d_name = 'contains_dependent_contracts'
                handle_processing_error(d_name, file_name, instr_dir, log_, not_supported_dir, walk_dir_)
            except ParameterTypeNotSupported as e:
                d_name = 'contains_unsupported_parameter_type'
                handle_processing_error(d_name, file_name, instr_dir, log_, not_supported_dir, walk_dir_)
            except Exception as e:
                if len(e.args) == 1:
                    if 'Invalid compilation' in e.args[0]:
                        d_name = 'invalid_compilation'
                        handle_processing_error(d_name, file_name, instr_dir, log_, not_supported_dir, walk_dir_)
                    elif 'time' in e.args[0]:
                        raise e
                    else:
                        d_name = 'other'
                        handle_processing_error(d_name, file_name, instr_dir, log_, not_supported_dir, walk_dir_)
                else:
                    d_name = 'other'
                    handle_processing_error(d_name, file_name, instr_dir, log_, not_supported_dir, walk_dir_)

    json_object = json.dumps(log_, indent=4)
    write_to_file(f'{logs_dir}/log.json', 'w', json_object)


def extract_paths_data(path_ids, paths):
    contains_loop = False
    nodes = set()
    for pid in path_ids:
        path_details = paths[pid]

        is_loop_path = path_details['is_loop_path']
        if is_loop_path:
            contains_loop = True

        for edge in path_details['path']:
            nodes.add(edge.from_node)
            nodes.add(edge.to_node)
    return nodes, contains_loop


def handle_processing_error(d_name, file_name, instr_dir, log_, not_supported_dir, walk_dir_):
    f = get_output_path(f'{walk_dir_}/', file_name)
    move_unsupported_file(f, not_supported_dir, d_name)
    os.remove(file_name)
    shutil.rmtree(instr_dir)
    del log_[file_name]


class DependentContractsException(Exception):
    pass


def execute_contract_command(uninstr_contract, instr_contract, instr_contract_details, fun_name, fun_details,
                             path_counter_contract, paths, web3, log_contract):
    params_values = get_params_values_(fun_name, fun_details['params'], instr_contract_details, web3)
    # statements_count = fun_details['uninstrumented_statements_count']
    # loops_count = fun_details['uninstrumented_loops_count']

    m_uninstr = get_contract_method(uninstr_contract, fun_name)
    m_uninstr = m_uninstr(*params_values)
    log_fun_uninstr = {
        'name': fun_name,
        'err': None,
        'gas': None,
        'path_statements_count': None,
        'contains_loop': None
    }

    m_instr = get_contract_method(instr_contract, fun_name)
    m_instr = m_instr(*params_values)
    log_fun_instr = {
        'name': fun_name,
        'err': None,
        'gas': None
    }

    if hasattr(m_uninstr, 'transact'):
        if not hasattr(m_instr, 'transact'):
            assert False

    if hasattr(m_instr, 'transact'):
        if not hasattr(m_uninstr, 'transact'):
            assert False

    if hasattr(m_uninstr, 'transact') and hasattr(m_instr, 'transact'):

        uninstr_exception = None
        try:
            log_fun_uninstr['gas'] = execute_method_transact(m_uninstr, web3)

        except Exception as e_uninstr:
            uninstr_exception = e_uninstr
            # log_fun_uninstr['err'] = 'unknown'

        instr_exception = None
        try:
            log_fun_instr['gas'] = execute_method_transact(m_instr, web3)

            path_ids = extract_path_ids_from_log(path_counter_contract)
            nodes, contains_loop = extract_paths_data(path_ids, paths)

            if len(nodes) > 0:
                log_fun_uninstr['path_statements_count'] = len(nodes)
                log_fun_uninstr['contains_loop'] = contains_loop
            else:
                log_fun_instr['gas'] = None
                log_fun_instr['err'] = 'no path generation'
                log_fun_uninstr['path_statements_count'] = None
                log_fun_uninstr['contains_loop'] = None

        except Exception as e_instr:
            instr_exception = e_instr
            # log_fun_instr['err'] = 'unknown'

        if uninstr_exception is None and uninstr_exception is None:
            # gas_inc_dif = (instr_gas_used - uninstr_gas_used) / uninstr_gas_used
            pass
        elif uninstr_exception is not None and uninstr_exception is None:
            raise Exception('unhandled scenario')
        elif uninstr_exception is None and uninstr_exception is not None:
            raise Exception('unhandled scenario')
        else:
            if len(uninstr_exception.args) != len(instr_exception.args):
                raise Exception('unhandled scenario')
            else:
                same_params = True
                for idx, val in enumerate(uninstr_exception.args):
                    if uninstr_exception.args[idx] != instr_exception.args[idx]:
                        same_params = False
                        break
                    else:
                        if uninstr_exception.args[
                            idx] == 'execution reverted: VM Exception while processing transaction: revert':
                            log_fun_uninstr['err'] = uninstr_exception.args[idx]
                            log_fun_instr['err'] = uninstr_exception.args[idx]
                        elif uninstr_exception.args[
                            idx] == 'execution reverted: VM Exception while processing transaction: invalid opcode':
                            log_fun_uninstr['err'] = uninstr_exception.args[idx]
                            log_fun_instr['err'] = uninstr_exception.args[idx]
                        else:
                            raise Exception('unsupported scenario')
                if not same_params:
                    raise Exception('unhandled scenario')

        log_contract['not_instr']['functions'].append(log_fun_uninstr)
        log_contract['instr']['functions'].append(log_fun_instr)


def execute_method_transact(m, web3):
    tx_hash = m.transact()
    tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
    gas_used = tx_receipt['gasUsed']
    return gas_used


def get_contract_method(contract, fun_name):
    if fun_name == 'fallback':
        if not hasattr(contract, fun_name):
            assert False
        m = getattr(contract, fun_name)
    elif fun_name == 'constructor':
        if not hasattr(contract, fun_name):
            assert False
        m = getattr(contract, fun_name)
    else:
        if not hasattr(contract.functions, fun_name):
            assert False
        m = getattr(contract.functions, fun_name)
    return m


def process_path_counter_contract(compiled_contracts, instr_sol_dir, web3):
    path_counter_target = f'{instr_sol_dir}/PathCounter.sol'
    slither = slitherfy_file(path_counter_target)
    assert len(slither.crytic_compile.contracts_names) == 1
    contract_name = slither.crytic_compile.contracts_names.pop()
    assert contract_name == 'PathCounter'
    abi = slither.crytic_compile.abi(contract_name)
    bytecode = slither.crytic_compile.bytecode_init(contract_name)
    contract = web3.eth.contract(abi=abi, bytecode=bytecode)
    tx_hash = contract.constructor().transact()
    tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
    path_counter_address = tx_receipt.contractAddress
    compiled_contracts[contract_name] = {
        'abi': abi,
        'bytecode': bytecode,
        'address': path_counter_address
    }


def get_params_values_(fun_name, params, compiled_contract, web3):
    # if fun_name == 'constructor':
    #     params = compiled_contract['constructor']['params']
    # elif fun_name == 'fallback':
    #     params = compiled_contract['fallback']['params']
    # else:
    #     found = False
    #     for f in compiled_contract['functions']:
    #         if f['name'] == fun_name:
    #             params = f['params']
    #             found = True
    #             break
    #     if not found:
    #         assert False

    abi = compiled_contract['abi']
    validate_abi_inputs(fun_name, params, abi)

    params_values = get_params_values(params, web3)
    return params_values


def get_params_values(params, web3):
    params_values = []
    if params is None:
        return params_values

    for p in params:
        t = p['type']
        if t == 'address':
            params_values.append(web3.eth.defaultAccount)
        elif t == 'address[]':
            params_values.append([web3.eth.defaultAccount])
        elif t == 'string':
            params_values.append('string_val')
        elif t == 'bytes':
            params_values.append(b'0x1')
        elif t == 'bytes16':
            params_values.append('0x1111')
        elif t == 'bytes32':
            params_values.append('0x11111111')
        elif t.startswith('uint') and '[' in t:
            params_values.append([1])
        elif t.startswith('uint'):
            params_values.append(1)
        elif t.startswith('int'):
            params_values.append(1)
        elif t.startswith('bool'):
            params_values.append(True)
        else:
            raise Exception('unsupported scenario')
    return params_values


class ParameterTypeNotSupported(Exception):
    pass


def validate_abi_inputs(fun_name, params, abi):
    inputs = None
    if fun_name == 'constructor':
        for a in abi:
            if a['type'] == 'constructor':
                inputs = a['inputs']
                same_params = is_parameters_equal(params, inputs)
                if not same_params:
                    # same function and params in contract
                    raise Exception('unhandled scenario')
                break

    elif fun_name == 'fallback':
        for a in abi:
            if a['type'] == 'fallback':
                inputs = []
                same_params = is_parameters_equal(params, inputs)
                if not same_params:
                    # same function and params in contract
                    raise Exception('unhandled scenario')
                break
    else:
        found = False
        for a in abi:
            if a['type'] == 'function' and a['name'] == fun_name:
                inputs = a['inputs']
                same_params = is_parameters_equal(params, inputs)
                if same_params:
                    # same function and params in contract
                    found = True
                    break
        if not found:
            raise Exception('unhandled scenario')
    return inputs


def get_path_counter_contract(compiled_contracts, web3):
    pcc = compiled_contracts['PathCounter']
    path_counter_contract = web3.eth.contract(
        address=pcc['address'],
        abi=pcc['abi'],
    )
    return path_counter_contract


def extract_path_ids_from_log(contract):
    path_ids = set()

    for contractEvent in contract.events:
        myfilter = contractEvent.createFilter(fromBlock="latest", toBlock="latest")
        eventlist = myfilter.get_all_entries()

        # if len(eventlist) != 0:
        #     found = True

        for event in eventlist:
            if event['event'] == '_pc_path':
                log = event['args']
                path = int(log['path_id'])
                path_ids.add(path)
    return path_ids


def move_unsupported_file(file_name, not_supported_dir, unsupported_reason):
    dir = f'{not_supported_dir}{unsupported_reason}/'
    mkdir_p(dir)
    output_file_name = get_output_path(dir, file_name)
    shutil.move(file_name, output_file_name)


def process_not_supported(not_supported_dir, walk_dir):
    mkdir_p(not_supported_dir)
    args = parse_args()
    for root, subdirs, files in os.walk(walk_dir):
        for filename in files:
            file_name = os.path.join(root, filename)

            # if '0xfa2400c873bf5e7243c5a5c40675868c4b7145ea' not in file_name:
            #     continue
            try:
                slither = Slither(file_name, is_truffle=os.path.isdir(file_name), solc=args.solc)

                for contract in slither.contracts:

                    if contract.is_interface:
                        dir = f'{not_supported_dir}contains_interface/'
                        mkdir_p(dir)
                        output_file_name = get_output_path(dir, file_name)
                        shutil.move(file_name, output_file_name)
                        break

                    if contract.kind == 'library':
                        dir = f'{not_supported_dir}contains_library/'
                        mkdir_p(dir)
                        output_file_name = get_output_path(dir, file_name)
                        shutil.move(file_name, output_file_name)
                        break

                    if len(contract.modifiers) > 0:
                        dir = f'{not_supported_dir}contains_modifier/'
                        mkdir_p(dir)
                        output_file_name = get_output_path(dir, file_name)
                        shutil.move(file_name, output_file_name)
                        break

                    should_break = False
                    for function in contract.functions:
                        if function.entry_point is None or function.is_empty:
                            dir = f'{not_supported_dir}contains_empty_functions/'
                            mkdir_p(dir)
                            output_file_name = get_output_path(dir, file_name)
                            shutil.move(file_name, output_file_name)
                            should_break = True
                            break

                        for node in function.nodes:
                            for ir in node.irs_ssa:
                                if isinstance(ir, OperationWithLValue):
                                    if isinstance(ir.lvalue, TupleVariableSSA):
                                        dir = f'{not_supported_dir}contains_tuples/'
                                        mkdir_p(dir)
                                        output_file_name = get_output_path(dir, file_name)
                                        shutil.move(file_name, output_file_name)
                                        should_break = True
                                        break

                            if should_break:
                                break

                        if should_break:
                            break

                    if should_break:
                        break
            except Exception as e:
                dir = f'{not_supported_dir}other/'
                mkdir_p(dir)
                output_file_name = get_output_path(dir, file_name)
                shutil.move(file_name, output_file_name)
                i = 2


def preprocess(preprocessed_dir, not_supported_dir, walk_dir):
    mkdir_p(preprocessed_dir)
    for root, subdirs, files in os.walk(walk_dir):
        for filename in files:

            # if '0x0a473605d21ac72ab6f942cd536dfb2776110de1.Americo' not in filename:
            #     continue

            file_name = os.path.join(root, filename)
            # file_name = "./instrumentor/contracts/other/10_contracts/^0.4.18/0x14e2ac9b6ca7bade21afdfa31b63708fc0b08d8f.KingOfTheHill/0x14e2ac9b6ca7bade21afdfa31b63708fc0b08d8f.KingOfTheHill.sol"
            print('file_name = ' + file_name)

            output_file = get_output_path(preprocessed_dir, file_name)

            if os.path.isfile(output_file):
                continue

            try:
                preprocess_contracts(file_name, preprocessed_dir)
            except Exception as e:
                move_unsupported_file(file_name, not_supported_dir, 'other')
                os.remove(output_file)
                i = 2


def change_files_extension_to_sol(walk_dir):
    for filename in os.listdir(walk_dir):
        infilename = os.path.join(walk_dir, filename)
        if not os.path.isfile(infilename): continue
        # oldbase = os.path.splitext(filename)
        newname = infilename.replace('.txt', '.sol')
        output = os.rename(infilename, newname)


def get_output_dir_ext_path(file_name, output_dir_ext, walk_dir):
    output_dir = walk_dir + output_dir_ext + "/"
    base = os.path.basename(file_name)
    f_name = os.path.splitext(base)[0]
    output_dir += f_name + '/'
    return output_dir


def process_contracts(batch_id, souffle_query_relations, slither, output_dir, path_counter_dir, compiled_contracts):
    populate_static_contract(batch_id, slither, souffle_query_relations)
    populate_static_contract_state_parameter(batch_id, slither, souffle_query_relations)
    populate_static_function(batch_id, slither, souffle_query_relations)
    populate_static_function_parameter(batch_id, slither, souffle_query_relations)
    populate_static_node(batch_id, slither, souffle_query_relations)
    populate_static_ssa_variable_related(batch_id, slither, souffle_query_relations)
    populate_static_ssa_non_contract_function_call(batch_id, slither, souffle_query_relations)

    contracts_graph = get_contracts_graph(slither.contracts)
    output_my_cfg_graph(contracts_graph, edge_instr=None,
                        filename=f'{output_dir}/graphs/1_all_contracts.dot')

    # simple_efficient_path_profiling_example(contracts_graph)
    # return

    contracts_ssa_graph = get_contracts_ssa_graph(slither.contracts)
    output_my_cfg_ssa_graph(contracts_ssa_graph, edge_instr=None,
                            filename=f'{output_dir}/graphs/2_all_ssa_contracts.dot')

    contracts_graph_with_entry_exit = contracts_graph.get_new_graph_with_connected_entry_exit_nodes()
    output_my_cfg_graph(contracts_graph_with_entry_exit, edge_instr=None,
                        filename=f'{output_dir}/graphs/3_all_contracts_with_entry_exit.dot')

    contracts_ssa_graph_with_entry_exit = contracts_ssa_graph.get_new_graph_with_connected_entry_exit_nodes()
    output_my_cfg_ssa_graph(contracts_ssa_graph_with_entry_exit, edge_instr=None,
                            filename=f'{output_dir}/graphs/4_all_ssa_contracts_with_entry_exit.dot')

    to_from_call_site_edges = get_call_site_calls_to_root_from_leaves_edges(contracts_ssa_graph_with_entry_exit)
    vertices = contracts_ssa_graph_with_entry_exit.vertices
    ssa_edges_with_call_site_calls = contracts_ssa_graph_with_entry_exit.edges.union(to_from_call_site_edges)
    extended_contracts_ssa_graph_with_entry_exit = MyGraphWithExitEntry(vertices, ssa_edges_with_call_site_calls)
    extended_contracts_ssa_graph_with_entry_exit.reset_entry_exit_node_connections()
    output_my_cfg_ssa_graph(extended_contracts_ssa_graph_with_entry_exit, edge_instr=None,
                            filename=f'{output_dir}/graphs/5_all_ssa_contracts_extended_with_exit_node.dot')

    populate_static_ssa_edge(batch_id, extended_contracts_ssa_graph_with_entry_exit, souffle_query_relations)
    populate_static_ssa_node(batch_id, contracts_ssa_graph_with_entry_exit, slither, souffle_query_relations)

    # validate_functions_visibility(contracts_ssa_graph_with_entry_exit, compiled_contracts)
    extract_contract_callable_functions(contracts_ssa_graph_with_entry_exit, compiled_contracts)

    consolidated_graph = get_consolidated_contracts(contracts_ssa_graph_with_entry_exit)
    output_my_cfg_graph(consolidated_graph, edge_instr=None,
                        filename=f'{output_dir}/graphs/6_consolidated_contracts_with_exit_node.dot')

    consolidated_contracts = remove_unreachable_nodes_and_edges(consolidated_graph)
    output_my_cfg_graph(consolidated_contracts, edge_instr=None,
                        filename=f'{output_dir}/graphs/7_consolidated_contracts_with_exit_node_unreachable_nodes_removed.dot')

    populate_static_edge(batch_id, consolidated_contracts, souffle_query_relations)

    back_edges, g_minus_back_plus_loop, incs = extract_efficient_path_profiling_incs(consolidated_contracts)

    paths = {}
    dfs_paths_extractor(entry_node, g_minus_back_plus_loop, back_edges, incs, 0, paths, [])

    sol_instr = SolidityCodeInstrumenter(paths, slither, path_counter_dir)

    # consolidate_dummy_edges_instrumentation(incs)

    instrumented_edges = update_graph_with_incs(incs, consolidated_contracts)
    code_instrumentations = get_code_instrumentations(sol_instr, instrumented_edges, consolidated_contracts.edges)
    output_my_cfg_graph(consolidated_contracts, edge_instr=code_instrumentations,
                        filename=f'{output_dir}/graphs/8_contracts_with_instrumentation.dot')

    additional_code_instrumentation = add_additional_code_instrumentation(batch_id, slither)

    code_instrumentation = list()
    code_instrumentation.extend(additional_code_instrumentation.values())
    code_instrumentation.extend(code_instrumentations.values())

    aggregated_code_instrumentation = get_aggregated_instrumentation(code_instrumentation)

    contract_src = inject_code_instrumentation_to_source_code(aggregated_code_instrumentation, slither)

    instrumented_sol_dir = f'{output_dir}instrumented_sol/'
    write_instrumented_files(contract_src, instrumented_sol_dir)

    sol_instr.copy_path_counter_path(instrumented_sol_dir)

    populate_static_path(batch_id, paths, souffle_query_relations)

    # for pragma in slither.pragma_directives:
    #     filename = pragma.source_mapping['filename_short'].split('/')[-1]
    #     contract_name = filename.split(".")[0]
    #     contract_name_to_pragmas[contract_name].append(str(pragma) + ";")

    return paths, sol_instr


def simple_efficient_path_profiling_example(contracts_graph):
    vertices = list()
    for v in contracts_graph.vertices:
        vertices.append(v)
    edges = list()
    edges.append(MyEdge(vertices[0], vertices[1]))
    edges.append(MyEdge(vertices[1], vertices[2]))
    edges.append(MyEdge(vertices[2], vertices[1]))
    edges.append(MyEdge(vertices[1], vertices[3]))
    vertices = vertices[0:4]
    myGraph = MyGraph(set(vertices), set(edges))
    myGraph = myGraph.get_new_graph_with_connected_entry_exit_nodes()
    output_my_cfg_ssa_graph(myGraph, edge_instr=None,
                            filename="2_all_ssa_contracts.dot")
    back_edges, g_minus_back_plus_loop, incs = extract_efficient_path_profiling_incs(myGraph)


def update_graph_with_incs(incs, consolidated_contracts):
    instrumented_edges = set()

    for item in incs.items():
        e = item[0]

        if e.from_node is entry_node and e.to_node is exit_node:
            continue

        inc = item[1]

        if e.from_node is entry_node:
            if e.back_edge_entry_mapping is not None:
                # assert e.back_edge_exit_mapping is None
                e.back_edge_entry_mapping._re_init = inc
            else:
                e._init = inc
        elif e.to_node is exit_node:
            if e.back_edge_exit_mapping is not None:
                # assert e.back_edge_entry_mapping is None
                e.back_edge_exit_mapping._inc = inc
            else:
                e._inc = inc
        else:
            if inc != 0:
                e._inc = inc

    print("instrumented edges")
    for e in consolidated_contracts.edges:
        if e.is_instrumented():
            if e._init is not None:
                assert e._re_init is None
            if e._init is None:
                assert e._re_init is not None or e._inc is not None
            if e._init is not None:
                assert e._inc is None
            if e._init is None:
                assert e._inc is not None
            if e._re_init is not None:
                assert e._inc is not None

            instrumented_edges.add(e)
            print(full_node_id(e.from_node), "-", full_node_id(e.to_node))
            print(f'\t\te._init: {e._init}; e._re_init: {e._re_init}; e._inc: {e._inc};')

    return instrumented_edges


def remove_unreachable_nodes_and_edges(extended_contracts_graph_with_entry_exit):
    unreachable_nodes_from_entries = get_unreachable_nodes_from_entries(extended_contracts_graph_with_entry_exit)
    constructor_variables_nodes = get_contract_constructor_variables_nodes(extended_contracts_graph_with_entry_exit)

    entry_exit_nodes = set()
    entry_exit_nodes.add(entry_node)
    entry_exit_nodes.add(exit_node)

    all_unreachable_nodes = unreachable_nodes_from_entries.union(constructor_variables_nodes).union(entry_exit_nodes)

    reachable_vertices = set()
    reachable_edges = set()
    for v in extended_contracts_graph_with_entry_exit.vertices:
        if v in all_unreachable_nodes:
            continue
        reachable_vertices.add(v)
    for e in extended_contracts_graph_with_entry_exit.edges:
        if e.from_node in all_unreachable_nodes or e.to_node in all_unreachable_nodes:
            continue
        reachable_edges.add(e)
    mg = MyGraph(reachable_vertices, reachable_edges)
    extended_contracts_graph_with_entry_exit = mg.get_new_graph_with_connected_entry_exit_nodes()
    return extended_contracts_graph_with_entry_exit


def extract_contract_callable_functions(graph_with_entry_exit, compiled_contracts):
    orphans_and_roots = graph_with_entry_exit.get_orphans_and_roots()

    # make sure the contracts we are going to handle don't have the same name as already processed contracts
    for v in orphans_and_roots:
        function = get_node_function(v)
        contract = function.contract
        if contract.name in compiled_contracts:
            assert False

    contract_details = None
    for v in orphans_and_roots:
        function = get_node_function(v)

        if function.visibility in ['private', 'internal']:
            # this are not accessible from outside the contract
            continue

        contract = function.contract

        if function.is_constructor_variables:
            continue

        if contract.name not in compiled_contracts:
            compiled_contracts[contract.name] = {'constructor': None, 'fallback': None, 'functions': []}

        contract_details = compiled_contracts[contract.name]

        if function.function_type == FunctionType.CONSTRUCTOR or function.name == "constructor":

            if contract_details['constructor'] is not None:
                # should have a single constructor
                assert False

            params = extract_function_parameters(function)

            # loops_count = 0
            # statements_count = 0
            # for n in function.nodes:
            #     statements_count = statements_count + 1
            #     if n.type == NodeType.STARTLOOP:
            #         loops_count = loops_count + 1

            contract_details['constructor'] = {
                'params': params,
                # 'uninstrumented_statements_count': statements_count,
                # 'uninstrumented_loops_count': loops_count
            }

        elif function.name == 'fallback':

            if contract_details['fallback'] is not None:
                # should have a single fallback
                assert False

            params = extract_function_parameters(function)

            # loops_count = 0
            # statements_count = 0
            # for n in function.nodes:
            #     statements_count = statements_count + 1
            #     if n.type == NodeType.STARTLOOP:
            #         loops_count = loops_count + 1

            contract_details['fallback'] = {
                'params': params,
                # 'uninstrumented_statements_count': statements_count,
                # 'uninstrumented_loops_count': loops_count
            }

        else:

            contract_functions = contract_details['functions']
            params = extract_function_parameters(function)

            for fun_details in contract_functions:

                if fun_details['name'] == function.name:
                    ps = fun_details['params']

                    same_params = is_parameters_equal(params, ps)
                    if not same_params:
                        # same function and params in contract
                        assert False

            # loops_count = 0
            # statements_count = 0
            # for n in function.nodes:
            #     statements_count = statements_count + 1
            #     if n.type == NodeType.STARTLOOP:
            #         loops_count = loops_count + 1

            fun_details = {
                'name': function.name,
                'params': params,
                # 'uninstrumented_statements_count': statements_count,
                # 'uninstrumented_loops_count': loops_count
            }
            contract_functions.append(fun_details)

        # if function.visibility == 'public':
        #     raise Exception(f'function {full_function_signature(function)} should be with EXTERNAL/INTERNAL/PRIVATE visibility only')

        # compiled_contracts[contract.name] = contract_details


def is_parameters_equal(ps1, ps2):
    same_params = False
    if ps1 is None and ps2 is None:
        same_params = True
    elif ps1 is not None and ps2 is None:
        same_params = False
    elif ps1 is None and ps2 is not None:
        same_params = False
    else:  # len(ps2) == len(ps1):
        same_params = True
        for idx, val in enumerate(ps2):
            if not (ps2[idx]['name'] == ps1[idx]['name'] and ps2[idx]['type'] == ps1[idx]['type']):
                same_params = False
                break

    return same_params


def extract_function_parameters(function):
    params = []
    if function.parameters:
        for parameter in function.parameters:
            params.append({'name': parameter.name, 'type': str(parameter.type)})
            # return_types = [str(x.type) for x in function.returns]
            # function_solidity_str = (" " * indent) + \
            #                         ("function " if function.name != "constructor" else "") + str(function.name) + \
            #                         "(" + ", ".join(parameters) + ") " + function.visibility + \
            #                         (" view " if function.view else (" pure " if function.pure else " ")) + \
            #                         ("returns (" + ", ".join(return_types) + ")" if len(return_types) > 0 else "") + \
            #                         " {"
            # d = {
            #     'batch_id': str(batch_id),
            #     'function_parameter_id': get_contract_full_function_parameter_id(function, parameter.name),
            #     'static_function_id': full_function_signature(function),
            #     'order_index': str(parameter_order_index),
            #     'solidity_type': str(parameter.type),
            #     'name': parameter.name,
            # }
    return params


main()
