* Part 1 -- try to recall how we did it and do the same again
** repeating what we did in ses-20250127/ following duct logs we ran

reprostim timesync-stimuli --mode event --audio-lib sounddevice -t 100

4 times:

 ~/proj/repronim/reproflow-data-sync/ses-20250127/incoming  master *1 ?8 ▓▒░─────
❯ con-duct ls
PREFIX                                COMMAND                                                                EXIT_CODE WALL_CLOCK_TIME PEAK_RSS
.duct/logs/2025.01.27T11.34.32-70567_ reprostim timesync-stimuli --mode event --audio-lib sounddevice -t 100 0         55.602 sec      437.4 MB
.duct/logs/2025.01.27T11.36.43-71022_ reprostim timesync-stimuli --mode event --audio-lib sounddevice -t 100 0         52.988 sec      436.3 MB
.duct/logs/2025.01.27T11.38.49-71499_ reprostim timesync-stimuli --mode event --audio-lib sounddevice -t 100 0         108.977 sec     437.6 MB
.duct/logs/2025.01.27T11.41.58-72437_ reprostim timesync-stimuli --mode event --audio-lib sounddevice -t 100 0         53.945 sec      436.8 MB

and had 5 runs of DICOMs -- all acq-short1

❯ ls ../DICOMS
001-anat-scout_ses-{date}/          005-func-bold_task-rest_acq-short1_run-01/  009-func-bold_task-rest_acq-short1_run-04/
002-anat-scout_ses-{date}_MPR_sag/  006-func-bold_task-rest_acq-short1_run-01/  010-func-bold_task-rest_acq-short1_run-05/
003-anat-scout_ses-{date}_MPR_cor/  007-func-bold_task-rest_acq-short1_run-02/
004-anat-scout_ses-{date}_MPR_tra/  008-func-bold_task-rest_acq-short1_run-03/
