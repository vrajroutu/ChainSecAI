from langchain.tools import BaseTool
from src.agents.base_agent import ChainSecAgent

class DataProcessingTool(BaseTool):
    name = "Data Processor"
    description = "Processes structured data and returns insights"

    def _run(self, input_data: dict):
        # Example data processing logic
        return {"insights": f"Processed {len(input_data)} items"}

class TaskAgent(ChainSecAgent):
    def __init__(self, blockchain: Blockchain):
        tools = [DataProcessingTool()]
        super().__init__("TaskAgent-v1", tools, blockchain)