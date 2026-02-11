
invariant totalSupplyIsSumOfBalances()
    totalSupply() == sum(balanceOf(_));

invariant noZeroAddressTransfers(address to)
    to != 0;

rule transferFromWorksAsIntended(address from, address to, uint256 amount) {
    uint256 allowanceBefore = allowance(from, this);
    uint256 balanceFromBefore = balanceOf(from);
    uint256 balanceToBefore = balanceOf(to);
    
    transferFrom(from, to, amount);
    
    uint256 allowanceAfter = allowance(from, this);
    uint256 balanceFromAfter = balanceOf(from);
    uint256 balanceToAfter = balanceOf(to);
    
    assert allowanceAfter == allowanceBefore - amount;
    assert balanceFromAfter == balanceFromBefore - amount;
    assert balanceToAfter == balanceToBefore + amount;
}
