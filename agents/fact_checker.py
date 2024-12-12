from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from .base_agent import BaseAgent

class FactCheckerAgent(BaseAgent):
    def _create_chain(self) -> LLMChain:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a fact-checking expert. Your job is to:
            1. Identify the main claim(s)
            2. Analyze the likelihood of accuracy
            3. Provide a clear, evidence-based response
            4. Rate confidence in your assessment
            Be objective and thorough in your analysis."""),
            ("user", "Fact check this claim: {content}")
        ])
        return LLMChain(llm=self.llm, prompt=prompt)
    
    async def process(self, content: str) -> str:
        try:
            response = await self.chain.arun(content=content)
            return f"📊 Fact Check Analysis:\n\n{response}"
        except Exception as e:
            return f"Sorry, I couldn't fact check this right now! Error: {str(e)}"