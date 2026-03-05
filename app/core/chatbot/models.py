from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.infra.dependables import Base


class MessageModel(Base):
    __tablename__ = "chatbot_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    topic = Column(String, nullable=True)
    language = Column(String, nullable=True)
    sentiment = Column(String, nullable=True)

    bot_answer = Column(Text, nullable=True)