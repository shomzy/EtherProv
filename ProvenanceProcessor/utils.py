def read_full_file(file_path):
    file_data = None
    with open(file_path, 'r') as file:
        file_data = file.read()
    return file_data


def write_line_to_file(line_data, file_name, write_attr):
    write_to_file(line_data+"\n", file_name, write_attr)


def write_to_file(line_data, file_name, write_attr):
    with open(file_name, write_attr) as myfile:
        myfile.write(line_data)


def full_function_signature(contract_name, function_name, function_parameters):
    sig = f'{contract_name}#{function_name}' + ('#' + '#'.join(function_parameters) if len(function_parameters) > 0 else '')
    return sig


def get_contract_full_function_parameter_id(contract_name, function_name, function_parameters, parameter_name):
    return f'{full_function_signature(contract_name, function_name, function_parameters)}#{parameter_name}'


def get_max_value(val_list):
    max_int = None
    if len(val_list) > 0:
        val_list.sort(key=lambda t: t, reverse=True)
        max_int = val_list[0]
    return max_int


def get_hash_of_list_items(list_):
    list_str = str(list_)
    hash_ = hash(list_str)
    return hash_
    #return str(list_)