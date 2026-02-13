// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract SimpleNFT {
    string public name = "TestNFT";
    string public symbol = "TNFT";
    uint256 public totalSupply = 10000;
    
    event Minted(address indexed to, uint256 tokenId);
    
    function mint(address to, uint256 tokenId) public {
        emit Minted(to, tokenId);
    }
    
    function transfer(address from, address to, uint256 tokenId) public pure {
        require(from != address(0), "Invalid sender");
        require(to != address(0), "Invalid recipient");
    }
}
