import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

load_dotenv()

SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
SERVICE_REGION = os.getenv("AZURE_SERVICE_REGION")

print("Loaded Speech Key:", SPEECH_KEY)
print("Loaded Region:", SERVICE_REGION)

config = speechsdk.translation.SpeechTranslationConfig(
    subscription=SPEECH_KEY,
    region=SERVICE_REGION
)
config.speech_recognition_language = "en-US"
config.add_target_language("ar")

# Use system default microphone instead of ALSA-specific device
audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

recognizer = speechsdk.translation.TranslationRecognizer(config, audio_config)

print("Speak something...")

result = recognizer.recognize_once_async().get()

if result.reason == speechsdk.ResultReason.TranslatedSpeech:
    print("Original:", result.text)
    print("Translation:", result.translations["ar"])
else:
    print("Error:", result.reason)
