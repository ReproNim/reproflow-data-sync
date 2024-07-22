# ReproNim ReproFlow Data Analysis

## Timing Data Model

Probably timing data model can be described as parallel swimlanes of data, where each lane is a different filtered data source, and the goal is to synchronize the lanes.  The lanes are:
- `timing-DICOMs` JSONL with from the MRI scanner, sequential list of A) `MRI` images, B) `study` and C) `series` list.
- `timing-psychopy` JSONL logs with events pulse events and QR codes original events.
- `timing-reprostim-videos` JSONL logs from the videos with QR codes.
- `timing-birch` JSONL log from birch device filtered by preliminary time frame.
- `timing-events` JSONL log with list of events/marks used to sync lines. It should be sequential list of events with timestamps and unique IDs. Idea is to proces all swimlanes data and put necessary event UID where it's possible to detect, so we can sync/link all data sources together and then analyze time offsets.

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
