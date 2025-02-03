class Blockchain:
    def __init__(self, reputation_contract_address: str = None):
        self.chain = []
        self.pending_transactions = []
        self.reputation_contract = reputation_contract_address
        # ... existing init code ...

    def update_agent_reputation(self, agent_address: str, 
                              task_success: bool,
                              response_time: int,
                              validation_score: int,
                              peer_rating: int = 0):
        """
        Update agent reputation through smart contract
        """
        contract = SmartContract(
            self.reputation_contract,
            self._load_reputation_abi()
        )
        
        tx_hash = contract.contract.functions.updateReputation(
            agent_address,
            task_success,
            response_time,
            validation_score,
            peer_rating
        ).transact()
        
        return self.w3.eth.wait_for_transaction_receipt(tx_hash)

    def get_agent_reputation(self, agent_address: str) -> dict:
        """
        Retrieve agent reputation from blockchain
        """
        contract = SmartContract(
            self.reputation_contract,
            self._load_reputation_abi()
        )
        
        score = contract.contract.functions.calculateReputationScore(agent_address).call()
        raw_rep = contract.contract.functions.reputations(agent_address).call()
        
        return {
            'score': score,
            'total_tasks': raw_rep[0],
            'successful_tasks': raw_rep[1],
            'validation_accuracy': raw_rep[2],
            'avg_response_time': raw_rep[3],
            'peer_reviews': raw_rep[4],
            'peer_score': raw_rep[5]
        }