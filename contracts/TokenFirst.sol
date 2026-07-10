// SPDX-License-Identifier: MIT
pragma solidity ^0.8.14;

/// @title IERC20 - the standard ERC-20 interface
/// @notice Any contract implementing this interface can be recognised as a
///         token by wallets, exchanges and block explorers.
interface IERC20 {
    function totalSupply() external view returns (uint256);

    function balanceOf(address account) external view returns (uint256);

    function allowance(address owner, address spender) external view returns (uint256);

    function transfer(address recipient, uint256 amount) external returns (bool);

    function approve(address spender, uint256 amount) external returns (bool);

    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
}

/// @title FirstToken - a minimal ERC-20 token
/// @notice The entire supply is minted to the deployer, who acts as the
///         treasury and distributes tokens to buyers.
/// @dev Solidity 0.8+ reverts automatically on overflow and underflow,
///      so a SafeMath library is no longer needed.
contract FirstToken is IERC20 {
    string public name = "SaraToken";
    string public symbol = "SAR";
    uint8 public decimals = 10;

    uint256 private _totalSupply;

    mapping(address => uint256) private _balances;
    mapping(address => mapping(address => uint256)) private _allowances;

    /// @notice Mints the full supply to the deployer.
    /// @dev 10^12 base units / 10^10 decimals = 100 whole tokens.
    constructor() {
        _totalSupply = 1_000_000_000_000;
        _balances[msg.sender] = _totalSupply;
        emit Transfer(address(0), msg.sender, _totalSupply);
    }

    function totalSupply() public view override returns (uint256) {
        return _totalSupply;
    }

    function balanceOf(address tokenOwner) public view override returns (uint256) {
        return _balances[tokenOwner];
    }

    function transfer(address recipient, uint256 numTokens) public override returns (bool) {
        require(recipient != address(0), "ERC20: transfer to the zero address");
        require(numTokens <= _balances[msg.sender], "ERC20: insufficient balance");

        _balances[msg.sender] -= numTokens;
        _balances[recipient] += numTokens;

        emit Transfer(msg.sender, recipient, numTokens);
        return true;
    }

    function approve(address delegate, uint256 numTokens) public override returns (bool) {
        require(delegate != address(0), "ERC20: approve to the zero address");

        _allowances[msg.sender][delegate] = numTokens;

        emit Approval(msg.sender, delegate, numTokens);
        return true;
    }

    function allowance(address owner, address delegate) public view override returns (uint256) {
        return _allowances[owner][delegate];
    }

    function transferFrom(address owner, address buyer, uint256 numTokens) public override returns (bool) {
        require(buyer != address(0), "ERC20: transfer to the zero address");
        require(numTokens <= _balances[owner], "ERC20: insufficient balance");
        require(numTokens <= _allowances[owner][msg.sender], "ERC20: insufficient allowance");

        _balances[owner] -= numTokens;
        _allowances[owner][msg.sender] -= numTokens;
        _balances[buyer] += numTokens;

        emit Transfer(owner, buyer, numTokens);
        return true;
    }
}
