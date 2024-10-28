- could not find existing psychopy venv/conda env which works. Creating new...

now it is psychopy-2024.2.1 in ~/miniconda3

- meanwhile tried sound

  - could not make it work through HDMI/audio jack on HDMI -> VGA+audio
  - switched to play through built-in socket on laptop. Recorded sample

    2024.10.04-09.04.39.304--2024.10.04-09.05.24.132.mkv -- and probably much longer prior one -- has sound!

  so we should be ok with sound

  - tested some recordings done by others later in the day (not in this repo) -- sounds recorded well!

  - `VM`: did tests with sounds locally with `sudo usbcaptureutility` and `reprostim-videocapture` one:
   - audio device `line-in` somehow doesn't work for me (maybe there something with my pre-owned device, although it blinks with blue light near line-in port when signal provided, but not recorded nor reported by `usbcaptureutility`). 
   - connected HDMI from media player device to capture one, and recorded video with the latest `reprostim-videocapture` and default `a_dev: "auto"` audio device configuration (`2024.10.08-17.51.51.468--2024.10.08-17.52.09.342.mkv`). Can confirm - video .mkv file has audio stream inside.

- chatted with chatgpt 

  - chatgpt-psychopy-1.py -- basic to get things going
  - chatgpt-pydub-1.py -- some with pydub
  - chatgpt-dtmf-1.py is kinda close to what needed
 
- committed changes which should have produced some sound but none came out TODO

- copied the data
  - apparently no birch!  I guess was rebooted and not remounted :-/

Results/problems found in timing-dumps:
  - `dicoms` - 5 func scans for 15 images each. Somehow predicted ISO time differs from expected one. e.g predicted time is `09:30:35` but real one is `09:31:22`, !!! differs in 47 seconds and this should be `TODO:` investigated (??? problem of algorithm or it was corrected manually on MRI side). In case this is result of MRI clock correction, we should force offset for `dicoms` swimlane manually and re-run dumps.    
  - `birch` - no records at all, ATM this is critical as birch considered as master clock and core to synchronize all other devices. But maybe we need to `TODO:` investigate and discuss possible workarounds in this case.
  - `psychopy` - OK, matched well with 5's series.
  - `reproevents` - OK, matched well with 5's series.
  - `qrinfo` - Failed:
    - Found QR codes in video only for last series `009-func-bold_task-rest_acq-short1_run-05`.
    - Matched incorrectly between in `dump_tmap_ex.csv`. Actually codes `qrinfo-000001`-`qrinfo-000015` corresponds to only the latest 5-th series, but it somehow matched 2 times for series `008-func-bold_task-rest_acq-short1_run-04` and `009-func-bold_task-rest_acq-short1_run-05`. So `TODO:` algorithm should be revised to improve quality. Yes this is most likely related to no-`birch` info or invalid `dicoms` ISO time, but anyway, code should more robust and accurate. 
