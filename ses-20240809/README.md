## 20240809

### Summary

- Earlier short runs are no good
- Useful bugs unraveled in the process
- Reported time difference from DICOMs to Terry and he relayed to Siemens tech who promised to "manually sync" the time on the scanner that day during the maintenance.

### 20240809_acq-short1_run-01.log -- important finding by mistake

- I forgot to connect usb for trigger pulse to my laptop.  
- As a result stimuli did not present any qrcode (although I thought there was a flip) and only at the end when I pressed 'q'.
- But also what was odd is that on birch the .json file also did not get any trigger pulse logged
- IS BIRCH LOGGING WHEN USB IS DISCONNECTED? DONE: emailed Ben of curdes about this.
- but we did them collected using our micropython board -- so they were at TTL level!
- I then connected usb cable leading to birch.

### 20240809_acq-short1_run-02.log -- "mistake" again

- I did not switch focus to psychopy window (apparently important but actually is not generally -- must be my laptop bisbehaving), so trigger pulses sent as '5's were not picked up by psychopy.
- But THEY WERE SENT overall over usb - so people would not know that birch did not record!
- The birch did not record any trigger pulse.

- And it did not record any trigger pulse or "live heartbeat" since Aug 02nd!
very odd.  It is set to trackball. last log lines (show also today I redid output mode so it is overall alive)
 
    pi@Birch-4115966:/mnt/td $ tail -f 20240604-135337
    {"epoch_time": 1722631530.009796, "iso_time": "2024-08-02T16:45:30.009796-04:00", "time": -859.1045919999999, "alink_byte": 255, "alink_flags": 0}
    {"epoch_time": 1722631590.0134468, "iso_time": "2024-08-02T16:46:30.013447-04:00", "time": -799.1045649999999, "alink_byte": 255, "alink_flags": 0}
    {"epoch_time": 1722631650.0115576, "iso_time": "2024-08-02T16:47:30.011558-04:00", "time": -739.1036629999999, "alink_byte": 255, "alink_flags": 0}
    {"epoch_time": 1722631710.013122, "iso_time": "2024-08-02T16:48:30.013122-04:00", "time": -679.103136, "alink_byte": 255, "alink_flags": 0}
    {"epoch_time": 1722631770.0143404, "iso_time": "2024-08-02T16:49:30.014340-04:00", "time": -619.1024839999998, "alink_byte": 255, "alink_flags": 0}
    {"epoch_time": 1722631807.26516, "iso_time": "2024-08-02T16:50:07.265160-04:00", "time": -581.8509999999999, "alink_byte": 254, "alink_flags": 1}
    {"epoch_time": 1722631807.266135, "iso_time": "2024-08-02T16:50:07.266135-04:00", "time": -581.8481649999999, "alink_byte": 252, "alink_flags": 0}
    {"time": 0, "tick": 1995308726, "description": "Handheld auto-detected", "epoch_time": 1722631831.855575, "iso_time": "2024-08-02T16:50:31.855575-04:00", "handheld": "HHSC-TRK-2", "gains": [0, 0, 0, 0, 19, 18, 17, 17]}
    {"time": 0, "tick": 1998597464, "description": "Output mode selected.", "epoch_time": 1722631835.1443074, "iso_time": "2024-08-02T16:50:35.144307-04:00", "output_mode": "HID_TRACK_COMP"}
    {"time": 0, "tick": 1623264401, "description": "Output mode selected.", "epoch_time": 1723211277.7834074, "iso_time": "2024-08-09T09:47:57.783407-04:00", "output_mode": "HID_TRACK_COMP"}


### 20240809_acq-short1_run-03.log 

- We switched to another mode for trackball -- HID_MOUSE_1 and that did not record anything too.
- My laptop also started to misbehave with those "random" events sent by X and started to scroll terminal. my touchscreen was disabled already before sleep. 
- Selecting in terminal for the clipboard stopped working!
- I ctrl-C'ed the  psychopy script
- Terry connected 2x2 button thingie, but birch in Autodetect said it was 1x1 !
- Terry rebooted the birch!
- Birch correctly selected 2x2...

  only then we unplug/plug USB, did reselect of device and the output mode 

### 20240809_acq-short1_run-04.log 

This one finally worked out ok and birch and everything seems has recorded stuff... NOT THE VIDEO GRAB!!!

main log only has from a few minutes back that it killed the ffmpeg:

    Killed
    2024-08-09 10:20:16.605 [INFO] [2906999] :      Ffmpeg thread terminated. Saving video /data/reprostim/Videos/2024/08/2024.08.09-09.45.15.996--2024.08.09-10.20.16.605.mkv
    2024-08-09 10:20:16.606 [INFO] [2906999] REPROSTIM-METADATA-JSON: {"cap_isotime_start":"2024-08-09T09:45:15.996523","cap_ts_start":"2024.08.09-09.45.15.996","json_isotime":"2024-08-09T10:20:16.606375","json_ts":"2024.08.09-10.20.16.606","message":"ffmpeg thread terminated","type":"session_end"} :REPROSTIM-METADATA-JSON

and we scanned at 10:25 or so....  when I unplugged video we got

    2024-08-09 10:30:22.162 [INFO] [75038] REPROSTIM-METADATA-JSON: {"cap_isotime_start":"2024-08-09T09:45:15.996523","cap_isotime_stop":"2024-08-09T10:30:22.130324","cap_ts_start":"2024.08.09-09.45.15.996","cap_ts_stop":"2024.08.09-10.30.22.130","json_isotime":"2024-08-09T10:30:22.130343","json_ts":"2024.08.09-10.30.22.130","message":":\tWhack resolution: 4104x23416. Stopped recording","type":"capture_stop"} :REPROSTIM-METADATA-JSON
    2024-08-09 10:30:22.162 [INFO] [75038] stop record says: terminating ffmpeg with SIGINT
    2024-08-09 10:30:22.179 [INFO] [75038] ffmpeg pid:
    2024-08-09 10:30:22.179 [INFO] [75038] 2024.08.09-10.30.22.130 :        Whack resolution: 4104x23416. Stopped recording

so unclear why it stopped recording before!

### 20240809_acq-short1_run-05.log  -- first success!

I think all went well.  There was first fast QR code flashing on the screen really fast... check what it is!

### 20240809_acq-short1_run-06.log  -- 2nd success!

### 20240809_acq-short1_run-07.log  -- 3nd success!
### 20240809_acq-med1_run-01.log  -- screw ups!

   - stimuli script stopped by itself after only few dynamics:

    ...
    Waiting for an event
    Waiting for an event
    Waiting for an event
    Waiting for an event
    2.8252 	WARNING 	Monitor specification not found. Creating a temporary one...
    2.8469 	WARNING 	User requested fullscreen with size [800 600], but screen is actually [1920, 1080]. Using actual size
    ./qr_code_flips.py `mdate`_acq-med1_run-01.log 1  61.72s user 13.06s system 88% cpu 1:24.49 total
    ❯ 555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555

   I fixed up script to do up to 300 dynamics.

   TODO: make it smart!

- we did few more med1 runs.  I lost connection to birch and reproiner -- smaug seems to be down!

