# Gesture Controller

**Play Brawl Stars with your hands. No touch, no keyboard, no controller.**

Gesture Controller uses your webcam to detect hand gestures in real time and maps them to in-game inputs on LDPlayer 9 — move, attack, super, gadget, hypercharge, all from hand movements alone.

---

## Demo

> 🎥 *Demo GIF coming soon*

---

## Features

- **7 gesture-to-action mappings** covering all core Brawl Stars inputs
- **Real-time detection** at 30 FPS with sub-20ms input latency
- **Tap vs. drag intelligence** — the system distinguishes between a quick tap and a held drag, so accidental triggers are virtually eliminated
- **8-directional movement** including diagonals
- **One-click Windows installer** — no Python, no terminal required

---

## Gesture Reference

| Gesture | Hand | Action |
|---|---|---|
| Fist + drag | Left | Move (WASD, 8 directions) |
| Pinch tap | Right | Instant attack (E) |
| Pinch + drag | Right | Aimed attack (X + mouse aim) |
| Fist tap | Right | Instant super (F) |
| Fist + drag | Right | Aimed super (C + mouse aim) |
| Peace sign ✌️ | Right | Hypercharge (R) |
| L-shape 🤙 | Right | Gadget (Q) |

---

## Requirements

- Windows 10 or 11
- Webcam (built-in or external)
- [LDPlayer 9](https://www.ldplayer.net/) installed at `C:\LDPlayer\LDPlayer9\`
- Brawl Stars installed inside LDPlayer

---

## Installation

1. Download `GestureController_Setup.exe` from the [latest release](https://github.com/Sithi-Vignesh/Gesture-Controller/releases/latest)
2. Run the installer and follow the prompts
3. Launch **Gesture Controller** from your Desktop or Start Menu

---

## LDPlayer Keybinding Setup

For gestures to map correctly, configure LDPlayer's keyboard controls to match:

| Key | Action |
|---|---|
| `W` `A` `S` `D` | Movement joystick |
| `E` | Attack button |
| `X` | Aimed attack (hold) |
| `F` | Super button |
| `C` | Aimed super (hold) |
| `R` | Hypercharge button |
| `Q` | Gadget button |

Open LDPlayer → **Keyboard Control** → assign the keys above to the corresponding on-screen buttons in Brawl Stars.

---

## How to Use

1. Open LDPlayer and launch Brawl Stars
2. Open **Gesture Controller** — the camera feed will appear
3. Position yourself so both hands are clearly visible in frame
4. Enter a match and start gesturing

**Tips:**
- Use **small wrist movements** for movement control — large sweeps overshoot
- Keep hands roughly **30–60cm from the camera** for best detection
- Good lighting improves tracking accuracy significantly

---

## Tech Stack

- Python, OpenCV, MediaPipe Hands
- pyautogui, win32gui
- PyQt6
- PyInstaller + NSIS

---

## Roadmap

- **V1** ✅ — 7 gestures, LDPlayer input, Windows installer
- **V2** — WiFi ADB support, device profiles, cloud config via Supabase
- **V3** — Fully on-device Android, no PC or ADB required

---

## License

MIT
