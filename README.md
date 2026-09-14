# Robot Window Nightlight

A quiet 800×480 animated room intended for a seven-inch HDMI display and an
original Raspberry Pi Zero W.

The robot follows a slow four-stop routine around the room, with longer pauses
at the window. Its antenna and chest lights pulse while rain stays entirely
outside on the glass. Equipment indicators change quietly, distant vehicles
occasionally cross the skyline, rare lightning softly illuminates the window,
and an extremely shy visitor may peek from the lower machinery. There is
deliberately no sound.

A small four-wheeled rover pet wanders independently between the rug, window,
plant, and cabinets. It occasionally follows the resident robot and takes long
rests in its favorite floor spot.

The room runs continuously. This monitor keeps its backlight illuminated even
when HDMI power management requests sleep, so a scheduled black screen would
provide no meaningful backlight-saving benefit.

Halloween decorations are selected automatically for the entire month of
October, with the normal room returning on November 1. Press `H` to preview the
opposite room manually; the automatic calendar selection returns after restart.
For a headless preview, create an empty `halloween-preview.flag` beside the
program and restart. Delete that flag to restore calendar-only selection.

## Windows preview

Double-click `run_windows.bat`. Press `F` for fullscreen and `Esc` to quit.

## Raspberry Pi

```bash
sudo apt update
sudo apt install -y python3-pygame
python3 robot_nightlight.py
```

The program is capped at 12 FPS and uses only pre-scaled 800×480 artwork plus
lightweight drawing effects, making it suitable for the original Pi Zero W.
