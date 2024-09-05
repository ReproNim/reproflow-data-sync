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
- `duration` - specifies duration in seconds till the next event in related swimlane clocks.

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
- `dump_psychopy.jsonl` Aggregated JSONL with items corresponding to psychopy logs. Target log file names extracted from QR codes and then filtered by MRI study datetime range. Datetime information extracted from `keys_time_str` field. Calculated fields:
  - `qrinfo_id` - optional, specifies related QR code ID from sessions's `dump_qrinfo.jsonl` file when exits.
- `dump_qrinfo.jsonl` JSONL with `QrRecord` items corresponding to QR codes logs. Datetime information extracted from `isotime_start` field (where this frame first appeared in captured video).
- `dump_reproevents.jsonl` JSONL with `ReproeventsRecord` items corresponding to reproevents logs. Datetime information extracted from `client_time_iso` column in CVS file, and entire row is converted to JSON object `data` field.
  - `duration` - duration in seconds till the next event in related swimlane clocks.
  - `state_duration` - duration in seconds till the next event when state will be changed to 0.
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
  - in `ses-20240809` we determined that client time in this logs is not precise and contains a lot of records with the same time, so it's not reliable to use it as a master clock.
  - in `ses-20240809` we also determined that `server_time` is not consistent and contains gap like 4 or 14 sec, and 7 trigger pulses are missed at all.
- `psychopy` 
  - `isotime` field is less precise, fluctuation in range 0.00-0.03 sec.
- `qrinfo` / `reprostim_video`
  - `isotime_start` field fluctuation in range 0.00-0.06 sec, and correlates with 60.0 FPS video capture, where each frame takes 0.017 sec.   
  - first QR code in each series has strange datetime offset around +0.320 sec (or 20 frames later on 60.0 FPS video) from other QR codes. Most likely it's related to Python script code presenting QR in experiments.
  - QR codes processing is not fast, looks like `reprostim/Parsing/generate_qrinfo.sh` script execution time is around x1-x4 slower comparing to related video, e.g. for 5 minutes video like 1920x1080, 60 FPS it can take up to 20 minutes to process. So in future it would be good idea to optimize `parse_wQR.py` script for better performance on demand.

- `ses-20240528`
  - problem to match other swimlanes with DICOMs at this moment, WiP. 
  - [ ] `qrinfo` data is not clean and consistent, but we have item with id `qrinfo-000006` and `keys_time_str` as `2024-05-28T11:06:29.435718-04:00`. This corresponds to `psychopy-000001`. Use this mapping between psychopy and qrinfo to match both swimlanes.
  - [ ] `dumps` series `005-func-bold_task-rest_run-1` has only 2 scans. And it looks like we have some small series in `qrinfo` and `psychopy` logs. Need to investigate this and if possible include series in marks.
- `ses-20240604`
  - produces most matches at this moment, but still some issues with psychopy, reprostim_video etc.
  - [ ] `dicoms` series `008-func-bold_task-rest_run-4_start` has invalid mapping with birch,psychopy and reproevents and as result invalid dicoms_offset 448 sec instead of 372 sec.
- `ses-20240809`
  - [x] under investigation, produces performance issues which partially are fixed, and swimlane matching issues.
  - [x] `birch` data for first 3 func scan x15 is omitted somehow and started from `008-func-bold_task-rest_acq-short1_run-04` at 10:27:12. This is ok for provided logs, somehow birch device is restarted in the middle of the scan.
  - [x] `psychopy` data for first 3 func scan x15 is omitted somehow and started from `008-func-bold_task-rest_acq-short1_run-04` at 10:27:12. This is ok for provided logs.
  - [x] `psychopy\20240809_acq-med1_run-01.log` contains only 30 records rather than 150 ones. After manual inspection it looks like it's cut in the middle of the scan at 10:39:06 rather than 10:43:06. So it's broken input data from psychopy.
  - [ ] `qrinfo` it looks like video duration is only 6:37 instead of 32:07 (based on reprostim json metadata and `2024.08.09-10.31.00.087--2024.08.09-11.03.07.318.mkv` file name ), and it contains only 3 short series of QRs. Need in future investigation of `reprostim-videocapture` utility and `ffmpeg` params.
  - [ ] `reproevents` started from `reproevents-000263` it produces invalid data. There are a lot of records in `events.csv/@client_time_iso` with time like `2024-08-09T10:49:39`. Real series time range based on the swimlanes is around `10:47:48`--`10:52:46` and scans count is 150. So it looks like some performance issues on hardware or software side recording events log.
  - [ ] `reproevents` related to original lines in `events.csv` `638:639`, `747:748` `server_time` 217.389434 and 339.392153 has untypical duration 4 and 14 sec instead of 2 sec. 
  - [ ] `reproevents` related to `013-func-bold_task-rest_acq-med1_run-02` series with 150 slices contains only 143 events instead of 150 ones, 7 are missed somehow. Series NTP EST time is `10:47:48`--`10:52:46` .
- `ses-20240830`
  - [ ] !!! No QR code recorded at all. DICOMS time is `11:35:22 -- 11:55:24`, 150 series started at `11:44:26` for 5 mins and this video file `2024.08.30-11.31.56.000--2024.08.30-11.48.03.377.mkv` should contain QR codes. But we see there error:
    - Video duration significant mismatch (real/file name): `569.2333333333333` sec vs `967.377` sec
    - Interesting thing is that in mkv.log file we see that fps was 59-60 and then dropped to 40-38 e.g.:
      - 2024-08-30 11:32:01.276 [INFO] [3393844] frame=  305 `fps= 60` q=31.0 size=     192kB time=00:00:04.22 bitrate= 372.6kbits/s speed=0.825x    
      - 2024-08-30 11:42:43.949 [INFO] [3393844] frame=27567 `fps= 43` q=31.0 size=   17555kB time=00:07:40.13 bitrate= 312.5kbits/s speed=0.71x    
      - 2024-08-30 11:46:55.547 [INFO] [3393844] frame=34185 `fps= 38` q=31.0 size=   19967kB time=00:09:28.89 bitrate= 287.5kbits/s speed=0.633x    
    - Also we can see that last frame was around 11:46, and count more or less corrseponds to number of frames in video:
      - 2024-08-30 11:46:56.080 [INFO] [3393844] frame=`34190` fps= 38 q=31.0 size=   19967kB time=00:09:28.97 bitrate= 287.5kbits/s speed=0.632x DTS 19356550163393, next:569
      - parse_wQR detected frame count: `34154`
    - root log in reproiner started recording 11:31:56, and stopped 11:48:03, somehow ffmpeg thread was terminated. And then at 11:56:13 capture was terminated by data/notification from device (Whack resolution).
  - [ ] DICOMS MRI clock in this study has offset around -27 sec in contrast to +391 sec in previous session. This 7 minutes gap or jump causes current match series algorithm to fail. Probably to see other swimlanes tmap record will be created manually for this series in `code/repronim_tmap.jsonl` file.
  - [ ] `dump_reproevents.py` bad performance, need to optimize it (execution time around 40 sec).
  - [ ] `reproevents/events.csv` doesn't contain any valid `client_time_iso` data. If possible we should look for older *.csv file if any:
    - started at : 2024-08-30T`15:47:03`.055736-04:00
    - ended   at : 2024-08-30T`20:02:33`.580731-04:00
    - but study range which in ISO time was `11:35:49 - 11:55:52`.
  - [ ] `psychopy` logs conatins only last 7 series, and not 10 ones. Some information listed below:
    - Time for first 3 series: `11:35:49 - 11:39:59` 
    - `20240830_acq-short1_run-01.log`, `20240830_acq-short1_run-02.log`, `20240830_acq-short1_run-03.log` contains only 2 header records end no event data at all.

## TODO:
  - Use DataLad run to execute commands (https://handbook.datalad.org/en/latest/basics/basics-run.html)