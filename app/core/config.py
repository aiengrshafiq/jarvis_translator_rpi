# config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    AZURE_TRANSLATOR_KEY: str
    PORCUPINE_ACCESS_KEY: str
    AZURE_REGION: str
    MIC_DEVICE_INDEX: int = 2
    SPEAKER_DEVICE: str = "default"
    TTS_PROVIDER: str = "elevenlabs"  # or "gtts"
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = ""  # Optional: Use a specific voice
    ELEVENLABS_VOICE_ID_EN: str = ""
    ELEVENLABS_VOICE_ID_AR: str = ""
    ELEVENLABS_TTS_MODE: str = os.getenv("ELEVENLABS_TTS_MODE", "stream")  # or "file"
   
    

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "allow"  # forbid is the default; you can change to "allow" if needed

@lru_cache()
def get_settings():
    return Settings()