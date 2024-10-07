#!/usr/bin/env python3

from pydub import AudioSegment
import numpy as np
from scipy.io.wavfile import write
from psychopy import sound, core
import os

# Function to generate a tone at a given frequency and duration
def generate_tone(frequency, duration, sample_rate=44100, amplitude=0.5):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = amplitude * np.sin(2 * np.pi * frequency * t)
    return tone

# Function to encode binary data as an audio signal (using 500Hz for 0 and 1000Hz for 1)
def encode_data_to_audio(data, bit_duration=0.5, sample_rate=44100):
    audio_data = np.array([])
    for bit in data:
        frequency = 500 if bit == '0' else 1000
        tone = generate_tone(frequency, bit_duration, sample_rate)
        audio_data = np.concatenate((audio_data, tone))
    return audio_data

# Save audio data to a WAV file
def save_audio(audio_data, filename, sample_rate=44100):
    write(filename, sample_rate, audio_data.astype(np.float32))

# Function to play audio using PsychoPy
def play_audio(file_path):
    beep = sound.Sound(file_path)
    beep.play()
    core.wait(beep.getDuration())  # Wait for the beep to finish

# Example usage: Encode a binary string into audio and play it
if __name__ == "__main__":
    binary_data = "10101010"  # Example binary data to encode
    bit_duration = 0.5  # Duration of each bit in seconds
    sample_rate = 44100  # Sampling rate for audio

    # Encode data into an audio signal
    audio_data = encode_data_to_audio(binary_data, bit_duration, sample_rate)

    # Save the encoded audio to a file
    output_file = "encoded_audio.wav"
    save_audio(audio_data, output_file, sample_rate)

    # Play the audio using PsychoPy
    if os.path.exists(output_file):
        play_audio(output_file)

    # End the script
    print("Done with encoding and playing the audio stimuli")
    core.quit()
