import "./PathCounter.sol";
pragma solidity ^0.4.17;

contract Owned 
{
    address newOwner;
    address owner = msg.sender;
    address creator = msg.sender;
    
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


function get_batch_id() external view returns (uint256) { return 1; }

function changeOwner(address addr)
    public
    {_pc_inc_counter(156);
        if(isOwner())
        {
            newOwner = addr;
        }
 else {

}_pc_flush_path_data();
    }
    
    function confirmOwner()
    public
    {
        if(msg.sender==newOwner)
        {
            owner=newOwner;_pc_inc_counter(152);
        }
 else {

_pc_inc_counter(151);}_pc_flush_path_data();
    }
    
    
    function isOwner()
    internal
    
    returns(bool)
    {
        _pc_inc_counter(-1);return owner == msg.sender;
    }
    
    function WthdrawAllToCreator()
    public
    payable
    {
        if(msg.sender==creator)
        {
            creator.transfer(this.balance);_pc_inc_counter(148);
        }
 else {

_pc_inc_counter(147);}_pc_flush_path_data();
    }
    
    function WthdrawToCreator(uint val)
    public
    payable
    {
        if(msg.sender==creator)
        {
            creator.transfer(val);_pc_inc_counter(1);
        }
 else {

}_pc_counter = _pc_counter + 143;_pc_flush_path_data();
    }
    
    function WthdrawTo(address addr,uint val)
    public
    payable
    {
        if(msg.sender==creator)
        {
            addr.transfer(val);_pc_inc_counter(140);
        }
 else {

_pc_inc_counter(139);}_pc_flush_path_data();
    }
}

contract EthDeposit is Owned
{
    address public Manager;
    
    address public NewManager;
    
    uint public SponsorsQty;
    
    uint public CharterCapital;
    
    uint public ClientQty;
    
    uint public PrcntRate = 5;
    
    bool paymentsAllowed;
    
    struct Lender
    {
        uint LastLendTime;
        uint Amount;
        uint Reserved;
    }
    
    mapping (address => uint) public Sponsors;
    
    mapping (address => Lender) public Lenders;
    
    event StartOfPayments(address indexed calledFrom, uint time);
    
    event EndOfPayments(address indexed calledFrom, uint time);
    
    function init(address _manager)
    public
    {
        owner = msg.sender;
        Manager = _manager;
    }
    
    function isManager()
    private
    
    returns (bool)
    {
        return(msg.sender==Manager);
    }
    
    function canManage()
    private
    
    returns (bool)
    {
        return(msg.sender==Manager||msg.sender==owner);
    }
    
    function ChangeManager(address _newManager)
    public
    {
        if(canManage())
        { 
            NewManager = _newManager;
        }
 else {

}
    }

    function ConfirmManager()
    public
    {
        if(msg.sender==NewManager)
        {
            Manager=NewManager;
        }
 else {

}
    }
    
    function StartPaymens()
    public
    {
        if(canManage())
        { 
            AuthorizePayments(true);
            StartOfPayments(msg.sender, now);
        }
 else {

}
    }
    
    function StopPaymens()
    public
    {
        if(canManage())
        { 
            AuthorizePayments(false);
            EndOfPayments(msg.sender, now);
        }
 else {

}
    }address owner;
    
    function AuthorizePayments(bool val)
    public
    {
        if(isOwner())
        {
            paymentsAllowed = val;
        }
 else {

}
    }
    
    function SetPrcntRate(uint val)
    public
    {
        if(canManage())
        {
            if(val!=PrcntRate)
            {
                if(val>=1)
                {
                    PrcntRate = val;  
                }
 else {

}
            }
 else {

}
        }
 else {

}
    }
    
    function()
    public
    payable
    {
        ToSponsor();
    }
    
    function ToSponsor() 
    public
    payable
    {
        if(msg.value>= 1 ether)
        {
            if(Sponsors[msg.sender]==0){
SponsorsQty++;
} else {

}

            Sponsors[msg.sender]+=msg.value;
            CharterCapital+=msg.value;
        }  else {

}
  
    }
    
    function WithdrawToSponsor(address _addr, uint _wei) 
    public 
    payable
    {
        if(Sponsors[_addr]>0)
        {
            if(isOwner())
            {
                 if(_addr.send(_wei))
                 {
                   if(CharterCapital>=_wei){
CharterCapital-=_wei;
}
                   else {
CharterCapital=0;
}
                 }
 else {

}
            }
 else {

}
        }
 else {

}
    }
    
    function Deposit() 
    public 
    payable
    {
        FixProfit();//fix time inside
        Lenders[msg.sender].Amount += msg.value;
    }
    
    function CheckProfit(address addr) 
    public 
     
    returns(uint)
    {
        return ((Lenders[addr].Amount/100)*PrcntRate)*((now-Lenders[addr].LastLendTime)/1 days);
    }
    
    function FixProfit()
    public
    {
        if(Lenders[msg.sender].Amount>0)
        {
            Lenders[msg.sender].Reserved += CheckProfit(msg.sender);
        }
 else {

}
        Lenders[msg.sender].LastLendTime=now;
    }
    
    function WitdrawLenderProfit() 
    public 
    payable
    {
        if(paymentsAllowed)
        {
            FixProfit();
            uint profit = Lenders[msg.sender].Reserved;
            Lenders[msg.sender].Reserved = 0;
            msg.sender.transfer(profit);
        }
 else {

}
    }
    
}
