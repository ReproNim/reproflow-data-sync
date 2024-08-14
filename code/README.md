# ReproNim ReproFlow Data Analysis

## Timing Data Model

### Session
Time calibration session is a set of raw data collected during MRI `dbic^QA` study, generated data dumps, statistics and tmap info. 

Session ID or name is unique string identifier usually containing date in independent format, e.g.: `ses-20240528`, so it was recorded on 28th May 2024.

Directory named as session ID contains all related data. Initially session is created by `collect_data.sh` script, then enriched with QR codes by `reprostim/Parsing/generate_qrinfo.sh` tool and finally processed and analyzed by `generate_timing.sh` scripts.

### Swimlanes
Swimlane is logical model for certain ReproNim system part. It can be described as linear sequence of events or items, where each event has timestamp, unique string ID inside current session and related dump data fragment. Event ID is also unique across all events in current session. 

Note: event can be addressed globally by concatenation of session ID and event ID, e.g. `ses-20240528:birch_000015`. 

Each swimlane has own clock, and events are ordered by this clock internally. 

Known swimlanes listed below, but it's possible to add more swimlanes in future:
- `dicoms` swimlane with DICOMs data where datetime comes from MRI device and extracted from DICOM image as `AcquisitionDate` + `AcquisitionTime` tags.
- `birch` swimlane with birch logs where datetime comes from `iso_time` field.
- `psychopy` swimlane with psychopy logs where datetime comes from `keys_time_str` field.
- `reproevents` swimlane with reproevents logs where datetime comes from `client_time_iso` column.
- `qrinfo` / `reprostim-videos` swimlanes with QR timestamps extracted from video as `isotime_start` field.

### Raw Data

Raw data is set of files collected from different devices and computers during MRI `dbic^QA` study (usually created by `collect_data.sh` script). 

It's stored under session directory as separate subdirectories:
- `DICOMS` directory with DICOMs data produced for study by MRI scanner.
- `birch` directory with JSONL log from birch device.
- `psychopy` directory with multiple psychopy logs in JSONL format.
- `reproevents` directory with reproevents data in CSV format.
- `reprostim-videos` directory with captured videos with QR codes in *.mkv format and corresponding *.log files with reprostim-videocapture metadata.

### Dumps
TBD:


Probably timing data model can be described as parallel swimlanes of data, where each lane is a different filtered data source, and the goal is to synchronize the lanes.  The lanes are:
- `timing-dumps` directory with JSONL logs from DICOMs, psychopy, birch, reprostim-videos, and events:
  - `dump_dicoms.jsonl` JSONL with from the MRI scanner, sequential list of A) `MRI` images, B) `study` and C) `series` list.
  - `dump_psychopy.jsonl` JSONL logs with events pulse events and QR codes original events.
  - `dump_qrinfo.jsonl` JSONL logs from the videos with QR codes.
  - `dump_birch.jsonl` JSONL log from birch device filtered by preliminary time frame.
  - `dump_events.jsonl` JSONL log with list of events/marks used to sync lines. It should be sequential list of events with timestamps and unique IDs. Idea is to proces all swimlanes data and put necessary event UID where it's possible to detect, so we can sync/link all data sources together and then analyze time offsets.

## Algorithm
Algorithm proposals for the ReproFlow time synchronization effort:
- Collect data from different sources: psychopy logs, DICOMs, and videos with QR codes with `collect_data.sh` script. As result it should produce session folder like `ses-20240604` with all necessary data and structure listed below:
  - `birch` folder JSONL log from birch device.
  - `DICOMS` folder with DICOMs data produced for study by MRI scaner, *.dcm images.
  - `psychopy` folder with psychopy logs in JSONL format.
  - `reproevents` folder with reproevents data in *.csv format.
  - `reprostim-videos` folder with captured videos in *.mkv format and corresponding *.mkv.log files with reprostim metadata.
- Parse DICOMs with `code/dump_dicoms.py` tool. It produces JSONL file with timing data, image data, sessions data and study data.
  - `./dump_dicoms.py --log-level DEBUG /data/repronim/reproflow-data-sync/ses-20240604 >dump_dicoms.jsonl 2> dump_dicoms.log` 
- Parse videos with QR codes from session `reprostim-videos` folder with `reprostim/Parse/parse_wQR.py` tool and place results under `timing-reprostim-video` location. At this moment it's unclear how to merge or split this data. So as initial step we consider single video file containing all QR codes. The tool takes long time to proceed video, so we cached result manually in `timing-reprostim-videos` folder for prorotype/development purposes.
  - `./parse_wQR.py --log-level DEBUG /data/repronim/reproflow-data-sync/ses-20240604/reprostim-videos/2024.06.04.13.51.36.620_2024.06.04.13.58.20.763.mkv > 2024.06.04.13.51.36.620_2024.06.04.13.58.20.763.qrinfo.jsonl 2> 2024.06.04.13.51.36.620_2024.06.04.13.58.20.763.qrinfo.log`
  - Note: consider parsing only videos that intersect with MRI study time range -+ 60 minutes.
  - Analyze QR code duration comparing to video script delay set to 0.5 sec at this moment.
  - Analyze time gap/difference between QR code isotime_start and data.keys_time_str.
- Prepare merged JSONL data for psychopy logs. It should be filtered by QR codes and DICOMs information.
  - Proposal for filtering are:
    - Extract JSON records from DICOMs log with type=study, name=dbic^QA, and extract general time range in MRI scanner format. In future we need to concentrate on series started with `func-` prefix, because it produced necessary event/pulse/message in system. Study time range can be set as 60 minutes before study.isotime_start and 60 minutes after study.isotime_end.
    - Extract names of psychopy logs from QR codes log available via QrRecord.data.logfn e.g. 20240604_run-3.log, and use only this filed to parse.
    - From this log subset filter only records with iso_time field in range of MRI study with overlap we calculated above.
    - Filter record with "alink_byte": 496, "alink_flags": 3.
    - TBD:
  - TBD: 
- Use DICOMs as primary data. We should concentrate first on series with `func-` prefix producing multiple image and pulse events in system. And try to locate similar events/sequenec in other data sources like birch, reproevent, psychopy, and videos. 

## Notes and Observations
- `DICOMs`
  - `AcquisitionDate`/`AcquisitionTime` is not reliable and precise. Time offset from NTP time is around 300-400 sec, and time fluctuation in func series scan can jump in 0.3-0.9 sec. This is problem and huge time gap for synchronization with scans each 2 sec.
  - DICOM image metadata contains `Series` tag, and it's possible that the same series are used in different subfolders, e.g. `ses-20240528/005-func-bold_task-rest_run-1`, `ses-20240528/006-func-bold_task-rest_run-1`. Time distance between both series in this case is not 2.0 sec.
- `birch` 
  - `iso_time` is less precise than `time` field from `pigpio.get_current_tick()` API. `time` fluctuated in range 0.0000-0.0003 sec, and `iso_time` fluctuated in range 0.00-0.05 sec.
  - in future look at possibility to use `time` field to produce more strict clock comparing to `iso_time`. This clock was selected as reference one for all other clocks and theoretically this can increase accuracy in 100+ times in this area.
  - `birch` events matched with DICOMs well, but anyway this is not always 100% match.
  - raw data JSONL is not safe to use, because it contains comments and some dirty lines, so custom preprocessing is used to fix this.
- `reproevents` 
  - `isotime` field is precise and reliable, and looks like more precise than birch `iso_time`, fluctuation in range 0.00-0.01 sec.
  - `reproevents` events also matched with DICOMs well close to `birch`, but this is not always 100% match.
- `psychopy` 
  - `isotime` field is less precise, fluctuation in range 0.00-0.03 sec.
- `qrinfo` / `reprostim_video`
  - `isotime_start` field fluctuation in range 0.00-0.06 sec, and correlates with 60.0 FPS video capture, where each frame takes 0.017 sec.   
  - first QR code in each series has strange datetime offset around +0.320 sec (or 20 frames later on 60.0 FPS video) from other QR codes. Most likely it's related to Python script code presenting QR in experiments.
  - QR codes processing is not fast, looks like `reprostim/Parsing/generate_qrinfo.sh` script execution time is around x1-x4 slower comparing to related video, e.g. for 5 minutes video like 1920x1080, 60 FPS it can take up to 20 minutes to process. So in future it would be good idea to optimize `parse_wQR.py` script for better performance on demand.

- `ses-20240528`
  - problem to match other swimlanes with DICOMs at this moment, WiP. 
- `ses-20240604`
  - produces most matches at this moment, but still some issues with psychopy, reprostim_video etc. 
- `ses-20240809`
  - under investigation, produces performance issues which partially are fixed, and swimlane matching issues. 

## TODO:
  - Use DataLad run to execute commands (https://handbook.datalad.org/en/latest/basics/basics-run.html)