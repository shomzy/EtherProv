from shutil import copyfile

from cfg.utils import write_to_file


def write_instrumented_files(contract_src, output_dir):
    # instrumented_contracts_path = './instrumentor/contracts/'
    instrumented_contracts_path = output_dir

    for item in contract_src.items():
        contract = item[0]
        src = item[1]
        file_path = instrumented_contracts_path + contract.name + '.sol'
        # with safe_open(file_path, 'w') as f:
        #     f.write(src)
        write_to_file(file_path, 'w', src)


    # contracts_path = './instrumentor/contracts/'
    # from_path = f'{contracts_path}PathCounter.sol'
    # to_path = f'{instrumented_contracts_path}PathCounter.sol'
    # copyfile(from_path, to_path)
    # from_path = f'{contracts_path}Migrations.sol'
    # to_path = f'{instrumented_contracts_path}Migrations.sol'
    # copyfile(from_path, to_path)








