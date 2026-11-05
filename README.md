# Windows Chores

A chores timer: a Windows-style stopwatch with laps, fastest and slowest lap markers, averages, a small always-on-top widget and an automatic text log, for anyone who times repeated tasks.

## What it does
- Times laps: when you press **Lap**, the lap is saved and the large timer starts again at `00:00:00.00`.
- Shows every lap in a table with the lap time, the total time so far and the average so far.
- Shows the session average under the table.
- Has an **Always on top** option and a small, movable widget that stays above other windows.
- Writes a log of every session and lap to `stopwatch_log.txt` in your **Documents** folder.
- Uses no keyboard shortcuts, so you can keep typing in other programs while it runs.

## What you need
- Windows 10 or 11.
- Python 3.8 or newer (from python.org or the Microsoft Store). It includes tkinter.
- No extra packages.

## Install
1. Download this project (green **Code** button, then **Download ZIP**) and unzip it, for example to `Downloads\windows-chores`.
2. If Python is not installed: press the **Windows key**, type **python** and press **Enter**. The Microsoft Store opens; click **Get**. If `python` is not found later, open **Settings > Apps > Advanced app settings > App execution aliases** and turn on **python.exe**.
3. Open the folder in File Explorer, click the address bar, type **cmd** and press **Enter**. A Command Prompt opens in that folder.

## How to use
1. Start the stopwatch:
   ```
   python stopwatch.py
   ```
2. Click the large blue **▶** button to start. It changes to **⏸**; click it again to pause.
3. Click **Lap** to save the current lap. The large timer starts again from zero. **Lap** only works while the stopwatch is running, so it is grey while paused.
4. Click **↺** to reset. It asks first, then clears the laps and ends the log session.
5. Tick **Always on top** to keep the window above other windows.
6. Click **Widget On/Off** to show or hide the small widget in the top-right corner of the screen. Drag it by its edge to move it. It has the same **▶/⏸**, **Lap** and **↺** buttons, and **✕** closes it.

## Settings and options
- **Always on top**: keeps the main window above other windows.
- **Widget On/Off**: the small widget is always on top and has no title bar.
- **Log file**: always `stopwatch_log.txt` in your Documents folder. The full path is shown at the bottom of the window ("Logging to: ...").

The log looks like this:

```
[SESSION START] 2026-01-05 09:00:12
LAP 01 | lap=00:02:10.45 | total=00:02:10.45 | avg=00:02:10.45
LAP 02 | lap=00:01:58.02 | total=00:04:08.47 | avg=00:02:04.23
[SESSION END]   2026-01-05 09:04:30 | laps=2 | total=00:04:08.47 | avg=00:02:04.23
```

A session starts with the first **▶** and ends when you reset or close the window.

## Safety notes
- The only file the stopwatch writes is `stopwatch_log.txt` in Documents. It only adds lines to the end; it never deletes or replaces anything. Delete or edit the file yourself whenever you like.
- **↺ (Reset)** clears the laps on screen after you confirm. The laps already written to the log stay there.
- Nothing is sent anywhere.

## Troubleshooting
- **No window appears**: check that `python --version` shows 3.8 or newer. If `python` is not found, try `py stopwatch.py`.
- **The log file is missing**: it is created at the first **▶**. Look at the path at the bottom of the window.
- **Fastest and Slowest are not colored**: they appear from two laps on.
- **The widget cannot be dragged**: drag it by the empty area around the time and buttons.

## How it works
The program is a single tkinter file. The time is measured with `time.perf_counter()`, and the display is refreshed every 20 ms with `after()`. The round buttons are drawn on small canvases, the lap list is a `ttk.Treeview`, and the widget is a borderless `Toplevel` with the `-topmost` attribute. Every log line is written to disk immediately, so the laps are kept in the log even if the program or the PC stops suddenly.

## License

MIT. See [LICENSE](LICENSE).
