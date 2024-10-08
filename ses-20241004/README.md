- could not find existing psychopy venv/conda env which works. Creating new...

now it is psychopy-2024.2.1 in ~/miniconda3

- meanwhile tried sound

  - could not make it work through HDMI/audio jack on HDMI -> VGA+audio
  - switched to play through built-in socket on laptop. Recorded sample

    2024.10.04-09.04.39.304--2024.10.04-09.05.24.132.mkv -- and probably much longer prior one -- has sound!

  so we should be ok with sound

  - `VM`: did tests with sounds locally with `sudo usbcaptureutility` and `reprostim-videocapture` one:
    - audio device `line-in` somehow doesn't work for me (maybe there something with my pre-owned device, although it blinks with blue light near line-in port when signal provided, but not recorded nor reported by `usbcaptureutility`). 
    - connected HDMI from media player device to capture one, and recorded video with the latest `reprostim-videocapture` and default `a_dev: "auto"` audio device configuration (`2024.10.08-17.51.51.468--2024.10.08-17.52.09.342.mkv`). Can confirm - video .mkv file has audio stream inside.

- chatted with chatgpt 

  - chatgpt-psychopy-1.py -- basic to get things going
  - chatgpt-pydub-1.py -- some with pydub
  - chatgpt-dtmf-1.py is kinda close to what needed
 
- committed changes which should have produced some sound but none came out TODO

- TODO: copy data!
