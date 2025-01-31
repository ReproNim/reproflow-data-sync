* It was messy
* Running psychopy in conda env where I first pip upgraded psychopy
  and then directly installed from github dev for today

  ❯ psychopy --version
PsychoPy3, version 2025.1.0 (c)Jonathan Peirce 2018, GNU GPL license

2024.2.5-587-gd4be108e2

* audio backends didn't work until I switched sounddevice


* a number of false starts, then one false start with MRI collected
  but no trigger pulse connected
  -- _run-03 -- I reconnected for a separate video, but it reset
  routing of audio to go to speaker instead of hdmi... and then I
  think one trigger pulse was into terminal instead of app

* _run-04 -- reconnected HDMI

 seems worked --

 NOTE: audio recording did go through HDMI but only by magic.

 we need to make it explicit

 and start "occupying" audio device before receiving trigger so it
 could be rerouted manually before trigger arrives

 otherwise it is not even in pavucontrol

* run-05 -- did not reconnect HDMI

############################################
## VM Notes 

### Environment & Execution
- Used reprostim 0.7.5 for the first time to parse qr @typhon:
  - created `screen` session
  - checked out `reprostim` from `github` branch to `/home/vmelnik/projects/reprostim` location.
  - created `venv` env and installed reprostim there from pypi:
    ```shell
    cd /home/vmelnik/projects/reprostim
      
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip 
    
    pip install reprostim
    ``` 
  - checked out local `reproflow-data-sync repo` and expanded git annex files:
    ```shell
    cd /home/vmelnik/projects/typhon
    git config --global --add safe.directory /data/repronim/reproflow-data-sync/.git
    git clone /data/repronim/reproflow-data-sync reproflow-data-sync
    cd reproflow-data-sync
    git annex get .
    ```
  - generated `qrinfo` in `screen` session as this is long process under venv 
    with installed reprostim. The `tools` folder is not included in pypi
    package, so it should be checked out from `github`:
      ```shell
      cd /home/vmelnik/projects/reprostim/tools
      ./reprostim-generate-qrinfo /home/vmelnik/projects/typhon/reproflow-data-sync/ses-20250127
      ```
    NOTE: produced JSONL file contains only QR codes and no audio ones ATM.
  - created custom `timing-dumps-config.yaml` in the `ses-20250127` folder, 
    where specified `reproevents` are missed in this series:
    ```yaml
    skip_swimlanes:
      # we don't have reproevents in ses-20250127
      - reproevents
    ```
  - generated dump/marks/tmap with script like below:
    ```shell
    #!/bin/bash

    DATA_DIR=/home/vmelnik/projects/typhon/reproflow-data-sync

    ./generate_timing_dumps.sh $DATA_DIR/ses-20250127
    ```
    or
    ```shell
    #!/bin/bash

    DATA_DIR=/home/vmelnik/projects/typhon/reproflow-data-sync
    GIT_DIR=/home/vmelnik/projects/reproflow-data-sync

    ./generate_timing_dumps.sh $DATA_DIR/ses-20250127
    cp -rv $DATA_DIR/ses-20250127/timing-dumps $GIT_DIR/ses-20250127
    ```
    it generates `ses-20250127/timing-dumps` folder, and it was committed to git.
  
### Results & Observations

- 0 `reproevents` series as no data provided. There is also error in 
  `dump_reproevents.log`, which is fixed now.
- Based on DICOMs we have 6 func scans - first is only 2 frames, and the rest 5
  contains 20 images each and interval is 1.83s (rather than 15/2.0 we had before).
- First series with 2 frames is not handled and considered to be series (maybe it's ok).
- `birch` found all 5 long series for 20 images and interval 1.83s correctly.
- `qrinfo` and `psychopy` somehow found 6 series, for unknown reasons they 
  split the 3rd series into 2 series with 8 and 11 images each or 19 
  totally instead of 20 ones. It should be investigated what is the cause and what
  happened with 9-th image in 3rd scan (008-func-bold_task-rest_acq-short1_run-03).
- After looking at `psychopy` logs and recorded video found:
  - Scan drop recorded in `psychopy` `output_2025.01.27-11.36.43.465--2025.01.27-11.37.36.144.log`:
    ```jsonl
    {"event": "trigger", "acqNum": 8, "logfn": "output_2025.01.27-11.36.43.465--.log", "time": 1737995831.072309, "time_formatted": "2025-01-27T11:37:11.072309-05:00", "mode": "event", "a_time": 1737995834.1524897, "a_time_str": "2025-01-27T11:37:14.152490-05:00", "a_data": 8, "a_codec": "FSK", "a_f0": 1000, "a_f1": 5000, "a_pre_delay": 0.1, "a_post_delay": 0.1, "a_duration": 0.648, "keys": ["5"], "keys_time": 1737995834.152525, "keys_time_str": "2025-01-27T11:37:14.152525-05:00", "time_flip": 1737995834.2256658, "time_flip_formatted": "2025-01-27T11:37:14.225666-05:00", "prior_time_off": 1737995834.7325563, "prior_time_off_str": "2025-01-27T11:37:14.732556-05:00"}
    {"event": "trigger", "acqNum": 9, "logfn": "output_2025.01.27-11.36.43.465--.log", "time": 1737995834.7326736, "time_formatted": "2025-01-27T11:37:14.732674-05:00", "mode": "event", "a_time": 1737995835.984098, "a_time_str": "2025-01-27T11:37:15.984098-05:00", "a_data": 9, "a_codec": "FSK", "a_f0": 1000, "a_f1": 5000, "a_pre_delay": 0.1, "a_post_delay": 0.1, "a_duration": 0.648, "keys": ["5"], "keys_time": 1737995835.9841313, "keys_time_str": "2025-01-27T11:37:15.984131-05:00", "time_flip": 1737995836.0421019, "time_flip_formatted": "2025-01-27T11:37:16.042102-05:00", "prior_time_off": 1737995836.5496328, "prior_time_off_str": "2025-01-27T11:37:16.549633-05:00"}
    ```
  - We can see that `acqNum` is sequential 8 -> 9, but time delta is 3.66s rather than 1.83s. 
  - This means that either no signal was received for 9-th image by pscychopy/timesync_stimuli or it was missed by script somehow inside. 
- Missed scan time interval is between 11:37:10 and 11:37:14.
- `dump_qrinfo.jsonl` contains only video QR codes and no audio ones.
- `dump_tmap.jsonl` contains only 4 series, the broken one explained above is not 
   included, so this is good.
- TBD: investigate `dump_tmap_ex.csv` series mapping data to check current 
  match algorithm accuracy.
- TODO: add session `tmap` data to global `repronim_tmap.jsonl` table.
- TODO: work on `qr-parse` reprostim sub-command code to parse audio codes as 
  well from recorded videos.