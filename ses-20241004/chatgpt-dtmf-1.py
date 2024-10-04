#!/usr/bin/env python3

import numpy as np
import soundfile as sf
from dtmf import generate_dtmf_tone, decode_dtmf
import scipy.io.wavfile as wavfile
from psychopy import sound, core
import os

# Generate a DTMF tone for each character in the data string
def encode_data_to_dtmf(data, sample_rate=44100):
    audio_data = np.array([])
    for char in data:
        tone = generate_dtmf_tone(char, duration=0.5, sample_rate=sample_rate)
        audio_data = np.concatenate((audio_data, tone))
    return audio_data

# Save the encoded audio to a file
def save_audio(audio_data, filename, sample_rate=44100):
    sf.write(filename, audio_data, sample_rate)

# Decode the DTMF tones from the audio file
def decode_dtmf_from_audio(file_path):
    sample_rate, audio_data = wavfile.read(file_path)
    decoded_data = decode_dtmf(audio_data, sample_rate)
    return decoded_data

# Play the audio using PsychoPy
def play_audio(file_path):
    beep = sound.Sound(file_path)
    beep.play()
    core.wait(beep.getDuration())  # Wait for the beep to finish

# Example usage: Encode a string into DTMF tones, save, play, and decode
if __name__ == "__main__":
    # Define the data to encode
    data_to_encode = "12345ABC"  # You can use any combination of numbers and characters supported by DTMF
    sample_rate = 44100  # Sampling rate for audio

    # Encode the data into DTMF tones
    encoded_audio = encode_data_to_dtmf(data_to_encode, sample_rate)

    # Save the encoded audio to a WAV file
    output_file = "encoded_dtmf_audio.wav"
    save_audio(encoded_audio, output_file, sample_rate)

    # Play the audio using PsychoPy
    if os.path.exists(output_file):
        print(f"Playing encoded audio: {output_file}")
        play_audio(output_file)

    # Decode the audio back into the original data
    decoded_data = decode_dtmf_from_audio(output_file)
    print(f"Decoded data from audio: {decoded_data}")

    # End the script
    core.quit()
