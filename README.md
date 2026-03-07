# Anti-Raid Multi-Bot Panel

Hosts up to 5 independent Discord anti-raid bots via a simple web panel.

## Features
- Web dashboard to add bot tokens
- Raid detection (mass joins → auto-ban)
- Anti-spam (mute on flood)
- Profanity filter
- !setup command for Muted role

## Local Setup
1. pip install -r requirements.txt
2. python main.py
3. Visit http://localhost:5000

## Hosting on Render
- New Web Service → Python → Build: pip install -r requirements.txt
- Start: python main.py
