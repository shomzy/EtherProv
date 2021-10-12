pragma solidity ^0.5.0;
//pragma solidity ^0.4.21;
//pragma solidity ^0.4.19;
//pragma experimental ABIEncoderV2;


contract PathCounter {
  
  address public _owner;  
  
  // current transaction counter
  int _counter;
  
  struct Uint_init {
    uint path_id;
	uint count;
	uint is_init;	
  }
  
  mapping(uint => uint) _revert_paths;
  
  Uint_init  public _current_path;
  
	
	// dynamic path event
	event path(uint path_id, uint count);
	
  
  
  ////////////////////////////////////////////////////////////////////////////////////////////////////
  //
  //				constructor
  //
  ////////////////////////////////////////////////////////////////////////////////////////////////////  
  
  constructor() public {
    
	_owner = msg.sender;   
	
  }


  ////////////////////////////////////////////////////////////////////////////////////////////////////
  //
  //				init all transaction data
  //
  ////////////////////////////////////////////////////////////////////////////////////////////////////  
  function init_all_transaction_data(int counter_init_val) external  {
  
	_counter = counter_init_val;
	
	_current_path.is_init = 0;
	
  }
  
  
    ////////////////////////////////////////////////////////////////////////////////////////////////////
  //
  //				inc transaction counter
  //
  ////////////////////////////////////////////////////////////////////////////////////////////////////  
  function inc_counter(int counter_inc) external returns (bool) {
	
	_counter = _counter + counter_inc;

	return false;
	
  }
  
  
      ////////////////////////////////////////////////////////////////////////////////////////////////////
  //
  //				inc transaction path count
  //
  ////////////////////////////////////////////////////////////////////////////////////////////////////  
  function inc_transaction_path_count(int counter_inc) external  {	
		
	uint path_id = uint256(_counter + counter_inc);	
	
	if (_counter + counter_inc < 0) {
		revert();
	}
	
	if (_current_path.is_init == 0) {			
	
		_current_path.is_init = 1;
		
		_current_path.path_id = path_id;
		
		_current_path.count = 1;		
		
	} else {		
		
		// check if current path is the same as the requested path
		if (_current_path.path_id == path_id) {
		
			_current_path.count++;
			
		} else {
		
			emit path(_current_path.path_id, _current_path.count);
			
			_current_path.path_id = path_id;
			
			_current_path.count = 1;
		
		} 	
	
	}	
	
  }
  
  
    ////////////////////////////////////////////////////////////////////////////////////////////////////
  //
  //				reset transaction current path counter
  //
  ////////////////////////////////////////////////////////////////////////////////////////////////////  
  function reset_counter(int counter_reset) external  {
  
	if (_current_path.is_init == 0) {
	
		// should never happen since reset should be called right after emitting an initialized path data
		revert();
		
	}
		
	_counter = counter_reset;
		
  }
  
      ////////////////////////////////////////////////////////////////////////////////////////////////////
  //
  //				flush path data
  //
  ////////////////////////////////////////////////////////////////////////////////////////////////////  
  function flush_path_data() external  {
  
	if (_revert_paths[_current_path.path_id] != 0) {
		
		revert();
		
	}
		
	emit path(_current_path.path_id, _current_path.count);
	
	_current_path.is_init = 0;
	
  }
  
      ////////////////////////////////////////////////////////////////////////////////////////////////////
  //
  //				reset transaction current path counter
  //
  ////////////////////////////////////////////////////////////////////////////////////////////////////  
  function update_reverted_path_id(uint[] calldata path_ids, uint size) external  {
  
	for (uint i=0; i<size; i++) {
	
		_revert_paths[path_ids[i]] = 1;
		
	}	
	
  }
  
}
