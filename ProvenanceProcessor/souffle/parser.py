import re


def get_souffle_query_relations_metadata(file_data):
    relation_names = [
        'static_contract_state_parameter',
        'static_path_first_read_last_written_state_parameter',
        'dynamic_contract',
        'dynamic_smart_contract_call',
        'dynamic_smart_contract_function_call_parameter',
        'dynamic_path',
        'dynamic_smart_contract_call_state_parameter_written',
        'dynamic_smart_contract_call_state_parameter_read']
    relation_names = set(relation_names)


    souffle_query_relations = {}
    r = r'(\.\s*decl\s*[^(]*\([^)]*\))'
    relations = re.findall(r, file_data)
    for relation in relations:

        r = r'\.\s*decl\s*([^\s(]*)\('
        relation_name = re.findall(r, relation)[0]

        if relation_name not in relation_names:
            continue

        souffle_query_relation = list()
        souffle_query_relations[relation_name] = souffle_query_relation
        r = r'([^\s,()]+)[:]([^\s,()]+)'
        fields_data = re.findall(r, relation)
        for field_data in fields_data:
            f_name = field_data[0]
            f_type = field_data[1]
            souffle_query_relation.append((f_name, f_type))
    return souffle_query_relations