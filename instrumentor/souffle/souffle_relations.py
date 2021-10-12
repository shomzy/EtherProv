import pathlib
import re

from cfg.utils import write_line_to_file, read_full_file, delete_directory_files


def populate_souffle_relations_parameters(file_data, souffle_relations):

    r = r'(\.\s*decl\s*[^(]*\([^)]*\))'
    relations = re.findall(r, file_data)
    for relation in relations:

        r = r'\.\s*decl\s*([^\s(]*)\('
        relation_name = re.findall(r, relation)[0]

        if relation_name not in souffle_relations:
            continue

        souffle_query_relation = list()
        souffle_relations[relation_name]['parameters'] = souffle_query_relation
        r = r'([^\s,()]+)[:]([^\s,()]+)'
        fields_data = re.findall(r, relation)
        for field_data in fields_data:
            f_name = field_data[0]
            f_type = field_data[1]
            souffle_query_relation.append((f_name, f_type))


def append_query_line_from_dic(dic_data, rel_name, souffle_query_relations):
    dic_to_list = []
    for field in souffle_query_relations[rel_name]['parameters']:
        f_name = field[0]
        f_type = field[1]
        val = dic_data[f_name]
        dic_to_list.append(val)
    write_line_to_file('\t'.join(dic_to_list), souffle_query_relations[rel_name]['file_path'], 'a')


def get_souffle_query_relations_metadata():
    work_dir = pathlib.Path().resolve()
    work_dir = f'{work_dir.parent}/{work_dir.name}'

    souffle_query_file_path = work_dir + "/souffle/query.dl"
    facts_dir_path = work_dir + "/data/facts/"

    delete_directory_files(facts_dir_path + '*')
    delete_directory_files(facts_dir_path + '.*')
    file_data = read_full_file(souffle_query_file_path)

    souffle_query_relations = {
        'static_contract': {'file_path': None, 'relation': None, 'parameters': None},
        'static_contract_state_parameter': {'file_path': None, 'relation': None, 'parameters': None},
        'static_function': {'file_path': None, 'relation': None, 'parameters': None},
        'static_function_parameter': {'file_path': None, 'relation': None, 'parameters': None},
        'static_node': {'file_path': None, 'relation': None, 'parameters': None},
        'static_variable': {'file_path': None, 'relation': None, 'parameters': None},
        'static_edge': {'file_path': None, 'relation': None, 'parameters': None},
        'static_ssa_edge': {'file_path': None, 'relation': None, 'parameters': None},
        'static_path': {'file_path': None, 'relation': None, 'parameters': None},
        'static_path_first_read_last_written_state_parameter': {'file_path': None, 'relation': None, 'parameters': None},
        'static_ssa_node': {'file_path': None, 'relation': None, 'parameters': None},
        'static_ssa_non_contract_function_call': {'file_path': None, 'relation': None, 'parameters': None},
        'static_ssa_node_variable': {'file_path': None, 'relation': None, 'parameters': None},
        'static_ssa_node_operation_with_l_value': {'file_path': None, 'relation': None, 'parameters': None},
        'static_ssa_node_index': {'file_path': None, 'relation': None, 'parameters': None},
        'static_ssa_function_return_variable': {'file_path': None, 'relation': None, 'parameters': None},
        'static_ssa_node_read_variable': {'file_path': None, 'relation': None, 'parameters': None},
        'dynamic_contract': {'file_path': None, 'relation': None, 'parameters': None},
        'dynamic_smart_contract_call': {'file_path': None, 'relation': None, 'parameters': None},
        'dynamic_smart_contract_function_call_parameter': {'file_path': None, 'relation': None, 'parameters': None},
        'dynamic_path': {'file_path': None, 'relation': None, 'parameters': None},
        'dynamic_smart_contract_call_state_parameter_written': {'file_path': None, 'relation': None, 'parameters': None},
        'dynamic_smart_contract_call_state_parameter_read': {'file_path': None, 'relation': None, 'parameters': None},
    }

    for r in souffle_query_relations:
        souffle_query_relations[r]['file_path'] = f'{facts_dir_path}{r}.facts'

    populate_souffle_relations_parameters(file_data, souffle_query_relations)

    return souffle_query_relations
