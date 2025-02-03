from typing import List, Dict
from langchain.tools import BaseTool
from src.agents.base_agent import ChainSecAgent
from src.blockchain.core import Blockchain
from src.utils.crypto import validate_signature

class BlockchainTools:
    class DataProcessor(BaseTool):
        name = "Data Processor"
        description = "Process structured data and generate insights"
        
        def _run(self, data: Dict) -> Dict:
            return {
                "insights": f"Processed {len(data.get('items', []))} items",
                "stats": {
                    "mean": sum(data.get('values', [])) / len(data.get('values', [1])),
                    "total": sum(data.get('values', []))
                }
            }

    class ContractInteractor(BaseTool):
        name = "Smart Contract Interactor"
        description = "Interact with blockchain smart contracts"
        
        def _run(self, contract_address: str, function_sig: str, args: list) -> Dict:
            return {
                "status": "pending",
                "operation": f"{function_sig}@{contract_address}",
                "arguments": args
            }

    class TransactionValidator(BaseTool):
        name = "Transaction Validator"
        description = "Validate blockchain transactions"
        
        def _run(self, tx_hash: str, blockchain: Blockchain) -> Dict:
            for block in blockchain.chain:
                for tx in block['transactions']:
                    if hash_data(tx) == tx_hash:
                        return {
                            "valid": validate_signature(
                                tx['public_key'],
                                hash_data(tx['data']),
                                tx['signature']
                            ),
                            "block": block['index'],
                            "timestamp": tx['timestamp']
                        }
            return {"valid": False, "error": "Transaction not found"}

class TaskAgent(ChainSecAgent):
    def __init__(
        self,
        blockchain: Blockchain,
        private_key: str,
        llm: BaseLLM,
        custom_tools: List[BaseTool] = None
    ):
        tools = [
            BlockchainTools.DataProcessor(),
            BlockchainTools.ContractInteractor(),
            BlockchainTools.TransactionValidator()
        ] + (custom_tools or [])
        
        super().__init__(
            name="TaskAgent-v1",
            purpose="Perform data processing and blockchain operations",
            tools=tools,
            blockchain=blockchain,
            llm=llm,
            private_key=private_key
        )

    def _create_output_parser(self):
        from langchain.agents.agent import AgentOutputParser
        from langchain.schema import AgentAction, AgentFinish
        
        class TaskOutputParser(AgentOutputParser):
            def parse(self, text: str) -> AgentAction | AgentFinish:
                if "Final Answer:" in text:
                    return AgentFinish(
                        {"output": text.split("Final Answer:")[-1].strip()}, 
                        text
                    )
                return AgentAction("Data Processor", None, text)
        
        return TaskOutputParser()

    def complex_operation(self, data: Dict) -> Dict:
        """Example complex operation combining AI and blockchain"""
        # Step 1: Process data
        processed = self.execute(f"Process this data: {data}")['result']
        
        # Step 2: Store results on blockchain
        store_tx = self.tools[1]._run(
            "0xCONTRACTADDRESS",
            "storeResults(bytes32)",
            [hash_data(processed)]
        )
        
        # Step 3: Validate transaction
        validation = self.tools[2]._run(
            store_tx['operation'],
            self.blockchain
        )
        
        return {
            "processed": processed,
            "storage_tx": store_tx,
            "validation": validation
        }