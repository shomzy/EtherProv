import "./PathCounter.sol";
pragma solidity ^0.4.2;

contract VouchCoin  {

  address public owner;
  uint public totalSupply;
  uint public initialSupply;
  string public name;
  uint public decimals;
  string public standard = "VouchCoin";

  mapping (address => uint) public balanceOf;

  event Transfer(address indexed from, address indexed to, uint value);

  int _pc_counter = 0;
struct Uint_init {
    int path_id;
	uint count;
	uint is_init;	
  }
Uint_init  public _pc_current_path;
mapping(uint => uint) _pc_revert_paths;
event _pc_path(int path_id, uint count);
function _pc_init_all_transaction_data(int counter_init_val) public  {
  
	_pc_counter = counter_init_val;

  }
function _pc_inc_counter(int counter_inc) public returns (bool) {
	
	_pc_counter = _pc_counter + counter_inc;

	return false;
	
  }
function _pc_inc_transaction_path_count(int counter_inc) public  {	
	
	_pc_counter = _pc_counter + counter_inc;
	
  }
function _pc_reset_counter(int counter_reset) public  {
		
	_pc_counter = counter_reset;
		
  }
function _pc_flush_path_data() public  {

	emit _pc_path(_pc_counter, 1);

	_pc_counter = 0;
	
  }
function _pc_update_reverted_path_id(uint[] memory path_ids, uint size) public  {
  
	for (uint i=0; i<size; i++) {
	
		_pc_revert_paths[path_ids[i]] = 1;
		
	}	
	
  }


function get_batch_id() external view returns (uint256) { return 2; }

function VouchCoin() {
    owner = msg.sender;
    balanceOf[msg.sender] = 10000000000000000;
    totalSupply = 10000000000000000;
    name = "VouchCoin";_pc_inc_counter(6);
    decimals = 8;_pc_flush_path_data();
  }

  function balance(address user) public returns (uint) {_pc_inc_counter(5);
    _pc_flush_path_data();return balanceOf[user];
  }

  function transfer(address _to, uint _value)  {_pc_counter = 1;
    if (_to == 0x0) {
_pc_inc_counter(3);
_pc_flush_path_data();throw;
} else {

}

    if (balanceOf[owner] < _value) {
_pc_inc_counter(2);
_pc_flush_path_data();throw;
} else {

}

    if (balanceOf[_to] + _value < balanceOf[_to]) {
_pc_counter = _pc_counter + 1;_pc_flush_path_data();throw;
} else {

}


    balanceOf[owner] -= _value;
    balanceOf[_to] += _value;
    Transfer(owner, _to, _value);_pc_flush_path_data();
  }

  function () {
    _pc_flush_path_data();throw;
  }
}
