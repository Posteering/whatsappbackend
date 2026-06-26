from openai import AsyncOpenAI
from app.core.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def transcribe_audio(audio_file_path: str) -> str:
    """
    Transcribe a WhatsApp voice note using OpenAI Whisper.
    """
    with open(audio_file_path, "rb") as audio_file:
        transcript = await client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )
    return transcript.text

async def generate_speech(text: str, output_path: str):
    """
    Generate speech from text using OpenAI TTS.
    """
    response = await client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text
    )
    response.stream_to_file(output_path)
