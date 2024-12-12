# genz_therapist.py
from .base_agent import BaseAgent
from langchain.prompts import ChatPromptTemplate

class GenZTherapistAgent(BaseAgent):
    def _create_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Gen Z therapist who uses modern slang, emojis, and relatable 
            references while providing genuine emotional support. Keep responses authentic, supportive, 
            and under 280 characters. Balance humor with empathy."""),
            ("human", "{content} CONTEXT: {user_context}")
        ])
        return prompt | self.llm
    
    async def process(self, content: str, user_context: str = "") -> str:
        try:
            response = await self.chain.ainvoke({
                "content": content,
                "user_context": user_context
            })
            return response.content.strip()
        except Exception as e:
            return "no cap fr fr, having some tech issues rn 😭 give me a sec bestie!"