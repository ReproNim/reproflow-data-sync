- It was ran from Yarik's laptop, not reproiner.  Failed to install psychopy in a virtualenv on reproiner -- might need wx etc libraries
- Laptop clock is not entirely in sync :-/

    ❯ date --iso-8601=ns | tr "\n" "\t" ; for h in reproiner birch localhost; do ssh $h 'date --iso-8601=ns | tr "\n" "\t" ; hostname' & done; sleep 3;
    2024-05-28T11:50:40,131809493-04:00	
    2024-05-28T11:50:40,168054275-04:00	bilena
    2024-05-28T11:50:40,777833551-04:00	reproiner
    2024-05-28T11:50:40,813447469-04:00	Birch-4115966

so over 600ms off. I am installing ntpsec now

- There should be two last runs of data and logs and videos

 We did restart the psychopy script  a few times though

# VMDOCUA Notes

- `ses-20240528`
  - problem to match other swimlanes with DICOMs at this moment, WiP. 
  - [ ] `qrinfo` data is not clean and consistent, but we have item with id `qrinfo-000006` and `keys_time_str` as `2024-05-28T11:06:29.435718-04:00`. This corresponds to `psychopy-000001`. Use this mapping between psychopy and qrinfo to match both swimlanes.
  - [ ] `dumps` series `005-func-bold_task-rest_run-1` has only 2 scans. And it looks like we have some small series in `qrinfo` and `psychopy` logs. Need to investigate this and if possible include series in marks.
- `ses-20240604`
  - produces most matches at this moment, but still some issues with psychopy, reprostim_video etc.
  - [ ] `dicoms` series `008-func-bold_task-rest_run-4_start` has invalid mapping with birch,psychopy and reproevents and as result invalid dicoms_offset 448 sec instead of 372 sec.
