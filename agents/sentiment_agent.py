from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from .base_agent import BaseAgent

class SentimentAgent(BaseAgent):
    def _create_chain(self) -> LLMChain:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a sentiment analysis expert. Your job is to:
            1. Analyze the emotional tone
            2. Identify key sentiments
            3. Provide a breakdown of emotions detected
            4. Give an overall sentiment score
            Be nuanced in your analysis and consider context."""),
            ("user", "Analyze the sentiment of: {content}")
        ])
        return LLMChain(llm=self.llm, prompt=prompt)
    
    async def process(self, content: str) -> str:
        try:
            response = await self.chain.arun(content=content)
            return f"🎭 Sentiment Analysis:\n\n{response}"
        except Exception as e:
            return f"Sorry, I couldn't analyze the sentiment right now! Error: {str(e)}"