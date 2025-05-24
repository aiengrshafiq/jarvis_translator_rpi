# File: jarvis_translator.py

import os
import struct
import time
import uuid
import requests
import pvporcupine
import pyaudio
import speech_recognition as sr
import subprocess
from gtts import gTTS

from app.core.config import get_settings
from app.core.logger import get_logger
from langdetect import detect


settings = get_settings()
logger = get_logger(__name__)

AZURE_TRANSLATOR_KEY = settings.AZURE_TRANSLATOR_KEY
AZURE_REGION = settings.AZURE_REGION
TRANSLATE_ENDPOINT = "https://api.cognitive.microsofttranslator.com"

translation_mode = False


def speak_elevenlabs(text, lang):
    try:
        if not (settings.TTS_PROVIDER == "elevenlabs" and settings.ELEVENLABS_API_KEY):
            logger.info("[TTS] ElevenLabs not configured properly. Using gTTS.")
            speak_gtts(text, lang)
            return

        voice_map = {
            "en": settings.ELEVENLABS_VOICE_ID_EN,
            "ar": settings.ELEVENLABS_VOICE_ID_AR
        }

        voice_id = voice_map.get(lang[:2], settings.ELEVENLABS_VOICE_ID_EN)

        logger.info(f"[ElevenLabs] Speaking ({lang}): {text}")

        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": settings.ELEVENLABS_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
        )
        response.raise_for_status()
        filename = f"/tmp/speak_{uuid.uuid4()}.mp3"
        with open(filename, 'wb') as f:
            f.write(response.content)
        subprocess.run(["paplay", "--device=" + settings.SPEAKER_DEVICE, filename], check=True)
        os.remove(filename)

    except Exception as e:
        logger.warning("[TTS] ElevenLabs failed, falling back to gTTS")
        speak_gtts(text, lang)



            


def speak_gtts(text, lang):
    try:
        logger.info(f"[gTTS] Speaking: {text}")
        filename = f"/tmp/speak_{uuid.uuid4()}.mp3"
        tts = gTTS(text=text, lang=lang)
        tts.save(filename)

        subprocess.run(["paplay", "--device=" + settings.SPEAKER_DEVICE, filename], check=True)
        os.remove(filename)
        time.sleep(0.5)
    except Exception as e:
        logger.exception("[gTTS] Failed to speak.")
        

def speak(text, lang):
    if not text.strip():
        logger.warning("[TTS] Skipped empty text.")
        return

    logger.info(f"[TTS] Speaking: {text} (Lang: {lang})")

    if settings.TTS_PROVIDER.lower() == "elevenlabs" and settings.ELEVENLABS_API_KEY:
        speak_elevenlabs(text, lang)
    else:
        speak_gtts(text, lang)
    

def translate(text, to_lang):
    path = "/translate?api-version=3.0"
    params = f"&to={to_lang}"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": AZURE_REGION,
        "Content-type": "application/json"
    }
    body = [{"text": text}]
    try:
        response = requests.post(TRANSLATE_ENDPOINT + path + params, headers=headers, json=body)
        response.raise_for_status()
        return response.json()[0]["translations"][0]["text"]
    except Exception as e:
        logger.exception("[Translation Error]")
        return ""

def listen_command():
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone(device_index=settings.MIC_DEVICE_INDEX) as source:
            logger.info("🎤 Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            text = recognizer.recognize_google(audio)
            logger.info(f"✅ Recognized: {text}")
            return text
    except sr.WaitTimeoutError:
        logger.warning("[Timeout] No speech detected.")
    except sr.UnknownValueError:
        logger.warning("[STT] Could not understand.")
    except sr.RequestError as e:
        logger.error(f"[STT Error] {e}")
    except Exception as e:
        logger.exception("[Mic Error]")
    return ""

def translator_loop():
    global translation_mode
    while translation_mode:
        logger.info("[↔] Speak to translate (English or Arabic)...")
        text = listen_command()
        if not text:
            continue
        
        # Stop command check
        if "stop translation" in text.lower():
            logger.info("🛑 Stop command detected. Exiting translation mode.")
            translation_mode = False
            speak("Translation mode stopped.", "en")
            break

        # Continue translation
        lang = detect(text)
        target_lang = "ar" if lang == "en" else "en"
        translated = translate(text, target_lang)
        logger.info(f"{lang.upper()} → {target_lang.upper()}: {translated}")
        speak(translated, target_lang)

        # if all(ord(c) < 128 for c in text):
        #     translated = translate(text, "ar")
        #     logger.info(f"EN → AR: {translated}")
        #     speak(translated, "ar")
        # else:
        #     translated = translate(text, "en")
        #     logger.info(f"AR → EN: {translated}")
        #     speak(translated, "en")

def listen_for_wake_word(callback):
    keyword_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "models", "porcupine", "jarvis_raspberry-pi.ppn")
    )

    porcupine = pvporcupine.create(
        access_key=settings.PORCUPINE_ACCESS_KEY,
        keyword_paths=[keyword_path]
    )
    pa = pyaudio.PyAudio()
    logger.info("🎙️ Wake word detection started...")

    try:
        while True:
            stream = pa.open(
                rate=porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                input_device_index=settings.MIC_DEVICE_INDEX,
                frames_per_buffer=porcupine.frame_length,
            )

            try:
                while True:
                    pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
                    pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
                    result = porcupine.process(pcm)

                    if result >= 0:
                        logger.info("🟢 Wake word detected.")
                        speak("Wake word detected. You can say start translation to begin.", "en")
                        
                        stream.stop_stream()
                        stream.close()
                        callback()
                        time.sleep(0.5)
                        break
            except Exception as e:
                logger.exception("[Wake Word Stream Error]")
                stream.stop_stream()
                stream.close()

    except KeyboardInterrupt:
        logger.info("🔴 Wake word listener interrupted.")
    finally:
        pa.terminate()
        porcupine.delete()

def command_loop():
    global translation_mode
    logger.info("Say 'Jarvis, start translation' or 'Jarvis, stop translation'")
    speak("Say 'Jarvis, start translation' or 'Jarvis, stop translation'", "en")
    while True:
        cmd = listen_command().lower()
        if not cmd:
            continue
        if "start translation" in cmd:
            if not translation_mode:
                logger.info("🟡 Translation mode ON")
                translation_mode = True
                translator_loop()
            else:
                logger.info("Already in translation mode.")
        elif "stop translation" in cmd:
            if translation_mode:
                logger.info("🔵 Translation mode OFF")
                translation_mode = False
            else:
                logger.info("Not in translation mode.")
        else:
            logger.info(f"[Jarvis] Unrecognized command: {cmd}")

if __name__ == "__main__":
    listen_for_wake_word(command_loop)
