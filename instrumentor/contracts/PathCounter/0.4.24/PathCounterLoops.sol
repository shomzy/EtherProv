pragma solidity ^0.4.24;
//pragma experimental ABIEncoderV2;


contract PathCounter {  

  
  // current transaction counter
  int _pc_counter = 0;
  
  struct Uint_init {
    int path_id;
	uint count;
	uint is_init;	
  }
  Uint_init  public _pc_current_path;
  
  mapping(uint => uint) _pc_revert_paths;
  
  // dynamic path event
  event _pc_path(int path_id, uint count);
	


  ////////////////////////////////////////////////////////////////////////////////////////////////////
  //
  //				init all transaction data
  //
  ////////////////////////////////////////////////////////////////////////////////////////////////////  
  function _pc_init_all_transaction_data(int counter_init_val) public  {
  
	_pc_counter = counter_init_val;

  }
  
  
    ////////////////////////////////////////////////////////////////////////////////////////////////////
  //
  //				inc transaction counter
  //
  ////////////////////////////////////////////////////////////////////////////////////////////////////  
  function _pc_inc_counter(int counter_inc) public returns (bool) {
	
	_pc_counter = _pc_counter + counter_inc;

	return false;
	
  }
  
  
      ////////////////////////////////////////////////////////////////////////////////////////////////////
  //
  //				inc transaction path count
  //
  ////////////////////////////////////////////////////////////////////////////////////////////////////  
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
  
  
    ////////////////////////////////////////////////////////////////////////////////////////////////////
  //
  //				reset transaction current path counter
  //
  ////////////////////////////////////////////////////////////////////////////////////////////////////  
  function _pc_reset_counter(int counter_reset) public  {
  
    /*
	if (_pc_current_path.is_init == 0) {
	
		// should never happen since reset should be called right after emitting an initialized path data
		revert();
		
	}
    */
		
	_pc_counter = counter_reset;
		
  }
  
      ////////////////////////////////////////////////////////////////////////////////////////////////////
  //
  //				flush path data
  //
  ////////////////////////////////////////////////////////////////////////////////////////////////////  
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
  
      ////////////////////////////////////////////////////////////////////////////////////////////////////
  //
  //				update reverted path id
  //
  ////////////////////////////////////////////////////////////////////////////////////////////////////  
  function _pc_update_reverted_path_id(uint[] memory path_ids, uint size) public  {
  
	for (uint i=0; i<size; i++) {
	
		_pc_revert_paths[path_ids[i]] = 1;
		
	}	
	
  }
  
}
