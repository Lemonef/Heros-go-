# Battle Heroes Defense

A 2D strategic tower defense game where you deploy heroes with unique skills to defeat waves of enemies. Built with Python using `pygame` for gameplay and `tkinter` + `matplotlib`/`seaborn` for data visualization.

---

## Requirements

- Python 3.10+
- pip (Python package manager)

### Install dependencies:
```bash
pip install -r requirements.txt
```

> If you're on Linux and get a Tkinter error, install it with:
```bash
sudo apt-get install python3-tk
```

---

## How to Run the Game

Run the main script:
```bash
python "heros go!.py"
```

---

## Gameplay Overview
- Deploy heroes: Archer, Warrior, Mage, Healer
- Use strategic skills: Buffs, AOE attacks, Group Heals
- Defend your base and destroy the enemy base to win
- Win a stage to unlock the next, where enemies become stronger

---

## Data Visualization
During gameplay, stats like hero usage, ability frequency, energy usage, and more are tracked.

Open settings and click "Show Stats" to launch analytics (opens a Tkinter GUI with interactive plots).

---

## Project Structure
```
heros-go-/
├── heros go!.py           # Main game entry point
├── requirements.txt       # Python dependencies
├── .gitignore             # Git exclusion rules
├── LICENSE                # MIT License
├── screenshots/           # Gameplay & data screenshots
├── core/                  # Screen, animation, resource, tracker
├── units/                 # Hero, Enemy, Base
├── combat/                # Attacks, Skills, Projectiles
├── ui/                    # Buttons and menus
├── settings/              # Settings window
└── analytics/             # Data visualization GUI
```

---

## Screenshots
See the `screenshots/` folder for gameplay and analytics UI examples.

---

## License
MIT — see [LICENSE](./LICENSE) for details.
