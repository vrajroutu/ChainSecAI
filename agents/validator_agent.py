from typing import Dict, Optional, Tuple
from langchain.tools import BaseTool
from langchain.agents import AgentExecutor
from src.agents.base_agent import ChainSecAgent
from src.blockchain.core import Blockchain
from src.utils.crypto import hash_data, validate_signature

class ValidationTools:
    class TransactionStructureValidator(BaseTool):
        name = "Transaction Structure Validator"
        description = "Validates transaction format and required fields"
        
        def _run(self, transaction: Dict) -> Tuple[bool, str]:
            required_fields = {'sender', 'receiver', 'data', 'timestamp'}
            if not all(field in transaction for field in required_fields):
                return False, "Missing required fields"
            return True, "Valid transaction structure"

    class CryptographicValidator(BaseTool):
        name = "Cryptographic Validator"
        description = "Verifies cryptographic signatures and hashes"

        def _run(self, transaction: Dict, public_key: str) -> Tuple[bool, str]:
            try:
                data_hash = hash_data(transaction['data'])
                if not validate_signature(public_key, data_hash, transaction['signature']):
                    return False, "Invalid cryptographic signature"
                return True, "Cryptographic validation passed"
            except KeyError:
                return False, "Missing cryptographic elements"

class ValidatorAgent(ChainSecAgent):
    def __init__(self, blockchain: Blockchain, smart_contract_address: str):
        tools = [
            ValidationTools.TransactionStructureValidator(),
            ValidationTools.CryptographicValidator()
        ]
        super().__init__("ValidatorAgent-v1", tools, blockchain)
        self.smart_contract_address = smart_contract_address
        self.validation_threshold = 3  # Number of validations required
        
    def validate_transaction(self, transaction: Dict) -> Dict:
        """
        Perform multi-stage validation of a transaction
        Returns validation report with status and reasons
        """
        report = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'validations_passed': 0
        }

        # Structural validation
        structure_valid, message = self.tools[0]._run(transaction)
        if not structure_valid:
            report['valid'] = False
            report['errors'].append(f"Structural error: {message}")
            return report
        report['validations_passed'] += 1

        # Cryptographic validation
        crypto_valid, message = self.tools[1]._run(
            transaction, 
            transaction.get('sender_public_key', '')
        )
        if not crypto_valid:
            report['valid'] = False
            report['errors'].append(f"Crypto error: {message}")
            return report
        report['validations_passed'] += 1

        # Smart contract validation
        sc_valid = self.validate_via_smart_contract(transaction)
        if not sc_valid:
            report['valid'] = False
            report['errors'].append("Smart contract validation failed")
            return report
        report['validations_passed'] += 1

        # Consensus check (mock implementation)
        if not self.check_network_consensus(transaction):
            report['warnings'].append("Consensus verification pending")
            
        return report

    def validate_via_smart_contract(self, transaction: Dict) -> bool:
        """Interact with blockchain smart contract for validation"""
        from src.blockchain.smart_contracts import SmartContract
        
        sc = SmartContract(
            contract_address=self.smart_contract_address,
            abi=self._load_contract_abi()
        )
        return sc.validate_transaction(transaction)

    def check_network_consensus(self, transaction: Dict) -> bool:
        """Check if transaction exists in majority of network nodes"""
        # Mock implementation - would connect to multiple nodes in real scenario
        return self.blockchain.hash(self.blockchain.last_block) == transaction.get('block_hash', '')

    def _load_contract_abi(self) -> Dict:
        """Load smart contract ABI from file"""
        # Implementation would load actual ABI JSON
        return {
            "validateTransaction": {
                "inputs": [{"name": "txData", "type": "bytes"}],
                "name": "validateTransaction",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "view",
                "type": "function"
            }
        }

    def process_pending_transactions(self) -> None:
        """Main validation workflow for pending transactions"""
        for tx in self.blockchain.pending_transactions:
            validation_report = self.validate_transaction(tx)
            if validation_report['valid']:
                self._finalize_transaction(tx)
            else:
                self._reject_transaction(tx, validation_report)

    def _finalize_transaction(self, transaction: Dict) -> None:
        """Add validated transaction to the blockchain"""
        self.log_transaction(
            receiver="Blockchain",
            data={
                'type': 'validation',
                'status': 'approved',
                'tx_hash': hash_data(transaction)
            }
        )

    def _reject_transaction(self, transaction: Dict, report: Dict) -> None:
        """Handle invalid transactions"""
        self.log_transaction(
            receiver="Network",
            data={
                'type': 'validation',
                'status': 'rejected',
                'tx_hash': hash_data(transaction),
                'errors': report['errors']
            }
        )
    def validate_transaction(self, transaction: Dict) -> Dict:
        report = super().validate_transaction(transaction)
        
        # Check reputation score
        sender_rep = self.blockchain.get_agent_reputation(
            transaction['sender_public_key']
        )
        
        if sender_rep['score'] < 50:  # Threshold
            report['warnings'].append("Low reputation agent - additional verification required")
            report['valid'] = False
            
        elif sender_rep['score'] < 70:
            report['warnings'].append("Medium reputation agent - limited privileges")
            
        return report