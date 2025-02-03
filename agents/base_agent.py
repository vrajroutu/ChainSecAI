from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
from langchain.chains import LLMChain
from langchain.llms import BaseLLM
from langchain.prompts import StringPromptTemplate
from src.blockchain.core import Blockchain
from src.utils.crypto import hash_data, sign_data

class AgentPromptTemplate(StringPromptTemplate, ABC):
    template: str = """
    You are {agent_name}, a blockchain-enabled AI agent. 
    Your purpose: {agent_purpose}
    
    Tools available:
    {tools}
    
    Current blockchain state:
    - Block height: {block_height}
    - Pending transactions: {pending_txs}
    
    Strict security rules:
    1. Always validate transactions before signing
    2. Never share private keys
    3. Verify blockchain confirmations for critical operations
    
    Task: {input}
    {agent_scratchpad}"""

    def format(self, **kwargs) -> str:
        kwargs["tools"] = "\n".join(
            [f"{tool.name}: {tool.description}" for tool in kwargs["tools"]]
        )
        kwargs["block_height"] = kwargs["blockchain"].chain[-1]["index"]
        kwargs["pending_txs"] = len(kwargs["blockchain"].pending_transactions)
        return self.template.format(**kwargs)

class ChainSecAgent(ABC):
    def __init__(
        self,
        name: str,
        purpose: str,
        tools: List[Tool],
        blockchain: Blockchain,
        llm: BaseLLM,
        private_key: Optional[str] = None
    ):
        self.name = name
        self.purpose = purpose
        self.tools = tools
        self.blockchain = blockchain
        self.llm = llm
        self.private_key = private_key
        self.agent_executor = self._create_agent_executor()
        self.public_key = self._derive_public_key() if private_key else ""

    def _create_agent_executor(self) -> AgentExecutor:
        prompt = AgentPromptTemplate(
            input_variables=["input", "agent_scratchpad"],
            partial_variables={
                "agent_name": self.name,
                "agent_purpose": self.purpose,
                "blockchain": self.blockchain
            }
        )

        llm_chain = LLMChain(llm=self.llm, prompt=prompt)
        tool_names = [tool.name for tool in self.tools]
        
        agent = LLMSingleActionAgent(
            llm_chain=llm_chain,
            output_parser=self._create_output_parser(),
            stop_sequence=["\nFinal Answer"],
            allowed_tools=tool_names
        )

        return AgentExecutor.from_agent_and_tools(
            agent=agent, 
            tools=self.tools, 
            verbose=True
        )

    def _derive_public_key(self) -> str:
        """Derive public key from private key using RSA"""
        from Crypto.PublicKey import RSA
        key = RSA.import_key(self.private_key)
        return key.publickey().export_key().decode()

    def sign_transaction(self, data: Dict) -> Dict:
        """Create signed transaction payload"""
        if not self.private_key:
            raise ValueError("Agent requires private key for signing")
            
        signature = sign_data(self.private_key, data)
        return {
            **data,
            "sender": self.name,
            "public_key": self.public_key,
            "signature": signature,
            "timestamp": time(),
            "nonce": self._generate_nonce()
        }

    def _generate_nonce(self) -> int:
        """Generate unique transaction nonce"""
        return int(time() * 1000) % 1000000

    def log_transaction(self, receiver: str, data: dict) -> str:
        """Submit transaction to blockchain network"""
        signed_tx = self.sign_transaction({
            "receiver": receiver,
            "data": data,
            "previous_hash": self.blockchain.hash(self.blockchain.last_block)
        })
        
        self.blockchain.add_transaction(**signed_tx)
        return hash_data(signed_tx)

    @abstractmethod
    def _create_output_parser(self):
        """Abstract method for custom output parsing"""
        pass

    def execute(self, task: str) -> dict:
        """Execute task and return parsed result with TX hash"""
        result = self.agent_executor.run(task)
        tx_hash = self.log_transaction("Network", {"task": task, "result": result})
        return {"result": result, "tx_hash": tx_hash}