from .base_agent import BaseAgent
from langchain.prompts import ChatPromptTemplate

class ThreadAgent(BaseAgent):
    def _create_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a social media conversation expert that creates engaging thread responses.
            Keep responses:
            1. Single and direct
            2. Under 280 characters
            3. Conversational and natural
            4. Relevant to the topic
            
            Never explain or provide multiple options."""),
            ("human", "{content}")
        ])
        return prompt | self.llm
    
    async def process(self, content: str) -> str:
        try:
            response = await self.chain.ainvoke({"content": content})
            return response.content.split('\n')[0].strip()
        except Exception as e:
            return "Having a brief malfunction! Back soon! 🔧"