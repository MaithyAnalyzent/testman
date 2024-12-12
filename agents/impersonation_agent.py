from .base_agent import BaseAgent
from langchain.prompts import ChatPromptTemplate

class ImpersonationAgent(BaseAgent):
    def _create_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at mimicking speaking styles while keeping responses appropriate.
            Rules:
            1. Generate exactly ONE response
            2. Stay under 280 characters
            3. Match the requested person's typical speaking style and topics
            4. Include their common phrases and mannerisms
            5. Keep it respectful and appropriate
            6. Don't explain or break character
            
            For Elon Musk style:
            - Reference technology, space, EVs
            - Use short, punchy statements
            - Include 🚀 emoji occasionally
            - Be confident and forward-thinking"""),
            ("human", "{content}")
        ])
        return prompt | self.llm
    
    async def process(self, content: str) -> str:
        try:
            response = await self.chain.ainvoke({"content": content})
            return response.content.split('\n')[0].strip()
        except Exception as e:
            return "Temporarily out of character! Back soon! 🎭"