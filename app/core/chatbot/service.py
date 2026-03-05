from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.chatbot.schemas import AIAnalysisResult
from app.core.chatbot.prompts import get_classifier_prompt
from app.core.chatbot.handlers import HandlerFactory
from app.core.config import settings


class ChatbotService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0,
            google_api_key = settings.GOOGLE_API_KEY,
            vertexai=True,
        )

    def _analyze_message(self, text: str) -> AIAnalysisResult:
        """
        Internal method to classify the message (Topic, Language, Sentiment).
        """
        structured_llm = self.llm.with_structured_output(AIAnalysisResult)
        classifier_chain = get_classifier_prompt() | structured_llm
        return classifier_chain.invoke({"text": text})

    def process_message(self, user_text: str) -> AIAnalysisResult:
        """
        Main entry point for AI logic.
        1. Classifies the message.
        2. Calls the Factory to get the right Agent.
        3. Executes the Agent to get the final answer.
        """
        analysis_result = self._analyze_message(user_text)

        handler = HandlerFactory.get_handler(analysis_result.topic)

        final_answer = handler.handle(
            query=user_text,
            initial_answer=analysis_result.answer
        )

        analysis_result.answer = final_answer

        return analysis_result