
invariant ownerIsNotZero()
    owner() != 0;

rule onlyOwnerCanCallRestrictedFunctions(address caller) {
    require caller != owner();
    
    // Should revert
    renounceOwnership@with(caller);
    assert lastReverted;
}
