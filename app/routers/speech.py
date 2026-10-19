import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from openai import OpenAI
from pydantic import BaseModel, Field

from config import Config

router = APIRouter(prefix="/speech", tags=["Jarvis Voice"])
logger = logging.getLogger(__name__)


class SpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


@router.post("/")
async def generate_speech(request: SpeechRequest):
    if not Config.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="La voz neuronal no esta configurada.")
    try:
        client = OpenAI(api_key=Config.OPENAI_API_KEY)
        audio = client.audio.speech.create(
            model="tts-1-hd",
            voice="onyx",
            input=request.text,
            response_format="mp3",
            speed=0.98,
        )
        return Response(content=audio.content, media_type="audio/mpeg")
    except Exception as error:
        logger.error("No se pudo generar la voz de JARVIS: %s", error)
        raise HTTPException(status_code=502, detail="No se pudo generar la voz neuronal.") from error
