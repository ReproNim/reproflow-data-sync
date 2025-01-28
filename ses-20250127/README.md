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
