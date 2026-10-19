# Village Developer Mini Game

A small real-time strategy game built with Python and Pygame. Build and upgrade your village, train units, defend against enemy waves, and complete all eight levels.

## Features

- Eight campaign levels with increasingly difficult enemy waves
- Gold and elixir resource management
- Train barbarian and wizard units
- Build gold mines, elixir collectors, and walls
- Upgrade the town hall, mines, and collectors
- Select units individually or with a drag box
- Move selected units and target enemies
- Particle effects, announcements, health bars, and level transitions

## Requirements

- Python 3.10 or newer
- Pygame

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python 1.py
```

## Controls

| Key / Input | Action |
| --- | --- |
| `1` | Train a barbarian |
| `2` | Train a wizard |
| `G` | Build or upgrade a gold mine |
| `E` | Build or upgrade an elixir collector |
| `W` | Place a wall |
| `U` | Upgrade the town hall |
| Left click | Select a unit or place a building |
| Shift + left click | Add or remove a unit from the selection |
| Left-button drag | Select multiple units |
| Right click | Move selected units or attack an enemy |
| `Esc` | Cancel placement or clear selection |
| `Tab` | Clear selection |
| `Enter` | Continue after completing a level |

## Project structure

```text
.
├── 1.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Future improvements

- Add save and load functionality
- Split game state, rendering, and input handling into modules
- Add sound effects and background music
- Add automated tests for resource and combat rules
- Add a packaged executable for Windows

## License

This project is available for learning and portfolio use.
