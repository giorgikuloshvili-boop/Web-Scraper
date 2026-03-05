from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.chatbot.schemas import ChatbotInput, ChatbotResponse
from app.core.interactor import ChatbotInteractor
from app.infra.dependables import get_db

chat_bot_api = APIRouter()

@chat_bot_api.post("/analyze",
                   response_model=ChatbotResponse,
                   status_code=HTTPStatus.OK)
def analyze_message(input_data: ChatbotInput, db: Session = Depends(get_db)):
    try:
        interactor = ChatbotInteractor(db_session=db)

        response = interactor.run(input_data)
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
