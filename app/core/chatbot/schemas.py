from typing import Literal, Optional
from pydantic import BaseModel, Field

class ChatbotInput(BaseModel):
    message: str

class AIAnalysisResult(BaseModel):
    topic: Literal[
        "Flight Information",
        "General Information",
        "Prompt Injection",
        "RAG Agent",
        "Comparison Agent"
    ] = Field(description="The categorization of the user's message.")
    language: str = Field(description="The language of the message.")
    sentiment: str = Field(description="The sentiment tone (e.g., Angry, Happy, Neutral).")
    answer: str = Field(description="A general answer or placeholder.")

class ChatbotResponse(BaseModel):
    id: int
    user_message: str
    analysis: AIAnalysisResult
    created_at: str