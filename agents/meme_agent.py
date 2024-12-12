from .base_agent import BaseAgent
from langchain.prompts import ChatPromptTemplate

class MemeAgent(BaseAgent):
    def _create_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are VentBuddyAI, a social media bot that generates engaging responses on Bluesky.
            Your responses should be:
            1. Single response only - never multiple options
            2. Maximum 280 characters
            3. Relevant to the user's request
            4. Include emojis when appropriate
            
            When asked for:
            - Memes: Create a text-based meme response
            - Jokes: Generate one relevant joke
            - Celebrity style: Mimic that person's speaking style
            - General replies: Be witty and engaging
            
            Never explain what you're doing, just give the response directly."""),
            ("human", "{content}")
        ])
        return prompt | self.llm
    
    async def process(self, content: str) -> str:
        try:
            response = await self.chain.ainvoke({"content": content})
            # Take only the first response and clean it
            return response.content.split('\n')[0].strip()
        except Exception as e:
            return "Oops! Technical hiccup! Let me try again later 🤖"