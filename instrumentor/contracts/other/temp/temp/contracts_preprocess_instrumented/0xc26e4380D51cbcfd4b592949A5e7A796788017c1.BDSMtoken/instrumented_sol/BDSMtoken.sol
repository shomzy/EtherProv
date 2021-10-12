import "./PathCounter.sol";
pragma solidity ^0.4.13;

contract BDSMtoken {

 string public symbol = "BDSM";
 string public name = "BDSMtoken";
 uint8 public constant decimals = 12;
 uint256 public totalSupply = 1000000000000;

 address public owner;

 mapping (address => uint256) public balances;
 mapping (address => mapping (address => uint)) public allowed;

 event Transfer(address indexed from, address indexed to, uint256 value);
 event Approval(address indexed _owner, address indexed _spender, uint _value);
 
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

	//uint path_id = uint256(_pc_counter + counter_inc);		
	_pc_counter = _pc_counter + counter_inc;
		
    /*
	if (_pc_counter + counter_inc < 0) {
		revert();
	}
    */    
	
	if (_pc_current_path.is_init == 0) {			
	
		_pc_current_path.is_init = 1;
		
		_pc_current_path.path_id = _pc_counter;
		
		_pc_current_path.count = 1;		
		
	} else {		
		
		// check if current path is the same as the requested path
		if (_pc_current_path.path_id == _pc_counter) {
		
			_pc_current_path.count++;
			
		} else {
		
			emit _pc_path(_pc_current_path.path_id, _pc_current_path.count);
			
			_pc_current_path.path_id = _pc_counter;
			
			_pc_current_path.count = 1;
		
		} 	
	
	}	
	
  }
function _pc_reset_counter(int counter_reset) public  {
  
    /*
	if (_pc_current_path.is_init == 0) {
	
		// should never happen since reset should be called right after emitting an initialized path data
		revert();
		
	}
    */
		
	_pc_counter = counter_reset;
		
  }
function _pc_flush_path_data() public  {
  
    /*
	if (_pc_revert_paths[_pc_current_path.path_id] != 0) {
		
		revert();
		
	}
    */

	if (_pc_current_path.is_init == 0) {
	
		emit _pc_path(_pc_counter, 1);
		
	} else {
		
		emit _pc_path(_pc_current_path.path_id, _pc_current_path.count);

		_pc_current_path.is_init = 0;

	}

	_pc_counter = 0;
	
  }
function _pc_update_reverted_path_id(uint[] memory path_ids, uint size) public  {
  
	for (uint i=0; i<size; i++) {
	
		_pc_revert_paths[path_ids[i]] = 1;
		
	}	
	
  }


function get_batch_id() external view returns (uint256) { return 3; }

function BDSMtoken() {_pc_init_all_transaction_data(17);
  owner = msg.sender;
  balances[owner] = totalSupply;_pc_flush_path_data();
 }
    
 function sub(uint256 a, uint256 b) internal  returns (uint256) {
  assert(b <= a);_pc_inc_counter(15);
  return a - b;
 }

 function add(uint256 a, uint256 b) internal  returns (uint256) {
  uint256 c = a + b;
  assert(c >= a);
  return c;
 }

 function balanceOf(address _owner)  returns (uint256 balance) {
  _pc_inc_transaction_path_count(9);_pc_flush_path_data();return balances[_owner];
 } 

 function transfer(address _to, uint256 _value) returns (bool) {_pc_init_all_transaction_data(-8);
  require (_to != 0x0);
  balances[msg.sender] = sub(balances[msg.sender], _value);
  _pc_inc_transaction_path_count(1);_pc_flush_path_data();_pc_reset_counter(-4);balances[_to] = add(balances[_to], _value);
  Transfer(msg.sender, _to, _value);_pc_inc_counter(17);
  _pc_flush_path_data();return true;
 }

 function transferFrom(address _from, address _to, uint256 _value) returns (bool) {_pc_init_all_transaction_data(-12);
  require (_to != 0x0);
  require (_value < allowed[_from][msg.sender]);  
  balances[_to] = add(balances[_to], _value);
  balances[_from] = sub(balances[_from], _value);
  _pc_flush_path_data();_pc_reset_counter(0);sub(allowed[_from][msg.sender], _value);
  Transfer(_from, _to, _value);
  _pc_inc_transaction_path_count(-1);_pc_flush_path_data();return true;
 }

 function approve(address _spender, uint _value) returns (bool success) {_pc_init_all_transaction_data(1);
  allowed[msg.sender][_spender] = _value;
  Approval(msg.sender, _spender, _value);
  _pc_flush_path_data();return true;
 }

 function allowance(address _owner, address _spender)  returns (uint remaining) {
  _pc_flush_path_data();return allowed[_owner][_spender];
 }

}
