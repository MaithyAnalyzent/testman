from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import Optional
import logging
from config import get_settings

settings = get_settings()

class IntentClassification(BaseModel):
    intent: str = Field(description="The classified intent of the user's query")
    confidence: float = Field(description="Confidence score of the classification")
    extracted_topic: Optional[str] = Field(description="Main topic or subject extracted from the query")

class IntentClassifier:
    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name="llama-3.2-3b-preview"
        )
        self.parser = PydanticOutputParser(pydantic_object=IntentClassification)
