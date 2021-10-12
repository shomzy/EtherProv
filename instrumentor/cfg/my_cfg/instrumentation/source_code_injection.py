def inject_code_instrumentation_to_source_code(all_instr, slither):

    contract_src = {}
    for contract in slither.contracts:
        contract_file_name = contract.source_mapping['filename_used']
        contract_source_code = slither.crytic_compile.src_content[contract_file_name]

        contract_instr = [i for i in all_instr if i['instr_group_contract'] is contract]

        line = 1
        col = 1
        pos = 0
        modified_source_prefix = ""
        instr_pos = 0

        current_instr = None
        if instr_pos < len(contract_instr):
            current_instr = contract_instr[instr_pos]

        while pos < len(contract_source_code):

            if current_instr is not None:
                if line == current_instr['instr_group_line'] and col == current_instr['instr_group_col']:

                    modified_source_prefix = modified_source_prefix + current_instr['aggregated_instrumentation']

                    instr_pos = instr_pos + 1
                    if instr_pos < len(contract_instr):
                        current_instr = contract_instr[instr_pos]
                    else:
                        current_instr = None

            read_char = contract_source_code[pos]
            modified_source_prefix = modified_source_prefix + read_char
            if read_char == '\n':
                line = line + 1
                col = 1
            else:
                col = col + 1
            pos = pos + 1
            result = col, line, modified_source_prefix, pos
            col, line, modified_source_prefix, pos = result

        path_counter_path = './PathCounter.sol'
        contract_src[contract] = f'import "{path_counter_path}";\n' + modified_source_prefix

    return contract_src






