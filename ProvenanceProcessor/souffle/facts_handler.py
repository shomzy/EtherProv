from utils import write_line_to_file


def get_all_relations_data(souffle_query_relations, facts_dir_path):
    relations_data = {}
    for rel_name in souffle_query_relations:
        load_relation(rel_name, facts_dir_path, souffle_query_relations, relations_data)
    return relations_data


def load_relation(rel_name, facts_dir_path, souffle_query_relations, relations_data):
    facts_file_path = facts_dir_path + rel_name + '.facts'
    relation_data = list()
    relations_data[rel_name] = relation_data
    with open(facts_file_path, 'r') as myfile:
        lines = myfile.readlines()

        for line in lines:
            line_split = line.strip('\n\r').split('\t')
            souffle_relation = souffle_query_relations[rel_name]

            d = {}
            for i in range(0, len(souffle_relation)):
                field_name = souffle_relation[i][0]

                # if i >= len(line_split):
                #     x = 3

                d[field_name] = line_split[i]
            relation_data.append(d)


def append_query_line_from_dic(dic_data, rel_name, souffle_query_relations, static_contract_file_path):
    dic_to_list = []
    for field in souffle_query_relations[rel_name]:
        f_name = field[0]
        f_type = field[1]
        val = dic_data[f_name]
        dic_to_list.append(val)
    write_line_to_file('\t'.join(dic_to_list), static_contract_file_path, 'a')


