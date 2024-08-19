# ReproNim ReproFlow Data Analysis

## Timing Data Model

### Session
Time calibration session is a set of raw data collected during MRI `dbic^QA` study, generated data dumps, statistics and tmap info. 

Session ID or name is unique string identifier usually containing date in independent format, e.g.: `ses-20240528`, so recording date is May 28, 2024.

Directory named as session ID contains all related data. Initially session is created by `collect_data.sh` script, then enriched with QR codes by `reprostim/Parsing/generate_qrinfo.sh` tool and finally processed and analyzed by `generate_timing.sh` scripts.

### Swimlanes
Swimlane is logical model for certain ReproNim system part. It can be described as linear sequence of events or items, where each event has timestamp, unique string ID inside current session and related dump data fragment. Event ID is also unique across all events in current session. 

Note: event can be addressed globally by concatenation of session ID and event ID, e.g. `ses-20240528:birch_000015`. 

Each swimlane has own clock, and all related events are ordered by this clock internally. 

Known swimlanes listed below, but it's possible this list will be extended in the future:
- `dicoms` swimlane with DICOMs data where datetime comes from MRI device and extracted from DICOM image as `AcquisitionDate` + `AcquisitionTime` tags.
- `birch` swimlane with birch logs where datetime comes from `iso_time` field.
- `psychopy` swimlane with psychopy logs where datetime comes from `keys_time_str` field.
- `reproevents` swimlane with reproevents logs where datetime comes from `client_time_iso` column.
- `qrinfo` / `reprostim-videos` swimlanes with QR timestamps extracted from video as `isotime_start` field.

### Clocks
Each ReproNim system part and related swimlane has own clock. 

All clocks values serialized into string as `isotime` format. It's variation of ISO 8601 format with microseconds and no-timezone. Timezone info removed to simplify readability and maintenance, but this format implictly treat is as `America/New_York` region (-04:00)  e.g. sample value is `2024-08-09T10:27:24.341075`, but it corresponds to `2024-08-09T10:27:24.341075-04:00` in real world. 

In addition to swimlanes internal timing, there is also global clock - `isotime`. It respresents absolute global time in ISO format, and it's used to synchronize all swimlanes together. 

Global clock timing information is currently sticked to `birch` clock, which mean both are the same. This was done as initial step to start development. But in nature it should not be bound any clocks, and can be set as independent clock, e.g. calculated from different swimlanes or taken somehow from NTP server, etc.

Known clocks listed below, but it's possible this list will be extended in the future:
- `isotime` global clock with absolute time in custom `isotime` format.
- `dicoms` clock of MRI device.
- `birch` clock of birch device.
- `psychopy` clock of psychopy.
- `reproevents` clock of reproevents.
- `qrinfo` / `reprostim_videos` clock for QR codes and `reprostim-videocapture` utility.

We have tmap service (`repronim_timing.TMapService`) to map datetime from one clock to another. This mapping based on tmap JSONL information we calculated for each time calibration session (`dump_tmap.jsonl`) and merged into the global single file (`repronim_tmap.jsonl`).

### Raw Data

Raw data is set of files collected from different devices and computers during MRI `dbic^QA` study (usually created by `collect_data.sh` script). 

It's stored under session directory as separate subdirectories:
- `DICOMS` directory with DICOMs data produced for study by MRI scanner.
- `birch` directory with JSONL log from birch device.
- `psychopy` directory with multiple psychopy logs in JSONL format.
- `reproevents` directory with reproevents data in CSV format.
- `reprostim-videos` directory with captured videos with QR codes in *.mkv format and corresponding *.log files with reprostim-videocapture metadata.

### QR Codes
Video recorded by `reprostim-videocapture` utility may contain QR codes with timestamps. This data is extracted by `reprostim/Parsing/generate_qrinfo.sh` script and stored as JSONL logs under `timing-reprostim-videos` subfolder in related session directory, e.g. `ses-202040604/2024.06.04.13.51.24.278_2024.06.04.13.51.31.057.qrinfo.jsonl` and `ses-202040604/2024.06.04.13.51.24.278_2024.06.04.13.51.31.057.qrinfo.log`. Where *.jsonl is parsed QR codes data and *.log is text file with detailed processing/execution info.

`generate_qrinfo.sh` script takes session root folder as parameter. It scans all video files (*.mkv,*.mov) and logs (*.log) in `reprostim-videos` sub-folder and produces JSONL logs with QR codes data under `timing-reprostim-videos` sub-folder.

QR codes generation process is not fast with current implementation, and can take up to 4 times longer than original video duration. But this information should be definitely created before any further processing and dumps calculations.

### Dumps
Dumps can be described as set of JSONL files with 0 or more objects inside. It's stored as JSONL files under `timing-dumps` subfolder in related session directory, e.g. `ses-202040604/timing-dumps/dump_dicoms.jsonl` and `ses-202040604/timing-dumps/dump_dicoms.log`. Where *.jsonl is dump data and *.log is text file with detailed processing/execution info. There are following dump types:
- Swimlane dumps with filtered and enriched data from raw data sources. Contain swimlane events ordered by time and also additional metadata and information. Raw data contains more logs and events, but dumps should contain only necessary data for further processing and analysis. Also, it's possible manually locate source raw data from certain JSON object in dump. Not all raw data exists in JSONL format, so in this case it's converted to JSONL, e.g. `reproevents` CSV file row converted to JSONL as `data` field.
- Marks dumps with synchronization information across swimlanes. Contain list of global events with timestamps and unique IDs used to synchronize swimlanes together.
- tmap dumps with mapping information between different clocks. 

Common dump JSON item fields are:
- `session_id` - specifies unique session ID.
- `id` - specifies unique dump item ID inside related session.
- `type` - specifies record class type, to distinguish different items if any inside single dump.
- `isotime` - specifies datetime in `isotime` format in related swimlane clocks.

Let's briefly describe each dump:
- `dump_dicoms.jsonl` JSONL with items generated from DICOMS images:
  - `DicomsRecord` items corresponding to DICOMs image. Datetime information extracted from DICOM tags (`AcquisitionDate` + `AcquisitionTime`). 
  - `StudyRecord` specifies target study and study name is extracted from DICOM tags. 
  - `SeriesRecord` specifies target series inside the study. 
- `dump_birch.jsonl` JSONL with items corresponding to birch logs. Datetime information extracted from `iso_time` field which is not very precise by now. It's filtered by 8-th bit of `alink_byte` field and contains additional calculated fields:
  - `duration` - duration in seconds till the next time 8-th bit will be set on again, calculated from strict clock based on `time` field.
  - `duration_isotime` - the same as `duration` but calculated based on `iso_time` field.
  - `flag_duration` - duration in seconds till the next event 8-th bit will be set off, calculated from precise `time` field.
  - `flag_duration_isotime` - the same as `flag_duration` but calculated based on `iso_time` field.
- `dump_psychopy.jsonl` Aggregated JSONL with items corresponding to psychopy logs. Target log file names extracted from QR codes and then filtered by MRI study datetime range. Datetime information extracted from `keys_time_str` field.
- `dump_qrinfo.jsonl` JSONL with `QrRecord` items corresponding to QR codes logs. Datetime information extracted from `isotime_start` field (where this frame first appeared in captured video).
- `dump_reproevents.jsonl` JSONL with `ReproeventsRecord` items corresponding to reproevents logs. Datetime information extracted from `client_time_iso` column in CVS file, and entire row is converted to JSON object `data` field.
- `dump_marks.jsonl` JSONL with `MarkRecord` items corresponding to global events used to synchronize all swimlanes and clocks.
- `dump_tmap.jsonl` JSONL with `TMapRecord` items specifying datetime mapping information between different clocks based on information and statistics extracted from the current session.

### Statistics
TBD:

### Code and Tools
TBD: 

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
  - in long scan from `ses-20240809` determined that we should look at lowest bit in `alink_flags` rather than 8-th bit of `alink_byte` to determine event start/stop.
- `reproevents` 
  - `isotime` field is precise and reliable, and looks like more precise than birch `iso_time`, fluctuation in range 0.00-0.01 sec.
  - `reproevents` events also matched with DICOMs well close to `birch`, but this is not always 100% match. It's possible that precision is even better than `birch` one, so it should be considered in future when calculating global clock information.
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
  - `birch` data for first 3 func scan x15 is omitted somehow and started from `008-func-bold_task-rest_acq-short1_run-04` at 10:27:12.
  - `psychopy` data for first 3 func scan x15 is omitted somehow and started from `008-func-bold_task-rest_acq-short1_run-04` at 10:27:12.
  - `psychopy\20240809_acq-med1_run-01.log` contains only 30 records rather than 150 ones. After manual inspection it looks like it's cutted in the middle of the scan at 10:39:06 rather than 10:43:06.

## TODO:
  - Use DataLad run to execute commands (https://handbook.datalad.org/en/latest/basics/basics-run.html)