* Summary: another problematic collection

 - I found magewell cable for reprostim disconnected since reproiner
   again lost its "glue" to the side.
 - I improved mount of the reproiner (screws now) and after the session
   also added external usb hub and plugged in the 2nd reproiner
   into it
 - I created singularity image and tried to run  on reproiner.
   But apparently there is no singularity there yet since not in 
   debian stable!  TODO: install singularity!
 - singularity "run" seems to not pass options inside the tool!
   This one I build directly from Singularity file so there
   might be one more gotcha.  TODO: check/fix
 - Somehow due to container or version we are not getting trigger
   pulses registerred while running from within container!  
   So first 3 runs 

 Additional notes

 - I think that the 2nd magewell for MRI console was disconnected,
   since I needed USB for keyboard. So might affect some video collection?

* short1_run-01 -- I did not connect triggers pulse USB cable! damn it
* run-2 and 3 --- were connected and I did see 5 when I focus on terminal

    but it didn't register as event within psychopy script which I ran inside fresh container image

    ❯ singularity exec /home/yoh/proj/repronim/containers/images/repronim/repronim-psychopy--2024.1.4.sing tools/reprostim-timesync-stimuli `mdate`_acq-short1_run-03.log 1

    note that we did not pass args so I had to use exec explicitly, also screen was 1 whioch is odd

* med just one run-01 -- were getting short on time

* 5 short ones automatically starting after each other -- with a single psychopy for all of them acq-short2_run-01-05.log

They all were automatically started by scanner without waiting for
operator input/click.

So without checking for stability within, we would have 5 DICOM series -- do we
see similar jumps in offset?

# VMDOCUA notes

- `ses-20240830`
  - [ ] !!! No QR codes recorded at all. DICOMS time is `11:35:22 -- 11:55:24`, 150 series started at `11:44:26` for 5 mins and this video file `2024.08.30-11.31.56.000--2024.08.30-11.48.03.377.mkv` should contain QR codes. But we see there error:
    - Video duration significant mismatch (real/file name): `569.2333333333333` sec vs `967.377` sec
    - Interesting thing is that in mkv.log file we see that fps was 59-60 and then dropped to 40-38 e.g.:
      - 2024-08-30 11:32:01.276 [INFO] [3393844] frame=  305 `fps= 60` q=31.0 size=     192kB time=00:00:04.22 bitrate= 372.6kbits/s speed=0.825x    
      - 2024-08-30 11:42:43.949 [INFO] [3393844] frame=27567 `fps= 43` q=31.0 size=   17555kB time=00:07:40.13 bitrate= 312.5kbits/s speed=0.71x    
      - 2024-08-30 11:46:55.547 [INFO] [3393844] frame=34185 `fps= 38` q=31.0 size=   19967kB time=00:09:28.89 bitrate= 287.5kbits/s speed=0.633x    
    - Also we can see that the last frame was around 11:46, and it more or less corresponds to frames count in video:
      - 2024-08-30 11:46:56.080 [INFO] [3393844] frame=`34190` fps= 38 q=31.0 size=   19967kB time=00:09:28.97 bitrate= 287.5kbits/s speed=0.632x DTS 19356550163393, next:569
      - parse_wQR detected frame count: `34154`
    - root log in reproiner started recording 11:31:56, and stopped 11:48:03, somehow ffmpeg thread was terminated. And then at 11:56:13 capture was terminated by data/notification from device (Whack resolution).
  - [ ] DICOMS MRI clock in this study has offset around -27 sec in contrast to +391 sec in previous session. This 7 minutes gap or jump causes current match series algorithm to fail. Probably to see other swimlanes tmap record will be created manually for this series in `code/repronim_tmap.jsonl` file. Note: think about some command line option to dump_marks to explicitly specify clock offset, to stick and force specific time, rather than manual editing of tmap JSONL file. 
  - [ ] `dump_reproevents.py` bad performance, need to optimize it (execution time around 40 sec).
  - [ ] `reproevents/events.csv` doesn't contain any valid `client_time_iso` data. If possible we should look for older *.csv file if any:
    - started at : 2024-08-30T`15:47:03`.055736-04:00
    - ended   at : 2024-08-30T`20:02:33`.580731-04:00
    - but study range which in ISO time was `11:35:49 - 11:55:52`.
  - [ ] `psychopy` logs conatins only last 7 series, and not 10 ones. Some information listed below:
    - Time for first 3 series: `11:35:49 - 11:39:59` 
    - `20240830_acq-short1_run-01.log`, `20240830_acq-short1_run-02.log`, `20240830_acq-short1_run-03.log` contains only 2 header records and no event data at all.