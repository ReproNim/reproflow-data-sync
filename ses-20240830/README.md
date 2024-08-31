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
