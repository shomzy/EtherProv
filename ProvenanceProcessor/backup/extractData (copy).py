# from web3 import Web3, HTTPProvider, IPCProvider, WebsocketProvider
# import json
#
#
# def write_line_to_file(line_data, file_name, write_attr):
#     write_to_file(line_data+"\n", file_name, write_attr)
#
# def write_to_file(line_data, file_name, write_attr):
#     with open(file_name, write_attr) as myfile:
#         myfile.write(line_data)
#
#
#
#
# w3 = Web3(HTTPProvider("http://127.0.0.1:7545"))
#
# data_dir_path = "../../data/"
# souffle_dir_path = "../../souffle/"
# souffle_facts_dir_path = "../../data/facts/"
#
# full_event_name_to_event_details = {}
#
#
# contract_info = json.loads(open(data_dir_path + "address_to_contract_details.data").read())
#
# for contract_address in contract_info:
#     contract_name = contract_info[contract_address]["contract_name"]
#     contract_abi = contract_info[contract_address]["contract_abi"]
#
#     myContract = w3.eth.contract(address=contract_address, abi=contract_abi)
#
#     for contractEvent in myContract.events:
#         myfilter = contractEvent.createFilter(fromBlock=0,toBlock="latest");
#         eventlist = myfilter.get_all_entries()
#
#
#         for event in eventlist:
#             #   t = w3.eth.getTransactionByBlock(event["blockNumber"], event["transactionIndex"])
#
#             event_name = event["event"]
#             #print(event_name+"--------------------------------------------"+contract_name)
#             if event_name.startswith("_provenance_call_"):
#                 #print(event)
#
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
#
#                 args_names_list = full_event_name_to_event_details[full_event_name]
#                 print(", ".join(args_names_list))
#
#                 position = str(event["blockNumber"] ) + "_" + str(event["transactionIndex"])  + "_" + str(event["logIndex"])
#
#                 args_values = []
#                 for arg_name in args_names_list:
#                     if arg_name =="position":
#                         args_values.append(position)
#                     else:
#                         args_values.append(str(event["args"][arg_name]))
#
#                 write_line_to_file("\t".join(args_values), souffle_facts_dir_path + full_event_name + ".facts", "a")
#
#                 print("\t".join(args_values))
#                 print()
#
#
# write_to_file("",souffle_dir_path + "query.dl", "w")
#
# for full_event_name in full_event_name_to_event_details:
#     event_args_str_list = []
#     args_names = full_event_name_to_event_details[full_event_name]
#     for arg_name in args_names:
#         event_args_str_list.append(arg_name + ":symbol")
#
#     decl = ".decl " + full_event_name + "(" + ", ".join(event_args_str_list) + ")"
#
#     write_line_to_file(decl, souffle_dir_path + "query.dl", "a")
#     write_line_to_file(".input " + full_event_name + "\n", souffle_dir_path + "query.dl", "a")
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
