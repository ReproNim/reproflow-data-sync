* Goal: collect another sample after NTP was configured on MRI + get closer to full automation during QA
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

** we did "new" sequences

... on boox

* Part 2 -- trying on reproiner

** within screen on remote
reprostim@reproiner:~/proj/repronim$ bash ./run-repronim-reprostim
reprostim timesync-stimuli
2025-04-23 13:07:32,801 [INFO] main script started
Traceback (most recent call last):
  File "/opt/psychopy/psychopy_2024.2.5_py3.10/bin/reprostim", line 8, in <module>
    sys.exit(main())
  File "/opt/psychopy/psychopy_2024.2.5_py3.10/lib/python3.10/site-packages/click/core.py", line 1161, in __call__
    return self.main(*args, **kwargs)
  File "/opt/psychopy/psychopy_2024.2.5_py3.10/lib/python3.10/site-packages/click/core.py", line 1082, in main
    rv = self.invoke(ctx)
  File "/opt/psychopy/psychopy_2024.2.5_py3.10/lib/python3.10/site-packages/click/core.py", line 1697, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
  File "/opt/psychopy/psychopy_2024.2.5_py3.10/lib/python3.10/site-packages/click/core.py", line 1443, in invoke
    return ctx.invoke(self.callback, **ctx.params)
  File "/opt/psychopy/psychopy_2024.2.5_py3.10/lib/python3.10/site-packages/click/core.py", line 788, in invoke
    return __callback(*args, **kwargs)
  File "/opt/psychopy/psychopy_2024.2.5_py3.10/lib/python3.10/site-packages/click/decorators.py", line 33, in new_func
    return f(get_current_context(), *args, **kwargs)
  File "/opt/psychopy/psychopy_2024.2.5_py3.10/lib/python3.10/site-packages/reprostim/cli/cmd_timesync_stimuli.py", line 137, in timesync_stimuli
    res = do_main(
  File "/opt/psychopy/psychopy_2024.2.5_py3.10/lib/python3.10/site-packages/reprostim/qr/timesync_stimuli.py", line 144, in do_main
    from psychopy import core, event, visual
  File "/opt/psychopy/psychopy_2024.2.5_py3.10/lib/python3.10/site-packages/psychopy/event.py", line 70, in <module>
    from pyglet.window.mouse import LEFT, MIDDLE, RIGHT
  File "/opt/psychopy/psychopy_2024.2.5_py3.10/lib/python3.10/site-packages/pyglet/window/__init__.py", line 1919, in <module>
    gl._create_shadow_window()
  File "/opt/psychopy/psychopy_2024.2.5_py3.10/lib/python3.10/site-packages/pyglet/gl/__init__.py", line 206, in _create_shadow_window
    _shadow_window = Window(width=1, height=1, visible=False)
  File "/opt/psychopy/psychopy_2024.2.5_py3.10/lib/python3.10/site-packages/pyglet/window/xlib/__init__.py", line 171, in __init__
    super(XlibWindow, self).__init__(*args, **kwargs)
  File "/opt/psychopy/psychopy_2024.2.5_py3.10/lib/python3.10/site-packages/pyglet/window/__init__.py", line 591, in __init__
    display = pyglet.canvas.get_display()
  File "/opt/psychopy/psychopy_2024.2.5_py3.10/lib/python3.10/site-packages/pyglet/canvas/__init__.py", line 94, in get_display
    return Display()
  File "/opt/psychopy/psychopy_2024.2.5_py3.10/lib/python3.10/site-packages/pyglet/canvas/xlib.py", line 123, in __init__
    raise NoSuchDisplayException('Cannot connect to "%s"' % name)
pyglet.canvas.xlib.NoSuchDisplayException: Cannot connect to "None"
0.9350  DEBUG   Opening message catalog /opt/psychopy/psychopy_2024.2.5_py3.10/lib/python3.10/site-packages/psychopy/localization/../app/locale/en_US/LC_MESSAGE/messages.mo for locale en_US
0.9353  DEBUG   Locale for 'en_US' not found. Using default.
reprostim@reproiner:~/proj/repronim$ cat ./run-repronim-reprostim
#!/bin/bash

singularity exec repronim-reprostim-0.7.5.sing /opt/psychopy/psychopy_2024.2.5_py3.10/bin/reprostim timesync-stimuli --mode event --audio-lib sounddevice -t 1000 

** on the phone -- as when run directly on the device but likely it is
just because of wayland or outdated reprostim...

** wayland??


reprost+ 2615742  1.5  0.6 4521488 223364 ?      Ssl  12:52   0:16     /usr/bin/gnome-shell
reprost+ 2622782  0.1  0.2 840004 89748 ?        Sl   13:07   0:00       /usr/bin/Xwayland :0 -rootless -noreset -accessx -core -auth /run/user/1001/.mutter-Xwaylandauth.MQ7H52 -listenfd 4 -listenfd 5 -displayfd 6 -initfd 7


** logged out and in gdm logged in with "Gnome on Xorg"

root     2614309  0.0  0.0 240384 11128 ?        Ssl  12:51   0:00   /usr/sbin/gdm3
root     2624480  0.1  0.0 165348 10484 ?        Sl   13:09   0:00     gdm-session-worker [pam/gdm-password]
reprost+ 2625084  0.0  0.0 162780  6864 tty2     Ssl+ 13:10   0:00       /usr/libexec/gdm-x-session --run-script /usr/bin/gnome-session
reprost+ 2625086  4.4  0.3 1162980 104496 tty2   Sl+  13:10   0:01         /usr/lib/xorg/Xorg vt2 -displayfd 3 -auth /run/user/1001/gdm/Xauthority -nolisten tcp -background none -noreset -keeptty -novtswitch -verbose 3
reprost+ 2625177  0.0  0.0 297952 18464 tty2     Sl+  13:10   0:00         /usr/libexec/gnome-session-binary


