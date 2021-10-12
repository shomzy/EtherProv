import json


def get_contract_address_to_contract_info(data_dir_path):
    contract_info = json.loads(open(data_dir_path + "address_to_contract_details.data").read())
    contract_address_to_contract_info = {}
    for item in contract_info.items():
        contract_address = item[0]
        c_info = json.loads(item[1])

        assert contract_address not in contract_address_to_contract_info

        contract_name = c_info["contractName"]
        contract_abi = c_info["abi"]
        contract_networks = c_info["networks"]

        contract_address_to_contract_info[contract_address] = {'contract_address': contract_address,
                                                               'contract_name': contract_name,
                                                               'contract_abi': contract_abi,
                                                               'networks': contract_networks}

    return contract_address_to_contract_info


def get_contract_address_to_contract(contracts):
    contract_address_to_contract = {}
    for contract_item in contracts.items():
        contract_id = contract_item[0]
        contract = contract_item[1]

        contract_address_to_contract[contract.address] = {
            'contract': contract,
            'contract_id': contract_id
        }
    return contract_address_to_contract