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
   
    

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "allow"  # forbid is the default; you can change to "allow" if needed

@lru_cache()
def get_settings():
    return Settings()