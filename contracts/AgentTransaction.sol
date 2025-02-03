// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract AgentTransaction {
    struct Transaction {
        address sender;
        address receiver;
        string data;
        uint256 timestamp;
    }

    Transaction[] public transactions;
    
    function addTransaction(
        address _receiver,
        string memory _data
    ) public returns (uint) {
        transactions.push(Transaction(
            msg.sender,
            _receiver,
            _data,
            block.timestamp
        ));
        return transactions.length - 1;
    }

    function validateTransaction(
        uint _txIndex
    ) public view returns (bool) {
        require(_txIndex < transactions.length, "Invalid transaction index");
        Transaction memory tx = transactions[_txIndex];
        return tx.sender != address(0);
    }
}