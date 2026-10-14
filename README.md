# EX WIFI ENHANCE

A small Windows app that helps keep your WiFi connection **stable**.

**Honest note:** it does not make your internet faster or "boost" your signal. What it does is cut down on drop-outs and lag spikes caused by Windows power saving, reconnect you automatically when the link dies, and give you one-click versions of the usual network repair commands.

## Features
- **Live status:** SSID, signal bars, receive/transmit rate, band and channel (from `netsh wlan show interfaces`).
- **Stabilize (admin):** turns off WiFi adapter power saving and sets the power plan's wireless adapter setting to Maximum Performance. Turning it off puts your previous settings back.
- **Auto-reconnect watchdog:** pings 1.1.1.1 / 8.8.8.8 and runs `netsh wlan connect` after 3 failures in a row.
- **Repair:** `ipconfig /flushdns`, `/release`, `/renew`, plus an optional Winsock reset (needs a reboot).
- **Ping test:** average and min/max latency, plus packet loss.
- **Update check** in Settings. It only opens the download page; nothing installs automatically.

## Install
1. Download `EX_WIFI_ENHANCE.zip` from [Releases](../../releases/latest).
2. Extract the whole zip, then run `EX WIFI ENHANCE.exe` inside the `EX WIFI ENHANCE` folder. Keep the `_internal` folder next to it.
3. The app is unsigned, so SmartScreen may warn you: click **More info → Run anyway**. Some antivirus tools flag PyInstaller apps by mistake.
4. Admin rights are only needed for Stabilize, Release/Renew and Winsock reset. The app offers to restart itself as administrator when needed.

## Update
Close the app. Download `EX_WIFI_ENHANCE_update.zip`, which contains only the files that changed since the previous version, and extract it into the folder that contains `EX WIFI ENHANCE`, letting it overwrite existing files. If you are more than one version behind, use the full zip instead.

## Build from source (Windows)
```
pip install pyinstaller
pyinstaller --onedir --noconsole --name "EX WIFI ENHANCE" --icon logo.ico --add-data "logo.ico;." --add-data "logo256.png;." ex_wifi_enhance.py
```
