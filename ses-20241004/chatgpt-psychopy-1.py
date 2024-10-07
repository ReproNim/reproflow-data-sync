#!/usr/bin/env python3

from psychopy import sound, core

# Function to play a beep at a specific frequency and duration
def play_beep(frequency, duration, volume=1.0):
    # Create a sound object with the specified frequency
    beep = sound.Sound(frequency, secs=duration, volume=volume)
    beep.play()
    core.wait(duration)  # Wait for the beep to finish

# Example usage
if __name__ == "__main__":
    # Define parameters
    frequencies = [500, 1000, 2000]  # Frequencies in Hz (e.g., 500 Hz, 1000 Hz, 2000 Hz)
    duration = 0.5  # Duration of each beep in seconds
    volume = 0.8  # Volume level (0.0 to 1.0)

    # Play beeps for each frequency
    for freq in frequencies:
        print(f"Playing beep at {freq} Hz")
        play_beep(freq, duration, volume)

    # End the script
    print("Done with the auditory stimuli")
    core.quit()
