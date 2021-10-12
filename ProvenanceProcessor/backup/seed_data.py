# from web3 import Web3, HTTPProvider, IPCProvider, WebsocketProvider
# import json
# import uuid
#
#
#
#
# w3 = Web3(HTTPProvider("http://127.0.0.1:7545"))
#
#
#
# contract_address_to_contract_details = json.loads(open("../../data/address_to_contract_details.data").read())
# contract_name_to_contract_details = {}
#
# for contract_address in contract_address_to_contract_details:
#     contract_name = contract_address_to_contract_details[contract_address]["contract_name"]
#     contract_abi = contract_address_to_contract_details[contract_address]["contract_abi"]
#
#     contract_name_to_contract_abi[contract_name] = {"contract_address":contract_address,
#                                                                                 "contract_abi":contract_abi}
#
#
# session_id = str(uuid.uuid4())
# scenario_id = str(uuid.uuid4())
#
# for contract_name in contract_name_to_contract_details:
#
#     myContract = w3.eth.contract(address=contract_name_to_contract_details[XXXX]["contract_address"], abi=contract_name_to_contract_details[XXXX]["contract_abi"])
#
#     for contractEvent in myContract.events:
#         myfilter = contractEvent.createFilter(fromBlock=0,toBlock="latest");
#         eventlist = myfilter.get_all_entries()
#
#         for event in eventlist:
#             #   t = w3.eth.getTransactionByBlock(event["blockNumber"], event["transactionIndex"])
#
#             event_name = event["event"]
#             #print(event_name)
#             if event_name.startswith("_provenance_call_"):
#                 #print(event)
#                 position = str(event["blockNumber"] ) + "_" + str(event["transactionIndex"])  + "_" + str(event["logIndex"])
#
#                 full_event_name = contract_name + "_" + event_name
#
#                 if full_event_name not in full_event_name_to_event_details:
#
#                     args_list = []
#                     args_list.append(("position", position))
#                     for arg_name in event["args"]:
#                         arg_details = (arg_name, event["args"][arg_name])
#                         args_list.append(arg_details)
#
#                     full_event_name_to_event_details[full_event_name] = args_list
#
#                 print(full_event_name)
#
#                 args_names = []
#                 args_list = full_event_name_to_event_details[full_event_name]
#                 for arg_details in args_list:
#                     args_names.append(arg_details[0])
#
#                 print(", ".join(args_names))
#
#                 args_values = []
#                 for arg_details in args_list:
#                     args_values.append(str(arg_details[1]))
#
#                 write_line_to_file("\t".join(args_values), data_facts_dir_path + full_event_name + ".facts", "a")
#
#
# write_to_file("",self.data_dir_path + "example.dl", "w")
#
# for full_event_name in full_event_name_to_event_details:
#     event_args_str_list = []
#     event_args = full_event_name_to_event_details[full_event_name]
#     for event_arg in event_args:
#         event_args_str_list.append(event_arg[0] + ":symbol")
#
#     decl = ".decl " + full_event_name + "(" + ", ".join(event_args_str_list) + ")"
#
#     write_line_to_file(decl, self.data_dir_path + "example.dl", "a")
#     write_line_to_file(".input edge\n", self.data_dir_path + "example.dl", "a")
#
#
#
#
#
#
#
#
#     """
#         filters = [   event.createFilter(fromBlock=log["block"], fromBlock=log["block"])
#                         for event in myContract.events
#                         if isinstance(event, contractEvent)]
#          createFilter(fromBlock="latest", argument_filters={"arg1":10})
#          contractEvent.processReceipt(receipt)
#
#
#             print(event)
#             print()
# """
#
# """
# filter = w3.eth.filter({"fromBlock": 0, "toBlock": w3.eth.blockNumber})
# logs = w3.eth.getFilterLogs(filter.filter_id)
# print(len(logs))
# for log in logs:
#     contract_address = log["address"]
#     if contract_address in contract_info:
#         receipt = w3.eth.getTransactionReceipt(log["transactionHash"])
#         contract_abi = contract_info[contract_address]["abi"]
#         myContract = w3.eth.contract(address=contract_address, abi=contract_abi)
#
#         #p = myContract.events.myEvent().processReceipt(receipt)
#         for contractEvent in myContract.events:
#             filters = [   event.createFilter(fromBlock=log["block"], fromBlock=log["block"])
#                             for event in myContract.events
#                             if isinstance(event, contractEvent)]
#
#
#             print(event)
#             print()
#
#         print(receipt)
#         print()
#         print()
#
#
# """
#
# """
# filter = w3.eth.filter({"fromBlock": 0, "toBlock": w3.eth.blockNumber})
# logs = w3.eth.getFilterLogs(filter.filter_id)
# print(len(logs))
# for log in logs:
#     contract_address = log["address"]
#     if contract_address in contract_info:
#         receipt = w3.eth.getTransactionReceipt(log["transactionHash"])
#         contract_abi = contract_info[contract_address]["abi"]
#         myContract = w3.eth.contract(address=contract_address, abi=contract_abi)
#
#         #p = myContract.events.myEvent().processReceipt(receipt)
#         for contractEvent in myContract.events:
#             print(event)
#             print()
#
#         print(receipt)
#         print()
#         print()
#
# """
# #for i in range(0, w3.eth.blockNumber):
# #    block = w3.eth.getBlock(i)
# #    for transaction in block.transactions:
# #        print(transaction)
