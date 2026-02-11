
invariant noReentrancyDuringWithdrawals()
    forall(uint x in withdrawals) x == 0;

rule reentrancyGuardPreventsReentrancy() {
    call withdraw();
    
    // Check that we didn't re-enter
    assert nonReentrant == 0;
}
