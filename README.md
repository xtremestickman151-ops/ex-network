# EX NETWORK

*(formerly EX WIFI ENHANCE)*

A small Windows app that helps keep your WiFi connection **stable**.

**Honest note:** it does not make your internet faster or "boost" your signal. What it does is cut down on drop-outs and lag spikes caused by Windows power saving, reconnect you automatically when the link dies, and give you one-click versions of the usual network repair commands.

## Features
- **Live status:** SSID, signal bars, receive/transmit rate, band and channel (from `netsh wlan show interfaces`).
- **Stabilize (admin):** turns off WiFi adapter power saving and sets the power plan's wireless adapter setting to Maximum Performance. Turning it off puts your previous settings back.
- **Auto-reconnect watchdog:** pings 1.1.1.1 / 8.8.8.8 and runs `netsh wlan connect` after 3 failures in a row.
- **Repair:** `ipconfig /flushdns`, `/release`, `/renew`, plus an optional Winsock reset (needs a reboot).
- **Ping test:** average and min/max latency, plus packet loss.
- **Update check** in Settings. It only opens the download page; nothing installs automatically.

## Install (recommended)
1. Download **`EX NETWORK Setup <version>.exe`** from [Releases](../../releases/latest) and run it. No admin rights needed: it installs for your user to `%LOCALAPPDATA%\Programs\EX NETWORK`, adds a Start menu shortcut (Desktop shortcut optional), and registers an uninstaller under Settings → Apps.
2. The app and installer are unsigned, so SmartScreen may warn you: click **More info → Run anyway**. Some antivirus tools flag PyInstaller apps by mistake.
3. Admin rights are only needed inside the app for Stabilize, Release/Renew and Winsock reset. The app offers to restart itself as administrator when needed.

## Update
Upgrading from EX WIFI ENHANCE (1.1.x): run the EX NETWORK installer. It removes the old "EX WIFI ENHANCE" folder and shortcuts and installs to `%LOCALAPPDATA%\Programs\EX NETWORK`.

Run the newest installer over your existing install; it replaces the app files cleanly. *Check for updates* in Settings opens it for you.

Portable alternative: `EX_NETWORK.zip` is the full app (extract the whole folder). `EX_WIFI_ENHANCE_update.zip` (shipped up to 1.1.3) contained only changed files; from 1.2.0 on, use the installer or the full zip.

## Build from source (Windows)
```
pip install pyinstaller
pyinstaller --onedir --noconsole --name "EX NETWORK" --icon logo.ico --version-file version.txt --add-data "logo.ico;." --add-data "logo256.png;." ex_wifi_enhance.py
```
Installer: compile `installer.iss` with Inno Setup 6.

---
©2026 EX Inc.
