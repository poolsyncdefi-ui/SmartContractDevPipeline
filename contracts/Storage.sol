// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title Storage
 * @dev Store et retrieve une valeur
 */
contract Storage {
    uint256 private _value;

    event ValueChanged(uint256 oldValue, uint256 newValue);

    /**
     * @dev Store une valeur
     * @param value La valeur à stocker
     */
    function store(uint256 value) public {
        uint256 oldValue = _value;
        _value = value;
        emit ValueChanged(oldValue, value);
    }

    /**
     * @dev Return la valeur stockée
     * @return La valeur stockée
     */
    function retrieve() public view returns (uint256) {
        return _value;
    }
}
