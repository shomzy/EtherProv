import os
import re

from slither import Slither
from slither.core.expressions import CallExpression
from slither.slithir.operations import SolidityCall, LowLevelCall, HighLevelCall, InternalCall
from slither.slithir.variables import Constant

from cfg.utils import write_to_file, write_line_to_file
from utils import parse_args, get_output_path, extract_src_details


def extract_for_loop_changes(node, source_code, changes):

    start_for, _ = extract_src_details(node['src'])
    start_for_body, len_for_body = extract_src_details(node['body']['src'])

    src = source_code[start_for:start_for_body + len_for_body]
    for_src = extract_src(node['src'], source_code)
    for_body_src = extract_src(node['body']['src'], source_code)

    for_header_len = start_for_body - start_for
    changes.append({
        'op': 'sub',
        'pos': start_for,
        'len': for_header_len
    })

    if node['initializationExpression'] is None:
        init_src = ''
    else:
        init_src = extract_src(node['initializationExpression']['src'], source_code)
        init_src = f'\n{init_src};'
    cond_src = extract_src(node['condition']['src'], source_code)

    loop_exp_src = None
    if node['loopExpression'] is not None:
        loop_exp_src = extract_src(node['loopExpression']['src'], source_code)

    changes.append({
        'op': 'add',
        'pos': start_for,
        'str': f'{init_src}\nwhile ({cond_src})'
    })

    for_body_node_type = node['body']['nodeType']
    if for_body_node_type in ['ExpressionStatement', 'IfStatement']:
        end_for_body = start_for_body + len_for_body
        changes.append({
            'op': 'add',
            'pos': start_for_body,
            'str': f'{{\n'
        })

        if loop_exp_src is not None:
            changes.append({
                'op': 'add',
                'pos': end_for_body + 1,
                'str': f'\n{loop_exp_src};\n}}'
            })

        # str = f'\n{init_src};\nwhile ({cond_src}) {{\n {for_body_src};\n{loop_exp_src};\n}}'
    elif for_body_node_type == 'Block':
        end_for_body = start_for_body + len_for_body

        # changes.append({
        #     'op': 'sub',
        #     'pos': end_for_body,
        #     'len': 1
        # })

        if loop_exp_src is not None:
            changes.append({
                'op': 'add',
                'pos': end_for_body - 1,
                'str': f'\n{loop_exp_src};\n'
            })

        # str = f'\n{init_src};\nwhile ({cond_src}) {for_body_src}\n{loop_exp_src};\n}}'
    else:
        raise Exception('unhandled scenario')







def extract_src(exp_src, source_code):
    start, len = extract_src_details(exp_src)
    src = source_code[start:start + len]
    return src





def extract_if_statement_changes(node, source_code, changes):
    true_body = node['trueBody']
    if true_body['nodeType'] in ['Block']:
        # do nothing
        pass
    elif true_body['nodeType'] in ['ExpressionStatement', 'Throw', 'Return', 'VariableDeclarationStatement',
                                   'InlineAssembly', 'IfStatement', 'Continue', 'Break', 'EmitStatement']:
        start_true_body, len_true_body = extract_src_details(true_body['src'])
        extract_full_if_body(start_true_body, len_true_body, source_code, changes)
    else:
        raise Exception('unhandled scenario')

    false_body = node['falseBody']
    if false_body is not None:
        if false_body['nodeType'] in ['ExpressionStatement', 'Throw', 'Return', 'VariableDeclarationStatement', 'EmitStatement']:
            start_false_body, len_false_body = extract_src_details(false_body['src'])
            extract_full_if_body(start_false_body, len_false_body, source_code, changes)
        elif 'condition' in false_body:
            return
        elif false_body['nodeType'] == 'Block':
            return
        else:
            raise Exception('unhandled scenario')
    else:
        start_if, len_if = extract_src_details(node['src'])
        src = source_code[start_if:start_if + len_if]

        end_if_body = start_if + len_if + 1
        changes.append({
            'op': 'add',
            'pos': end_if_body,
            'str': f' else {{\n\n}}\n'
        })


def extract_full_if_body(start_body, len_body, source_code, changes):
    true_body_src = source_code[start_body:start_body + len_body + 1]
    changes.append({
        'op': 'sub',
        'pos': start_body,
        'len': len_body + 1
    })
    changes.append({
        'op': 'add',
        'pos': start_body,
        'str': f'{{\n{true_body_src}\n}}'
    })


def extract_function_defenition_changes(node, source_code, changes):
    state_mutability = node['stateMutability']
    if state_mutability in ['view', 'constant', 'pure']:
        start_fun, len_fun = extract_src_details(node['src'])
        src = source_code[start_fun:start_fun + len_fun]


        matches = re.finditer(r"\s*(view|constant|pure)\s*", src)
        # for m in matches:
        #     i=2
        #     i=3
        l = [(m.start(1), m.end(1)) for m in matches]
        if len(l) != 1:
            raise Exception('should not get here')

        view_start = l[0][0]
        len_view = l[0][1] - view_start
        view_src = source_code[start_fun + view_start:start_fun + view_start + len_view]

        changes.append({
            'op': 'sub',
            'pos': start_fun + view_start,
            'len': len_view
        })
    elif state_mutability in ['nonpayable', 'payable']:
        pass
    else:
        raise Exception('unhadled scenario')


def refactor_constructs(i, source_code, changes):
    if type(i) == dict:
        if 'nodeType' in i:
            if i['nodeType'] == 'ForStatement':
                extract_for_loop_changes(i, source_code, changes)
            elif i['nodeType'] == 'IfStatement':
                extract_if_statement_changes(i, source_code, changes)
            elif i['nodeType'] == 'FunctionDefinition':
                extract_function_defenition_changes(i, source_code, changes)
        for k in i:
            v = i[k]
            refactor_constructs(v, source_code, changes)

    if type(i) == list:
        for ii in i:
            refactor_constructs(ii, source_code, changes)


def preprocess_contracts(file_name, output_dir):

    output_file_name = replace_tabs_with_spaces(file_name, output_dir)
    # file_name = replace_tabs_with_spaces(file_name, output_dir)

    args = parse_args()
    slither = Slither(output_file_name, is_truffle=os.path.isdir(output_file_name), solc=args.solc)

    changes = []
    for source_file in slither.crytic_compile.asts:
        ast = slither.crytic_compile.asts[source_file]
        source_code = slither.crytic_compile.src_content_for_file(source_file)

        refactor_constructs(ast, source_code, changes)
        update_src_with_changes(changes, output_dir, source_code, source_file)

    # seperate_multiple_called_functions(slither, output_dir)


def replace_tabs_with_spaces(file_name, output_dir):
    file_data = None
    with open(file_name, 'r') as file:
        file_data = file.read()
    file_data = re.sub(r'\t', ' ', file_data)
    output_file_name = get_output_path(output_dir, file_name)
    write_to_file(output_file_name, 'w', file_data)
    return output_file_name


def update_src_with_changes(grouped_changes, output_dir, source_code, source_file):

    d = {}
    for change in grouped_changes:
        pos = change['pos']
        if pos not in d:
            d[pos] = {'add': [], 'sub': []}

        if 'add' in change['op']:
            d[pos]['add'].append(change)
        else:
            d[pos]['sub'].append(change)

    grouped_changes = []
    for i in d.items():
        grouped_changes.append({
            'pos': i[0],
            'val': i[1]
        })

    grouped_changes = sorted(grouped_changes, key=lambda i: i['pos'], reverse=False)

    src_len = len(source_code)
    pos = 0
    updated_src = ''
    while (pos < src_len):
        if len(grouped_changes) == 0:
            break

        changes = grouped_changes.pop(0)
        changes_pos = changes['pos']
        # assert pos < changes_pos
        updated_src = updated_src + source_code[pos:changes_pos]
        pos = changes_pos
        changes_val = changes['val']

        sub_changes = changes_val['sub']
        if len(sub_changes) > 0:
            lens = [c['len'] for c in sub_changes]
            max_len = max(lens)
            pos = pos + max_len

        add_changes = changes_val['add']
        while len(add_changes) > 0:
            add_change = add_changes.pop(0)
            updated_src = updated_src + add_change['str']

    if pos < src_len:
        updated_src = updated_src + source_code[pos:src_len]

    output_file_name = get_output_path(output_dir, source_file)
    write_line_to_file(updated_src, output_file_name, 'w')


def seperate_multiple_called_functions(slither, output_dir):
    src_path_to_instrs = {}
    get_src_path_to_instrs(slither, src_path_to_instrs)
    # for each path in src_path_to_instrs sort instruments by pos ascending and merge same positions by \n\n
    sort_and_merge_instrs(src_path_to_instrs)
    src_path_to_instrs_code = {}
    get_src_path_to_instrs_code(slither, src_path_to_instrs, src_path_to_instrs_code)
    for item in src_path_to_instrs_code.items():
        src_path = item[0]
        src_code = item[1]
        output_src_path = get_output_path(output_dir, src_path)
        write_to_file(output_src_path, 'w', src_code)


def get_src_path_to_instrs(slither, src_path_to_instrs):

    called_contracts = {}
    get_function_calls_details(called_contracts, slither)

    populate_called_functions_instr_at_destination(called_contracts, src_path_to_instrs, slither)
    populate_function_calls_instr_at_source(called_contracts, src_path_to_instrs)


def populate_function_calls_instr_at_source(called_contracts, src_path_to_instrs):
    for item in called_contracts.items():
        called_contract = item[0]
        called_funcs = item[1]

        duplicate_funcs = []
        for called_items in called_funcs.items():
            called_func = called_items[0]
            callers = called_items[1]

            if len(callers) > 1:
                count = -1
                for caller in callers:
                    count = count + 1
                    if count == 0:
                        continue

                    start_pos = caller.called.source_mapping["start"]
                    length = caller.called.source_mapping["length"]
                    injection_pos = start_pos + length

                    contract_file_name = called_contract.source_mapping['filename_used']

                    if contract_file_name not in src_path_to_instrs:
                        src_path_to_instrs[contract_file_name] = []

                    instr = {
                        "pos": injection_pos,
                        "instr": f'_{count}'
                    }
                    src_path_to_instrs[contract_file_name].append(instr)


def get_function_calls_details(called_contracts, slither):
    for contract in slither.contracts:
        if contract.is_interface:
            raise Exception('contract %s. interface is not supported yet' % (str(contract.name)))

        for function in contract.functions + contract.modifiers:
            if function.is_constructor_variables:
                continue

            for node in function.nodes:
                for ir in node.irs_ssa:
                    function_name = None
                    if isinstance(ir, SolidityCall):
                        function_name = ir.function.name
                    elif isinstance(ir, LowLevelCall):
                        assert isinstance(ir.function_name, Constant)
                        function_name = ir.function_name.name
                    # elif isinstance(ir, InternalCall):
                    #     assert True
                    elif isinstance(ir, (HighLevelCall, InternalCall)):

                        called_contract = ir.function.contract
                        if called_contract not in called_contracts:
                            called_contracts[called_contract] = {}

                        called_func = ir.function
                        if called_func not in called_contracts[called_contract]:
                            called_contracts[called_contract][ir.function] = set()

                        exp = ir.expression
                        assert isinstance(exp, CallExpression)
                        called_contracts[ir.function.contract][called_func].add(exp)
                    else:
                        continue


def populate_called_functions_instr_at_destination(called_contracts, src_path_to_instrs, slither):
    for item in called_contracts.items():
        called_contract = item[0]
        called_funcs = item[1]

        duplicate_funcs = []
        for called_items in called_funcs.items():
            called_func = called_items[0]
            callers = called_items[1]

            if len(callers) > 1:
                contract_file_name = called_contract.source_mapping['filename_used']
                called_contract_src_code = slither.crytic_compile.src_content[contract_file_name]
                start_pos = called_func.source_mapping["start"]
                length = called_func.source_mapping["length"]
                func_src = called_contract_src_code[start_pos:start_pos + length]

                func_prefix = f'function {called_func.name}'

                counter = -1
                for caller in callers:
                    counter = counter + 1
                    if counter == 0:
                        continue

                    duplicate_func = re.sub(f'^{func_prefix}', f'{func_prefix}_{counter}', func_src)
                    duplicate_funcs.append(duplicate_func)

                duplicate_funcs_str = '\n' + '\n\n'.join(duplicate_funcs) + '\n'
                start_pos = called_contract.source_mapping["start"]
                length = called_contract.source_mapping["length"]
                injection_pos = start_pos + length - 1

                # instr_pos = called_contract_src_code[injection_pos:injection_pos+1]

                if contract_file_name not in src_path_to_instrs:
                    src_path_to_instrs[contract_file_name] = []

                instr = {
                    "pos": injection_pos,
                    "instr": duplicate_funcs_str
                }
                src_path_to_instrs[contract_file_name].append(instr)


def sort_and_merge_instrs(src_path_to_instrs):
    for src_path in src_path_to_instrs:
        l = src_path_to_instrs[src_path]
        l = sorted(l, key=lambda i: i['pos'], reverse=False)
        src_path_to_instrs[src_path] = l
    for src_path in src_path_to_instrs:
        l = src_path_to_instrs[src_path]
        if l is None or len(l) < 2:
            continue

        merged_instrs = []
        prev_pos = -1
        new_l = []
        for instr in l:
            pos = instr["pos"]

            if prev_pos == -1:
                prev_pos = pos
                new_l = [instr["instr"]]
                continue

            if prev_pos == pos:
                new_l.append(instr["instr"])
            else:
                merged_instrs_str = '\n\n'.join(new_l)
                merged_instr = {
                    "pos": prev_pos,
                    "instr": merged_instrs_str
                }
                merged_instrs.append(merged_instr)
                prev_pos = pos
                new_l = [instr["instr"]]

        assert len(new_l) > 0

        merged_instrs_str = '\n\n'.join(new_l)
        merged_instr = {
            "pos": prev_pos,
            "instr": merged_instrs_str
        }
        merged_instrs.append(merged_instr)

        src_path_to_instrs[src_path] = merged_instrs


def get_src_path_to_instrs_code(slither, src_path_to_instrs, src_path_to_instrs_code):
    src_file_names = set()
    for contract in slither.contracts:
        contract_file_name = contract.source_mapping['filename_used']
        src_file_names.add(contract_file_name)
    for src_file_name in src_file_names:
        src_code = slither.crytic_compile.src_content[src_file_name]

        if src_file_name not in src_path_to_instrs:
            src_path_to_instrs_code[src_file_name] = src_code
            continue

        instrs = src_path_to_instrs[src_file_name]

        pos = 0
        modified_source_prefix = ""
        instr_pos = 0

        current_instr = None
        if instr_pos < len(instrs):
            current_instr = instrs[instr_pos]

        while pos < len(src_code):

            if current_instr is not None:
                if pos == current_instr["pos"]:
                    modified_source_prefix = modified_source_prefix + current_instr["instr"]

                    instr_pos = instr_pos + 1
                    if instr_pos < len(instrs):
                        current_instr = instrs[instr_pos]
                    else:
                        current_instr = None

            read_char = src_code[pos]
            modified_source_prefix = modified_source_prefix + read_char

            pos = pos + 1

        src_path_to_instrs_code[src_file_name] = modified_source_prefix