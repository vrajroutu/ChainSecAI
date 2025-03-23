from web3 import Web3

class SmartContract:
    def __init__(self, contract_address: str, abi: dict):
        self.w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
        self.contract = self.w3.eth.contract(
            address=contract_address,
            abi=abi
        )

    def validate_transaction(self, tx_data: dict) -> bool:
        return self.contract.functions.validateTransaction(
            tx_data['sender'],
            tx_data['receiver'],
            tx_data['data']
        ).call()

    def add_to_chain(self, tx_data: dict):
        tx_hash = self.contract.functions.addTransaction(
            tx_data['sender'],
            tx_data['receiver'],
            tx_data['data']
        ).transact()
        return self.w3.eth.wait_for_transaction_receipt(tx_hash)