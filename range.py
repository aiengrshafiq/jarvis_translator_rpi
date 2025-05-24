import pyaudio

p = pyaudio.PyAudio()
device_index = 0  # Replace with your MIC index

info = p.get_device_info_by_index(device_index)
print(f"Device: {info['name']}")
print(f"Default Sample Rate: {info['defaultSampleRate']}")