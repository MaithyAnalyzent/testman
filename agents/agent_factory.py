from langchain_groq import ChatGroq
from .meme_agent import MemeAgent
from .thread_agent import ThreadAgent
from .impersonation_agent import ImpersonationAgent
from .genz_therapist import GenZTherapistAgent

class AgentFactory:
    def __init__(self, groq_api_key: str):
        self.llm = ChatGroq(
            api_key=groq_api_key,
            model_name="mixtral-8x7b-32768"
        )
        self.agents = {
            'meme': MemeAgent,
            'thread': ThreadAgent,
            'impersonation': ImpersonationAgent,
            'therapy': GenZTherapistAgent,
            'default': MemeAgent
        }
    
    def get_agent(self, agent_type: str):
        agent_class = self.agents.get(agent_type, self.agents['default'])
        return agent_class(self.llm)