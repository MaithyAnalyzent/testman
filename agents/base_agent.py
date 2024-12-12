from abc import ABC, abstractmethod
from langchain_groq import ChatGroq
from langchain.schema.runnable import RunnableSequence

class BaseAgent(ABC):
    def __init__(self, llm: ChatGroq):
        self.llm = llm
        self.chain = self._create_chain()
    
    @abstractmethod
    def _create_chain(self) -> RunnableSequence:
        pass
    
    @abstractmethod
    async def process(self, content: str) -> str:
        pass
