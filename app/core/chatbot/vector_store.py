import os
from langchain_community.document_loaders import DirectoryLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

from app.core.config import settings


def get_vector_store():
    embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001",
        vertexai=True,
        google_api_key=settings.GOOGLE_API_KEY,
    )

    if os.path.exists(settings.CHROMA_PATH) and os.listdir(settings.CHROMA_PATH):
        return Chroma(persist_directory=settings.CHROMA_PATH, embedding_function=embeddings)

    if not os.path.exists(settings.MARKDOWN_STORAGE_PATH):
        os.makedirs(settings.MARKDOWN_STORAGE_PATH, exist_ok=True)

    loader = DirectoryLoader(
        settings.MARKDOWN_STORAGE_PATH,
        glob="**/*.md",
        loader_cls=UnstructuredMarkdownLoader
    )
    docs = loader.load()

    if not docs:
        return Chroma(persist_directory=settings.CHROMA_PATH, embedding_function=embeddings)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(docs)

    return Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=settings.CHROMA_PATH
    )