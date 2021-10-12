pragma solidity ^0.4.24;
pragma experimental ABIEncoderV2;


contract Client {

	BalanceManager _balance_manager;
	Client _other_client;
  
	constructor(address balance_manager_address, address other_client_address) public {
		_owner = msg.sender;               
		_balance = BalanceManager(balance_manager_address);
		_other_client = Client(other_client_address);
	}
  
	function transferFunds() {		
		int balance = _balance_manager.getBalance();
		if (balance > 100) {
			//_owner.call.value(100).gas(20317)();
			_owner.call.value(100)();
		}
		_balance_manager.subFromBalance(100);		
	}
}


contract BalanceManager {
	int _balance = 0;
  
	constructor(int balance) public { _balance = balance; }
	
	function getBalance() returns (int) { return _balance; }

	function subFromBalance(int val) { _balance = _balance - val;	}
}