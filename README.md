# Data samples for ReproFlow time synchronization effort

It is primarily containing data produced/recorded in the course of the
https://github.com/ReproNim/reprostim project (which currently contains
also ReproEvents). The goal is to automatically capture

- audio-video stimuli as presented to the participants using our
  ReproStim's reprostim-videocapture

- events information as recorded by response capturing device (of
  https://curdes.com ATM).  This effort includes 2 approaches

  - "patching" BIRCH interface software (in Python, not yet open)
    to collect/record time stamps in easily accessible form

  - develop/interface custom MicroPython board to collect events via 
    DB35 socket available on some curdes devices.

and align them (in time) to fMRI data, which was obtained by the MRI
scanner.

As the events information contains trigger pulses as well, in principle it
makes it relatively trivial to align those if automatically captured.

Videos are trickier and hence we want to automate collection of
"callibration" data samples while performing regular MRI QA.

See https://github.com/ReproNim/reprostim/issues/13 for more diagrams and
information.

This repository contains all collected data, and psychopy "stimuli" displaying
QR codes with metadata.
