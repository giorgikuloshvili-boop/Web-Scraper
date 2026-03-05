# app/core/chatbot/handlers.py
from abc import ABC, abstractmethod
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.chatbot.vector_store import get_vector_store
from app.core.chatbot.prompts import RAG_SYSTEM_PROMPT

# Shared LLM instance (or you can inject it)
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)


class TopicHandler(ABC):
    """Base strategy interface for handling different topics."""

    @abstractmethod
    def handle(self, query: str, initial_answer: str) -> str:
        """
        :param query: The original user message.
        :param initial_answer: The placeholder answer generated during classification.
        """
        pass


class RagHandler(TopicHandler):
    """Handles questions about the scraped data (Gloworld)."""

    def __init__(self):
        self.vector_store = get_vector_store()
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})

        self.chain = (
                {"context": self.retriever | self._format_docs, "question": RunnablePassthrough()}
                | ChatPromptTemplate.from_messages([("system", RAG_SYSTEM_PROMPT), ("human", "{question}")])
                | llm
                | StrOutputParser()
        )

    def _format_docs(self, docs):
        return "\n\n".join(d.page_content for d in docs)

    def handle(self, query: str, initial_answer: str) -> str:
        return self.chain.invoke(query)


class McpHandler(TopicHandler):
    """
    Handles Comparison or Tool-based requests (Model Context Protocol).
    Future: Connect this to actual Python tools/APIs.
    """

    def handle(self, query: str, initial_answer: str) -> str:
        prompt = f"Perform a detailed comparison/analysis based on this request: {query}"
        return llm.invoke(prompt).content


class PromptInjectionHandler(TopicHandler):
    """Handles security risks."""

    def handle(self, query: str, initial_answer: str) -> str:
        return "I cannot fulfill that request as it violates my safety guidelines."


class DefaultHandler(TopicHandler):
    """Handles General Info, Chit-chat, etc."""

    def handle(self, query: str, initial_answer: str) -> str:
        return initial_answer


class HandlerFactory:
    """Factory to instantiate the correct handler based on the topic."""

    @staticmethod
    def get_handler(topic: str) -> TopicHandler:
        if topic == "RAG Agent":
            return RagHandler()
        elif topic == "MCP Agent: Flight Information":
            return McpHandler()
        elif topic == "Comparison Agent":
            return DefaultHandler()
        elif topic == "Prompt Injection":
            return PromptInjectionHandler()
        return DefaultHandler()