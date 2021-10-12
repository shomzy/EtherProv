import re
import shutil

from cfg.utils import write_to_file
from utils import slitherfy_file, extract_src_details

instr_placeholder_str = '$$PathCounterInstrumentationPlaceholder$$'
instr_placeholder_re = '\$\$PathCounterInstrumentationPlaceholder\$\$'

class SolidityCodeInstrumenterWithNoLoops:
    def __init__(self):
        pass

    # solidity code formatters
    def get_solidity_init_all_transaction_data(self, counter_init_val):
        # return f'r = {counter_init_val}'
        assert counter_init_val != 0
        # return f'_pc_init_all_transaction_data({counter_init_val})'
        return f'_pc_counter = {counter_init_val}'

    def get_solidity_inc_counter(self, counter_inc):
        # return f'r += {counter_inc}'
        assert counter_inc != 0
        return f'_pc_inc_counter({counter_inc})'

    def get_solidity_inc_transaction_path_count_and_flush(self, counter_inc):
        # return f'path_counter[r + {counter_inc}]++'
        if counter_inc == 0:
            return f'_pc_flush_path_data()'
        else:
            return f'_pc_counter = _pc_counter + {counter_inc};_pc_flush_path_data()'

    def get_solidity_reset_counter(self, counter_reset):
        # return f'r = {counter_reset}'
        return f'_pc_counter = {counter_reset}'


class SolidityCodeInstrumenterWithLoops:
    def __init__(self):
        pass

    # solidity code formatters
    def get_solidity_init_all_transaction_data(self, counter_init_val):
        # return f'r = {counter_init_val}'
        assert counter_init_val != 0
        return f'_pc_init_all_transaction_data({counter_init_val})'

    def get_solidity_inc_counter(self, counter_inc):
        # return f'r += {counter_inc}'
        assert counter_inc != 0
        return f'_pc_inc_counter({counter_inc})'

    def get_solidity_inc_transaction_path_count_and_flush(self, counter_inc):
        # return f'path_counter[r + {counter_inc}]++'
        if counter_inc == 0:
            return f'_pc_flush_path_data()'
        else:
            return f'_pc_inc_transaction_path_count({counter_inc});_pc_flush_path_data()'

    def get_solidity_reset_counter(self, counter_reset):
        # return f'r = {counter_reset}'
        return f'_pc_reset_counter({counter_reset})'


class SolidityCodeInstrumenter:
    def __init__(self, paths, slither, path_counter_dir):
        self.slither = slither
        self.path_counter_dir = path_counter_dir


        self.path_statements_contain_loop = False
        for pid in paths:
            path_details = paths[pid]
            is_loop_path = path_details['is_loop_path']
            if is_loop_path:
                self.path_statements_contain_loop = True
                break

        self.path_counter_path = get_path_counter_path(path_counter_dir, self.slither, self.path_statements_contain_loop)

        if self.path_statements_contain_loop:
            self.instr = SolidityCodeInstrumenterWithLoops()
        else:
            self.instr = SolidityCodeInstrumenterWithNoLoops()

    def add_path_counter_logic_instrumentation(self, instr_sol_file):
        slither_path_counter = slitherfy_file(self.path_counter_path)

        path_counter_ast = slither_path_counter.crytic_compile.asts[self.path_counter_path]
        path_counter_source_code = slither_path_counter.crytic_compile.src_content_for_file(self.path_counter_path)

        if path_counter_ast['nodeType'] != 'SourceUnit':
            raise Exception('unhandled scenario')

        for n in path_counter_ast['nodes']:
            if n['nodeType'] != 'ContractDefinition':
                continue

            var_instr = self.extract_path_counter_var_instr_code(n, path_counter_source_code)

            fun_instr = self.extract_path_counter_fun_instr_code(n, path_counter_source_code)

            # PathCounter _path_counter = PathCounter();
            path_counter_instr = f'{var_instr}\n{fun_instr}\n'
            self.inject_path_counter_instrumentation(path_counter_instr, instr_sol_file)

    def extract_path_counter_fun_instr_code(self, node, path_counter_source_code):
        fun_instr = []
        for cn in node['nodes']:
            if cn['nodeType'] == 'FunctionDefinition':
                if cn['name'] != '':
                    start, len = extract_src_details(cn['src'])
                    src = path_counter_source_code[start:start + len]
                    fun_instr.append(src)
        fun_instr = '\n'.join(fun_instr)
        return fun_instr


    def extract_path_counter_var_instr_code(self, node, path_counter_source_code):
        var_instr = []
        for cn in node['nodes']:
            if cn['nodeType'] in ['VariableDeclaration']:
                start, len = extract_src_details(cn['src'])
                src = path_counter_source_code[start:start + len] + ';'
                var_instr.append(src)
            elif cn['nodeType'] in ['StructDefinition']:
                start, len = extract_src_details(cn['src'])
                src = path_counter_source_code[start:start + len]
                var_instr.append(src)
            elif cn['nodeType'] in ['EventDefinition']:
                start, len = extract_src_details(cn['src'])
                src = path_counter_source_code[start:start + len]
                var_instr.append(src)
        var_instr = '\n'.join(var_instr)
        return var_instr

    def copy_path_counter_path(self, instrumented_sol_dir):
        path_counter_source = self.path_counter_path
        path_counter_target = f'{instrumented_sol_dir}PathCounter.sol'

        shutil.copyfile(path_counter_source, path_counter_target)

    def inject_path_counter_instrumentation(self, instr, instr_sol_file):
        with open(instr_sol_file, 'r') as ff:
            content = ff.read()
        content_updated = re.sub(f'{instr_placeholder_re};', instr, content)
        write_to_file(instr_sol_file, 'w', content_updated)


def get_path_counter_path(path_counter_dir, slither, contains_loops):
    compiler_version = slither.crytic_compile.compiler_version.version

    if contains_loops:
        path_counter_path = f'{path_counter_dir}{compiler_version}/PathCounterLoops.sol'
    else:
        path_counter_path = f'{path_counter_dir}{compiler_version}/PathCounterNoLoops.sol'
    return path_counter_path



