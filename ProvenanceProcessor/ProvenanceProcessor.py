import uuid

from web3 import Web3, HTTPProvider

from contract_mapping.contract_mapping import get_contract_address_to_contract_info, get_contract_address_to_contract
from souffle.facts_handler import get_all_relations_data, append_query_line_from_dic, load_relation
from souffle.parser import get_souffle_query_relations_metadata
from utils import read_full_file, get_contract_full_function_parameter_id, get_hash_of_list_items, get_max_value, \
    full_function_signature


def get_events_data(contract, fromBlock, toBlock):
    # should have just 1 event - 'path'
    assert len(contract.events._events) == 1

    events_data = []
    for contractEvent in contract.events:
        myfilter = contractEvent.createFilter(fromBlock=fromBlock, toBlock=toBlock)
        eventlist = myfilter.get_all_entries()



        for event in eventlist:
            # for arg_name in event["args"]:
            #     args_names_list.append(arg_name)

            # event_data = {
            #     'blockNumber': event["blockNumber"],
            #     'transactionIndex': event["transactionIndex"],
            #     'logIndex': event["logIndex"],
            #     'count': event["args"]['count'],
            #     'path_id': event["args"]['path_id'],
            # }

            events_data.append(event)

    return events_data


def get_function_name_and_parameters(contract, transaction_input):
    function = contract.decode_function_input(transaction_input)
    function_attr = function[0]
    function_vals = function[1]
    function_name = function_attr.abi['name']
    f_inputs = function_attr.abi['inputs']
    parameters = list()
    for p in f_inputs:
        p_name = p['name']
        p_data = {
            'name': p_name,
            'type': p['type'],
            'val': function_vals[p_name]
        }
        parameters.append(p_data)
    return function_name, parameters


def get_dynamic_sc_call_grouped_by_block_trans(dynamic_sc_call_memory):
    grouped_dynamic_sc_call = {}
    for dc in dynamic_sc_call_memory.values():
        block_id = int(dc['block_id'])
        if block_id not in grouped_dynamic_sc_call:
            grouped_dynamic_sc_call[block_id] = {}
        transaction_id = int(dc['transaction_id'])
        if transaction_id not in grouped_dynamic_sc_call[block_id]:
            grouped_dynamic_sc_call[block_id][transaction_id] = {}
        dynamic_contract_id = dc['dynamic_contract_id']
        if dynamic_contract_id not in grouped_dynamic_sc_call[block_id][transaction_id]:
            grouped_dynamic_sc_call[block_id][transaction_id][dynamic_contract_id] = list()
        grouped_dynamic_sc_call[block_id][transaction_id][dynamic_contract_id].append(dc)
    return grouped_dynamic_sc_call


def get_last_dynamic_sc_state_param_written(
        dynamic_sc_call_state_parameter_written_grouped_by_contract_state_parameter_id,
        batch_id,
        static_contract_state_parameter_id):

    last_written = 'NULL'
    batch_id_str = str(batch_id)
    key = (batch_id_str, static_contract_state_parameter_id)
    if key in dynamic_sc_call_state_parameter_written_grouped_by_contract_state_parameter_id:
        l = dynamic_sc_call_state_parameter_written_grouped_by_contract_state_parameter_id[key]

        if len(l) > 0:
            last_written = l[len(l) - 1]
            last_written = last_written['dynamic_smart_contract_call_state_parameter_written_id']
    return last_written


# def get_logs_hash(transaction):
#     logs = transaction['logs']
#     logs = [v for v in logs]
#     logs.sort(key=lambda t: int(t[0]), reverse=False)
#     path_ids_list = list()
#     visited = set()
#     for log in logs:
#         log_pos = log[0]
#         log_args = log[1]
#
#         path_id = log_args['path_id']
#         if path_id in visited:
#             continue
#
#         visited.add(path_id)
#         path_ids_list.append(path_id)
#     hash_ = get_hash_of_list_items(path_ids_list)
#     return hash_


# def update_first_read_last_written_states_original(current_read_parameters, current_written_parameters, first_read_states,
#                                           last_write_states):
#     intersec = current_read_parameters.intersection(current_written_parameters)
#     if len(intersec) > 1:
#         raise Exception('we support only one state that is both written and read in the same node at most once')
#     elif len(intersec) == 1:
#         # for example state1 = state1 + var
#         for sv in intersec:
#             if sv in first_read_states:
#                 # do nothing, state is read again
#                 pass
#
#             elif sv in last_write_states:
#                 # state was read after it was written with another value, do nothing
#                 pass
#
#             else:
#                 # new state read, record it
#                 first_read_states.add(sv)
#     for sv in current_read_parameters:
#         if sv in first_read_states:
#             # do nothing, state is read again
#             pass
#
#         elif sv in last_write_states:
#             # state was read after it was written with another value, do nothing
#             pass
#
#         else:
#             # new state read, record it
#             first_read_states.add(sv)
#     for sv in current_written_parameters:
#         if sv in first_read_states:
#             # state was written after it was read, record it
#             last_write_states.add(sv)
#
#         elif sv in last_write_states:
#             # state was rewritten do nothing
#             pass
#
#         else:
#             # new state write, record it
#             last_write_states.add(sv)
#


def update_first_read_last_written_states(current_read_parameters, current_written_parameters, first_read_states,
                                          last_write_states):
    # intersec = current_read_parameters.intersection(current_written_parameters)
    # if len(intersec) > 1:
    #     raise Exception('we support only one state that is both written and read in the same node at most once')
    # elif len(intersec) == 1:
    #     # for example state1 = state1 + var
    #     for sv in intersec:
    #         if sv in first_read_states:
    #             # do nothing, state is read again
    #             pass
    #
    #         elif sv in last_write_states:
    #             # state was read after it was written with another value, do nothing
    #             pass
    #
    #         else:
    #             # new state read, record it
    #             first_read_states.add(sv)

    for sv in current_read_parameters:
        if sv in first_read_states:
            # do nothing, state is read again
            pass

        elif sv in last_write_states:
            # state was read after it was written with another value, do nothing
            pass

        else:
            # new state read, record it
            first_read_states.add(sv)
    for sv in current_written_parameters:
        if sv in first_read_states:
            # state was written after it was read, record it
            last_write_states.add(sv)

        elif sv in last_write_states:
            # state was rewritten do nothing
            pass

        else:
            # new state write, record it
            last_write_states.add(sv)



class ProvenanceProcessor:
    def __init__(self):

        self.data_dir_path = "/home/slinoy/Downloads/Simple_contract/data/"

        self.facts_dir_path = "/home/slinoy/Downloads/Simple_contract/data/facts/"
        self.souffle_query_file_path = '/home/slinoy/Downloads/Simple_contract/souffle/query.dl'

        # self.socialite_dir_path = "/home/slinoy/Downloads/Simple_contract/socialite/"
        # self.socialite_str_symbol = "`"

        file_data = read_full_file(self.souffle_query_file_path)

        self.souffle_query_relations_metadata = get_souffle_query_relations_metadata(file_data)

        self.contract_address_to_contract_info = get_contract_address_to_contract_info(self.data_dir_path)

        self.relations_data = get_all_relations_data(self.souffle_query_relations_metadata, self.facts_dir_path)

        # self.inject_dynamic_dummies()
        # return

        self.w3 = Web3(HTTPProvider("http://127.0.0.1:7545"))

        self.contracts = self.get_contracts()

        self.path_counter_contract = self.get_path_counter_contract()

        # the following line was supposed to help in mapping a transaction used to deploy a contract
        # to the deployed contract address. Important: multiple instances of the same contract are not
        # supported since Truffle and Ganache don't support them!!!
        self.txhash_to_deployed_contract_address = self.get_txhash_to_deployed_contract_address()

        self.contract_address_to_contract = get_contract_address_to_contract(self.contracts)
        self.w3.eth.defaultAccount = self.w3.eth.accounts[0]

        self.static_path_first_read_last_written_state_parameter_memory = self.get_static_path_first_read_last_written_state_parameter_memory()
        self.static_contract_state_parameter_memory = self.get_static_contract_state_parameter_memory()

        self.dynamic_contract_memory = self.get_dynamic_contract_memory()
        self.dynamic_sc_call_memory = self.get_dynamic_sc_call_memory()
        self.dynamic_sc_call_state_parameter_written_memory = self.get_dynamic_sc_call_state_parameter_written_memory()

    def get_txhash_to_deployed_contract_address(self):
        txhash_to_deployed_contract_address = {}
        for item in self.contract_address_to_contract_info.items():
            contract_name = item[1]['contract_name']
            if contract_name == 'PathCounter':
                continue

            contract_address = item[0]
            txhash = None

            for i in item[1]['networks'].items():
                txhash = i[1]["transactionHash"]
                break
            assert txhash is not None

            txhash_to_deployed_contract_address[txhash] = contract_address
        return txhash_to_deployed_contract_address

    def get_path_counter_contract(self):
        path_counter_contract = None
        for item in self.contract_address_to_contract_info.items():
            contract_name = item[1]['contract_name']
            if contract_name == 'PathCounter':
                contract_address = item[0]
                path_counter_contract = self.get_contract(contract_address)
                break
        assert path_counter_contract is not None
        return path_counter_contract

    def get_contracts(self):
        contracts = {}
        for item in self.contract_address_to_contract_info.items():
            contract_name = item[1]['contract_name']
            if contract_name == 'PathCounter':
                continue

            contract_address = item[0]
            contracts[contract_address] = self.get_contract(contract_address)

        return contracts

    def run(self):

        # static_contract_state_parameter_grouped_by_contract_id = {}
        # for static_contract_state_parameter in self.static_contract_state_parameter_memory.values():
        #     contract_id = static_contract_state_parameter['static_contract_id']
        #     if contract_id not in static_contract_state_parameter_grouped_by_contract_id:
        #         static_contract_state_parameter_grouped_by_contract_id[contract_id] = list()
        #     static_contract_state_parameter_grouped_by_contract_id[contract_id].append(static_contract_state_parameter)

        # for c_item in self.contracts.items():
        #     contract_id = c_item[0]
        #     contract_address = c_item[1].address
        #
        #     contract_found = False
        #     for dynamic_contract_id in self.dynamic_contract_memory:
        #         if dynamic_contract_id == contract_id:
        #             contract_found = True
        #
        #     if not contract_found:
        #         # all deployed contracts need to be written to the dynamic_contract relation
        #         self.process_dynamic_contract(contract_id, contract_address)

                # Important: multiple instances of the same contract are not supported since Truffle
                # and Ganache don't support them!!!
                # Because of this, in these environments, there is no way to connect the transaction that
                # deploys a contract to its deployed contract address. So no contract creation info is collected
                #self.process_init_contract_state_parameters_values(contract_id, static_contract_state_parameter_grouped_by_contract_id)

        self.process()

        # tx_hash = client_contract.functions.withdraw(100).transact()
        # w3.eth.waitForTransactionReceipt(tx_hash)

    # todo - the premise is that this process function should be ran after each single transaction has finished
    #  processing in the miner side. this is due to us enquiring the state values of the relevant contract from the
    #  contract itself after its execution. reading these sate values after a different transaction had ran can result
    #  in overriding the previous state values
    def process(self):

        dynamic_sc_call_grouped_by_block_trans = get_dynamic_sc_call_grouped_by_block_trans(self.dynamic_sc_call_memory)
        grouped_events_data = self.get_current_grouped_events_data(dynamic_sc_call_grouped_by_block_trans, self.path_counter_contract)

        block_numbers = grouped_events_data.keys()
        block_numbers = [v for v in block_numbers]
        block_numbers.sort(key=lambda t: int(t), reverse=False)
        for block_id in block_numbers:
            transaction_ids = grouped_events_data[block_id].keys()
            transaction_ids = [v for v in transaction_ids]
            transaction_ids.sort(key=lambda t: int(t), reverse=False)
            for transaction_id in transaction_ids:
                dynamic_sc_call_id = uuid.uuid4()
                transaction = grouped_events_data[block_id][transaction_id]

                transaction_to = transaction['transaction'].to
                transaction_from = transaction['transaction']['from']
                contract_address = None

                # Important: multiple instances of the same contract are not supported since Truffle
                # and Ganache don't support them!!!
                # Because of this, in these environments, there is no way to connect the transaction that
                # deploys a contract to its deployed contract address. So no contract creation info is collected
                if transaction_to is None:
                    # created contract address is in the from field
                    contract_address = transaction_from
                else:
                    contract_address = transaction_to

                if contract_address not in self.contract_address_to_contract_info:
                    continue

                f_name = f'get_batch_id'
                contract = self.contracts[contract_address]
                m = getattr(contract.functions, f_name)
                batch_id = m().call()

                if contract_address not in self.dynamic_contract_memory:
                    contract_name = self.contract_address_to_contract_info[contract_address]['contract_name']
                    # all deployed contracts need to be written to the dynamic_contract relation
                    self.process_dynamic_contract(batch_id, contract_name, contract_address)
                assert contract_address in self.dynamic_contract_memory

                self.process_dynamic_sc_call(dynamic_sc_call_id, block_id, transaction_id, transaction)
                self.process_dynamic_path(dynamic_sc_call_id, transaction)
                self.process_dynamic_sc_function_call_parameter(dynamic_sc_call_id, transaction)

                first_read_states, last_write_states = self.get_transaction_first_read_last_write_state_ids(batch_id, transaction)

                dynamic_sc_call_state_parameter_written_grouped_by_contract_state_parameter_id = \
                    self.get_dynamic_sc_call_state_parameter_written_grouped_by_contract_state_parameter_id()

                rel_name = 'dynamic_smart_contract_call_state_parameter_read'
                facts_file_path = self.facts_dir_path + rel_name + '.facts'
                for static_contract_state_parameter_id in first_read_states:
                    #static_contract_state_parameter_id = read_parameter['static_contract_state_parameter_id']
                    last_written = get_last_dynamic_sc_state_param_written(
                        dynamic_sc_call_state_parameter_written_grouped_by_contract_state_parameter_id,
                        batch_id,
                        static_contract_state_parameter_id)

                    d = {
                        'dynamic_smart_contract_call_id': str(dynamic_sc_call_id),
                        'static_contract_state_parameter_id': static_contract_state_parameter_id,
                        'dynamic_smart_contract_call_state_parameter_written': last_written,
                    }
                    append_query_line_from_dic(d, rel_name, self.souffle_query_relations_metadata, facts_file_path)
                load_relation(rel_name, self.facts_dir_path, self.souffle_query_relations_metadata, self.relations_data)

                rel_name = 'dynamic_smart_contract_call_state_parameter_written'
                facts_file_path = self.facts_dir_path + rel_name + '.facts'
                for static_contract_state_parameter_id in last_write_states:
                    dynamic_smart_contract_call_state_parameter_written_id = uuid.uuid4()
                    #static_contract_state_parameter_id = written_parameter['static_contract_state_parameter_id']
                    last_written = get_last_dynamic_sc_state_param_written(
                        dynamic_sc_call_state_parameter_written_grouped_by_contract_state_parameter_id,
                        batch_id,
                        static_contract_state_parameter_id)

                    batch_id_str = str(batch_id)
                    key = (batch_id_str, static_contract_state_parameter_id)
                    static_contract_state_parameter = self.static_contract_state_parameter_memory[key]

                    parameter_name = static_contract_state_parameter['name']
                    f_name = f'get_state_{parameter_name}'

                    #contract_id = static_contract_state_parameter['static_contract_id']
                    #contract = self.contracts[contract_id]
                    contract = self.contracts[contract_address]

                    m = getattr(contract.functions, f_name)
                    new_written = m().call()

                    d = {
                        'dynamic_smart_contract_call_state_parameter_written_id': str(dynamic_smart_contract_call_state_parameter_written_id),
                        'dynamic_smart_contract_call_id': str(dynamic_sc_call_id),
                        'static_contract_state_parameter_id': static_contract_state_parameter_id,
                        'value': str(new_written),
                        'prev_dynamic_smart_contract_call_state_parameter_written': last_written,
                    }
                    append_query_line_from_dic(d, rel_name, self.souffle_query_relations_metadata, facts_file_path)
                load_relation(rel_name, self.facts_dir_path, self.souffle_query_relations_metadata, self.relations_data)
                self.dynamic_sc_call_state_parameter_written_memory = self.get_dynamic_sc_call_state_parameter_written_memory()

    def inject_dynamic_dummies(self):
        sc_call = self.relations_data['dynamic_smart_contract_call']
        # get last contract call
        last_sc_call = sc_call[len(sc_call) - 1]
        prev_sc_call_id = last_sc_call['smart_contract_call_id']

        path = self.relations_data['dynamic_path']
        prev_sc_call_paths = [p for p in path if
                                 p['dynamic_smart_contract_call_id'] == prev_sc_call_id]

        sc_state_param_written = self.relations_data['dynamic_smart_contract_call_state_parameter_written']
        prev_sc_state_param_written = [p for p in sc_state_param_written if
                                          p['dynamic_smart_contract_call_id'] == prev_sc_call_id]
        suffix = "_20M.facts"
        for i in range(0, 20000000):

            current_sc_call_id = str(uuid.uuid4())
            # d = {
            #     'smart_contract_call_id': current_sc_call_id,
            #     'dynamic_contract_id': last_sc_call['dynamic_contract_id'],
            #     'block_id': last_sc_call['block_id'],
            #     'transaction_id': last_sc_call['transaction_id'],
            #     'caller_address': last_sc_call['caller_address'],
            #     'ether_start': 'not_yet_supported',
            #     'ether_end': 'not_yet_supported',
            #     'static_function_id': last_sc_call['static_function_id'],
            # }
            # rel_name = 'dynamic_smart_contract_call'
            # facts_file_path = self.facts_dir_path + rel_name + suffix
            # append_query_line_from_dic(d, rel_name, self.souffle_query_relations_metadata, facts_file_path)
            #
            # continue
            #
            # current_sc_call_paths = list()
            # for p in prev_sc_call_paths:
            #     d = {
            #         'dynamic_smart_contract_call_id': current_sc_call_id,
            #         'static_path_id': p['static_path_id'],
            #         'order': p['order'],
            #         'path_count': p['path_count'],
            #     }
            #     rel_name = 'dynamic_path'
            #     facts_file_path = self.facts_dir_path + rel_name + suffix
            #     append_query_line_from_dic(d, rel_name, self.souffle_query_relations_metadata, facts_file_path)
            #     current_sc_call_paths.append(d)
            # prev_sc_call_paths = current_sc_call_paths

            current_sc_state_param_written = list()
            for p in prev_sc_state_param_written:

                d = {
                    'dynamic_smart_contract_call_state_parameter_written_id': str(uuid.uuid4()),
                    'dynamic_smart_contract_call_id': current_sc_call_id,
                    'static_contract_state_parameter_id': p['static_contract_state_parameter_id'],
                    'value': p['value'],
                    'prev_dynamic_smart_contract_call_state_parameter_written': p['dynamic_smart_contract_call_state_parameter_written_id'],
                }
                rel_name = 'dynamic_smart_contract_call_state_parameter_written'
                facts_file_path = self.facts_dir_path + rel_name + suffix
                append_query_line_from_dic(d, rel_name, self.souffle_query_relations_metadata, facts_file_path)
                current_sc_state_param_written.append(d)
            prev_sc_state_param_written = current_sc_state_param_written


    def get_transaction_first_read_last_write_state_ids(self, batch_id, transaction):
        # hash_ = str(get_logs_hash(transaction))

        logs = transaction['logs']
        logs = [v for v in logs]
        logs.sort(key=lambda t: int(t[0]), reverse=False)
        # path_ids_list = list()
        first_read_states = set()
        last_write_states = set()
        for log in logs:
            log_pos = log[0]
            log_args = log[1]
            path_id = log_args['path_id']

            path_id_str = str(path_id)
            batch_id_str = str(batch_id)
            key = (batch_id_str, path_id_str)
            if key not in self.static_path_first_read_last_written_state_parameter_memory:
                continue

            current_read_parameters = [p['static_contract_state_parameter_id'] for p in
                                       self.static_path_first_read_last_written_state_parameter_memory[key]
                                       if p['first_read_or_last_written'] == 'first_read']
            current_read_parameters = set(current_read_parameters)

            current_written_parameters = [p['static_contract_state_parameter_id'] for p in
                                          self.static_path_first_read_last_written_state_parameter_memory[key]
                                          if p['first_read_or_last_written'] == 'last_written']
            current_written_parameters = set(current_written_parameters)

            update_first_read_last_written_states(current_read_parameters, current_written_parameters,
                                                       first_read_states,
                                                       last_write_states)

        # read_parameters = [p for p in self.static_path_first_read_last_written_state_parameter_memory[hash_]
        #                    if p['first_read_or_last_written'] == 'first_read']
        # written_parameters = [p for p in self.static_path_first_read_last_written_state_parameter_memory[hash_]
        #                    if p['first_read_or_last_written'] == 'last_written']
        # important! do this before the written parameters so in the case a written value was also read, we don't
        # point to it but point to the past transaction written value

        return first_read_states, last_write_states

    def get_dynamic_sc_call_state_parameter_written_grouped_by_contract_state_parameter_id(self):
        dynamic_sc_call_state_parameter_written_grouped_by_contract_state_parameter_id = {}
        for dynamic_sc_call_state_parameter_written_item in self.dynamic_sc_call_state_parameter_written_memory.items():
            contract_state_parameter_id = dynamic_sc_call_state_parameter_written_item[0]
            dynamic_sc_call_state_parameter_written = dynamic_sc_call_state_parameter_written_item[1]

            dynamic_smart_contract_call_id = dynamic_sc_call_state_parameter_written['dynamic_smart_contract_call_id']
            assert dynamic_smart_contract_call_id in self.dynamic_sc_call_memory

            dynamic_sc_call = self.dynamic_sc_call_memory[dynamic_smart_contract_call_id]
            static_contract_state_parameter_id = dynamic_sc_call_state_parameter_written['static_contract_state_parameter_id']

            contract_id = dynamic_sc_call['dynamic_contract_id']
            assert contract_id in self.dynamic_contract_memory

            batch_id = self.dynamic_contract_memory[contract_id]['batch_id']
            key = (batch_id, static_contract_state_parameter_id)

            if key not in dynamic_sc_call_state_parameter_written_grouped_by_contract_state_parameter_id:
                dynamic_sc_call_state_parameter_written_grouped_by_contract_state_parameter_id[key] = list()

            l_i = (dynamic_sc_call['block_id'], dynamic_sc_call['transaction_id'], dynamic_sc_call_state_parameter_written)
            dynamic_sc_call_state_parameter_written_grouped_by_contract_state_parameter_id[key].append(l_i)

        for key in dynamic_sc_call_state_parameter_written_grouped_by_contract_state_parameter_id:
            l = dynamic_sc_call_state_parameter_written_grouped_by_contract_state_parameter_id[key]
            l.sort(key=lambda t: (int(t[0]), int(t[1])), reverse=False)
            new_l = [i[2] for i in l]
            dynamic_sc_call_state_parameter_written_grouped_by_contract_state_parameter_id[key] = new_l
        return dynamic_sc_call_state_parameter_written_grouped_by_contract_state_parameter_id

    def get_dynamic_sc_call_state_parameter_written_memory(self):
        dynamic_sc_call_state_parameter_written = self.relations_data['dynamic_smart_contract_call_state_parameter_written']
        dynamic_sc_call_state_parameter_written_memory = {}
        for dynamic_sc_call_state_parameter_written_item in dynamic_sc_call_state_parameter_written:
            dynamic_smart_contract_call_state_parameter_written_id = dynamic_sc_call_state_parameter_written_item['dynamic_smart_contract_call_state_parameter_written_id']
            dynamic_sc_call_state_parameter_written_memory[dynamic_smart_contract_call_state_parameter_written_id] = dynamic_sc_call_state_parameter_written_item

        return dynamic_sc_call_state_parameter_written_memory

    def get_dynamic_contract_memory(self):
        dynamic_contract = self.relations_data['dynamic_contract']
        dynamic_contract_memory = {}
        for dynamic_contract_item in dynamic_contract:
            contract_address = dynamic_contract_item['contract_address']
            dynamic_contract_memory[contract_address] = dynamic_contract_item
        return dynamic_contract_memory

    def get_static_path_first_read_last_written_state_parameter_memory(self):
        static_path_first_read_last_written_state_parameter = self.relations_data['static_path_first_read_last_written_state_parameter']
        static_path_first_read_last_written_state_parameter_memory = {}
        for static_path_first_read_last_written_state_parameter_item in static_path_first_read_last_written_state_parameter:
            batch_id = static_path_first_read_last_written_state_parameter_item['batch_id']
            static_contract_id = static_path_first_read_last_written_state_parameter_item['static_path_id']
            key = (batch_id, static_contract_id)

            if key not in static_path_first_read_last_written_state_parameter_memory:
                static_path_first_read_last_written_state_parameter_memory[key] = list()

            static_path_first_read_last_written_state_parameter_memory[key].append(static_path_first_read_last_written_state_parameter_item)
        return static_path_first_read_last_written_state_parameter_memory

    def get_static_contract_state_parameter_memory(self):
        static_contract_state_parameter = self.relations_data['static_contract_state_parameter']
        static_contract_state_parameter_memory = {}
        for static_contract_state_parameter_item in static_contract_state_parameter:
            batch_id = static_contract_state_parameter_item['batch_id']
            contract_state_parameter_id = static_contract_state_parameter_item['contract_state_parameter_id']
            key = (batch_id, contract_state_parameter_id)
            static_contract_state_parameter_memory[key] = static_contract_state_parameter_item

        return static_contract_state_parameter_memory

    def process_init_contract_state_parameters_values(self, contract_id, static_contract_state_parameter_grouped_by_contract_id):
        dynamic_sc_call_id = uuid.uuid4()
        # create a dummy dynamic smart contract call
        rel_name = 'dynamic_smart_contract_call'
        facts_file_path = self.facts_dir_path + rel_name + '.facts'
        d = {
            'smart_contract_call_id': str(dynamic_sc_call_id),
            'dynamic_contract_id': contract_id,
            'block_id': str(-1),
            'transaction_id': str(-1),
            'caller_address': 'NULL',
            'ether_start': 'NULL',
            'ether_end': 'NULL',
            'static_function_id': 'NULL',
            #'static_full_path_id': 'NULL',
        }
        append_query_line_from_dic(d, rel_name, self.souffle_query_relations_metadata, facts_file_path)
        load_relation(rel_name, self.facts_dir_path, self.souffle_query_relations_metadata, self.relations_data)
        self.dynamic_sc_call_memory = self.get_dynamic_sc_call_memory()

        rel_name = 'dynamic_smart_contract_call_state_parameter_written'
        facts_file_path = self.facts_dir_path + rel_name + '.facts'

        contract_name = self.contract_address_to_contract_info[contract_id]['contract_name']
        for state_parameter_item in static_contract_state_parameter_grouped_by_contract_id[contract_name]:
            d = {
                'dynamic_smart_contract_call_state_parameter_written_id': str(uuid.uuid4()),
                'dynamic_smart_contract_call_id': str(dynamic_sc_call_id),
                'static_contract_state_parameter_id': state_parameter_item['contract_state_parameter_id'],
                'value': state_parameter_item['initial_value'],
                'prev_dynamic_smart_contract_call_state_parameter_written': 'NULL'
            }
            append_query_line_from_dic(d, rel_name, self.souffle_query_relations_metadata, facts_file_path)
        load_relation(rel_name, self.facts_dir_path, self.souffle_query_relations_metadata, self.relations_data)
        self.dynamic_sc_call_state_parameter_written_memory = self.get_dynamic_sc_call_state_parameter_written_memory()

    def process_dynamic_contract(self, batch_id, contract_name, contract_address):
        rel_name = 'dynamic_contract'
        facts_file_path = self.facts_dir_path + rel_name + '.facts'

        # contract_name = self.contract_address_to_contract_info[contract_address]['contract_name']
        d = {
            'batch_id': str(batch_id),
            'contract_id': contract_name,
            'deployer_address': 'not_yet_supported',
            'initial_ether': 'NULL',
            'contract_address': contract_address,
            'contract_name': contract_name,
        }
        append_query_line_from_dic(d, rel_name, self.souffle_query_relations_metadata, facts_file_path)
        load_relation(rel_name, self.facts_dir_path, self.souffle_query_relations_metadata, self.relations_data)

        self.dynamic_contract_memory = self.get_dynamic_contract_memory()

    def get_current_grouped_events_data(self, grouped_dynamic_sc_call, path_counter_contract):
        block_ids = grouped_dynamic_sc_call.keys()
        block_ids = [int(v) for v in block_ids]
        current_max_block_id = get_max_value(block_ids)
        current_max_transaction_id = None
        if current_max_block_id is not None:
            transaction_ids = grouped_dynamic_sc_call[current_max_block_id].keys()
            transaction_ids = [int(v) for v in transaction_ids]
            current_max_transaction_id = get_max_value(transaction_ids)

        # todo - there is a bug that will freezes ganache if from_block is different than 0
        # current_max_block_id = 0 if current_max_block_id is None else current_max_block_id
        events_data = get_events_data(path_counter_contract, 0, "latest")
        grouped_events_data = {}
        for e in events_data:
            block_number = int(e['blockNumber'])
            transaction_index = int(e['transactionIndex'])

            if current_max_block_id is not None and block_number and block_number < current_max_block_id:
                continue

            if current_max_block_id is not None and block_number == current_max_block_id and transaction_index <= current_max_transaction_id:
                continue

            block_data = None
            if block_number not in grouped_events_data:
                block_data = {}
                grouped_events_data[block_number] = block_data
            else:
                block_data = grouped_events_data[block_number]

            transaction_data = None
            if transaction_index not in block_data:

                transaction = self.w3.eth.getTransaction(e['transactionHash'])

                transaction_data = {
                    'transaction': transaction,
                    'logs': list()
                }
                block_data[transaction_index] = transaction_data
            else:
                transaction_data = block_data[transaction_index]

            log_index = e['logIndex']
            args = {
                'path_id': e["args"]['path_id'],
                'count': e["args"]['count']
            }
            transaction_data['logs'].append((log_index, args))
        return grouped_events_data

    def process_dynamic_sc_function_call_parameter(self, dynamic_sc_call_id, transaction):
        # todo -  handle transaction, which involves a smart contract deployment with constructor parameters

        rel_name = 'dynamic_smart_contract_function_call_parameter'
        facts_file_path = self.facts_dir_path + rel_name + '.facts'

        transaction_to = transaction['transaction'].to
        transaction_input = transaction['transaction'].input
        if transaction_to in self.contract_address_to_contract:
            contract_item = self.contract_address_to_contract[transaction_to]
            contract = contract_item['contract']
            contract_name = contract_item['contract_id']

            function_name, parameters = get_function_name_and_parameters(contract, transaction_input)

            function_parameters = list()
            for p in parameters:
                function_parameters.append(p['type'])

            for p in parameters:
                parameter_name = p['name']
                parameter_value = p['val']

                c_name = self.contract_address_to_contract_info[contract_name]['contract_name']
                static_function_parameter_id = get_contract_full_function_parameter_id(c_name, function_name,
                                                                                       function_parameters,
                                                                                       parameter_name)

                d = {
                    'dynamic_smart_contract_call_id': str(dynamic_sc_call_id),
                    'static_function_parameter_id': static_function_parameter_id,
                    'value': str(parameter_value)
                }
                append_query_line_from_dic(d, rel_name, self.souffle_query_relations_metadata, facts_file_path)

        load_relation(rel_name, self.facts_dir_path, self.souffle_query_relations_metadata, self.relations_data)

    def process_dynamic_path(self, dynamic_sc_call_id, transaction):
        rel_name = 'dynamic_path'
        facts_file_path = self.facts_dir_path + rel_name + '.facts'

        logs = transaction['logs']
        logs = [v for v in logs]
        logs.sort(key=lambda t: int(t[0]), reverse=False)
        path_ids_list = list()
        for log in logs:
            log_pos = log[0]
            log_args = log[1]

            path_id = log_args['path_id']
            path_count = log_args['count']

            path_ids_list.append(path_id)

            # todo sort by log_pos before writing to file
            d = {
                'dynamic_smart_contract_call_id': str(dynamic_sc_call_id),
                'static_path_id': str(path_id),
                'order': str(log_pos),
                'path_count': str(path_count),
            }
            append_query_line_from_dic(d, rel_name, self.souffle_query_relations_metadata, facts_file_path)

        load_relation(rel_name, self.facts_dir_path, self.souffle_query_relations_metadata, self.relations_data)

    def process_dynamic_sc_call(self, dynamic_sc_call_id, block_id, transaction_id, transaction):
        rel_name = 'dynamic_smart_contract_call'
        facts_file_path = self.facts_dir_path + rel_name + '.facts'

        #hash_ = get_logs_hash(transaction)
        transaction_to = transaction['transaction'].to
        transaction_from = transaction['transaction']['from']
        transaction_input = transaction['transaction'].input

        # static_function_id = None

        # todo - constructor call on deployed contract without a to address is not supported yet
        contract_item = self.contract_address_to_contract[transaction_to]
        contract = contract_item['contract']
        contract_name = contract_item['contract_id']
        function_name, parameters = get_function_name_and_parameters(contract, transaction_input)

        function_parameters = list()
        for p in parameters:
            function_parameters.append(p['type'])

        c_name = self.contract_address_to_contract_info[contract_name]['contract_name']
        static_function_id = full_function_signature(c_name, function_name, function_parameters)

        d = {
            'smart_contract_call_id': str(dynamic_sc_call_id),
            'dynamic_contract_id': transaction_to if transaction_to is not None else 'NULL',
            'block_id': str(block_id),
            'transaction_id': str(transaction_id),
            'caller_address': transaction_from,
            'ether_start': 'not_yet_supported',

            # 'ether_end': 'not_yet_supported',
            'ether_end': str(self.w3.eth.getBalance(transaction_to)) if transaction_to is not None else 'NULL',

            'static_function_id': static_function_id if static_function_id is not None else 'NULL',
            #'static_full_path_id': str(hash_),
        }
        append_query_line_from_dic(d, rel_name, self.souffle_query_relations_metadata, facts_file_path)
        load_relation(rel_name, self.facts_dir_path, self.souffle_query_relations_metadata, self.relations_data)
        self.dynamic_sc_call_memory = self.get_dynamic_sc_call_memory()

    def get_dynamic_sc_call_memory(self):
        dynamic_sc_call = self.relations_data['dynamic_smart_contract_call']
        dynamic_sc_call_memory = {}
        for dynamic_sc_call_item in dynamic_sc_call:
            smart_contract_call_id = dynamic_sc_call_item['smart_contract_call_id']
            dynamic_sc_call_memory[smart_contract_call_id] = dynamic_sc_call_item

        return dynamic_sc_call_memory

    # def process_dynamic_contract_(self):
    #     # dynamic_contract
    #     rel_name = 'dynamic_contract'
    #     facts_file_path = self.facts_dir_path + rel_name + '.facts'
    #     dynamic_contract_data = self.relations_data[rel_name]
    #     for c_item in self.contracts.items():
    #         contract_id = c_item[0]
    #         contract_address = c_item[1].address
    #
    #         contract_found = False
    #         for d in dynamic_contract_data:
    #             if d['contract_id'] == contract_id:
    #                 contract_found = True
    #
    #         if not contract_found:
    #             d = {
    #                 'contract_id': contract_id,
    #                 'deployer_address': 'not_yet_supported',
    #                 'ether': 'not_yet_supported',
    #                 'contract_address': contract_address,
    #             }
    #             append_query_line_from_dic(d, rel_name, self.souffle_query_relations, facts_file_path)
    #
    #     load_relation(rel_name, self.facts_dir_path, self.souffle_query_relations, self.relations_data)

    def get_contract(self, contract_address):
        #contract_address = self.contract_address_to_contract_info[contract_name]['contract_address']
        address = self.w3.toChecksumAddress(contract_address)
        abi = self.contract_address_to_contract_info[contract_address]['contract_abi']
        myContract = self.w3.eth.contract(address=address, abi=abi)

        return myContract


pp = ProvenanceProcessor()
pp.run()






# def process_events(myContract, contract_name, full_event_name_to_event_details):
#     for contractEvent in myContract.events:
#         myfilter = contractEvent.createFilter(fromBlock=0, toBlock="latest")
#         eventlist = myfilter.get_all_entries()
#
#         for event in eventlist:
#             #   t = w3.eth.getTransactionByBlock(event["blockNumber"], event["transactionIndex"])
#
#             event_name = event["event"]
#             # print(event_name+"--------------------------------------------"+contract_name)
#             # if event_name.startswith("_provenance_call_"):
#             if event_name.startswith("_provenance_"):
#                 # print(event)
#
#                 full_event_name = contract_name + "_" + event_name
#
#                 if full_event_name not in full_event_name_to_event_details:
#                     args_names_list = []
#                     args_names_list.append("position")
#                     for arg_name in event["args"]:
#                         args_names_list.append(arg_name)
#
#                     full_event_name_to_event_details[full_event_name] = args_names_list
#
#                 args_names_list = full_event_name_to_event_details[full_event_name]
#                 print(", ".join(args_names_list))
#
#                 position = str(event["blockNumber"]) + "_" + str(event["transactionIndex"]) + "_" + str(
#                     event["logIndex"])
#
#                 args_values = []
#                 for arg_name in args_names_list:
#                     if arg_name == "position":
#                         args_values.append(position)
#                     else:
#                         args_values.append(str(event["args"][arg_name]))
#
#                 write_line_to_file("\t".join(args_values), facts_dir_path + full_event_name + ".facts", "a")
#
#                 print("\t".join(args_values))
#                 print()


# def write_socialite_query(full_event_name_to_event_details):
#     write_to_file("", socialite_dir_path + "query.py", "w")
#
#     for full_event_name in full_event_name_to_event_details:
#         event_args_str_list = []
#         args_names = full_event_name_to_event_details[full_event_name]
#         for arg_name in args_names:
#             event_args_str_list.append("String " + arg_name)
#
#         facts_file_path = facts_dir_path + full_event_name + '.facts'
#
#         write_line_to_file('print("reading ' + facts_file_path + '")', socialite_dir_path + "query.py", "a")
#
#         load_rel_cmd = socialite_str_symbol + full_event_name + '(' + ', '.join(event_args_str_list) + ').\n'
#         load_rel_cmd += full_event_name + '(' + ', '.join(args_names) + ') :- l=$read("' + facts_file_path + '"),\n'
#         load_rel_cmd += '(' + ', '.join(args_names) + ') = $split(l,"\\t").' + socialite_str_symbol + '\n'
#         print(load_rel_cmd)
#         print()
#
#         write_line_to_file(load_rel_cmd, socialite_dir_path + "query.py", "a")

"""
        filters = [   event.createFilter(fromBlock=log["block"], fromBlock=log["block"])
                        for event in myContract.events
                        if isinstance(event, contractEvent)]
         createFilter(fromBlock="latest", argument_filters={"arg1":10})
         contractEvent.processReceipt(receipt)

            
            print(event)
            print()
"""    

"""
filter = w3.eth.filter({"fromBlock": 0, "toBlock": w3.eth.blockNumber})
logs = w3.eth.getFilterLogs(filter.filter_id)
print(len(logs))
for log in logs:    
    contract_address = log["address"]
    if contract_address in contract_info:
        receipt = w3.eth.getTransactionReceipt(log["transactionHash"])
        contract_abi = contract_info[contract_address]["abi"]
        myContract = w3.eth.contract(address=contract_address, abi=contract_abi)
        
        #p = myContract.events.myEvent().processReceipt(receipt)
        for contractEvent in myContract.events:
            filters = [   event.createFilter(fromBlock=log["block"], fromBlock=log["block"])
                            for event in myContract.events
                            if isinstance(event, contractEvent)]
                            
            
            print(event)
            print()
            
        print(receipt)
        print()
        print()


"""

"""
filter = w3.eth.filter({"fromBlock": 0, "toBlock": w3.eth.blockNumber})
logs = w3.eth.getFilterLogs(filter.filter_id)
print(len(logs))
for log in logs:    
    contract_address = log["address"]
    if contract_address in contract_info:
        receipt = w3.eth.getTransactionReceipt(log["transactionHash"])
        contract_abi = contract_info[contract_address]["abi"]
        myContract = w3.eth.contract(address=contract_address, abi=contract_abi)
        
        #p = myContract.events.myEvent().processReceipt(receipt)
        for contractEvent in myContract.events:
            print(event)
            print()
            
        print(receipt)
        print()
        print()

"""
