# Battle Heroes Defense

## Overview
Battle Heroes Defense is a 2D side-scrolling tower defense game inspired by *Line Rangers*. Players deploy unique hero units with different stats and skills to defend their base while attacking the enemy's. The game integrates real-time strategy, cooldown and energy systems, AI-controlled enemies, and gameplay analytics.

## Game Concept
- Deploy Archer, Warrior, Mage, and Healer units.
- Each hero has unique attributes, attack cooldowns, and skill effects.
- Use energy (minerals) to summon units, which regenerates over time.
- Each hero summon button has an individual cooldown.
- AI-controlled enemies spawn and move toward the player base.
- Use tactics and timing to defeat the enemy base before losing your own.
- **Advance Stages** – After each victory, the player can proceed to the next stage where enemies become stronger (increased health), adding difficulty over time.

## How to Run
1. **Clone this repository**
```bash
git clone https://github.com/Lemonef/heros-go-.git
cd heros-go-
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the game**
```bash
python "heros go!.py"
```

> On Linux, if you encounter a `tkinter` error:
```bash
sudo apt-get install python3-tk
```

## UML Diagram
```html
## UML Diagram
<img src="https://raw.githubusercontent.com/Lemonef/heros-go-/main/screenshots/UML.png" alt="UML Diagram" />
<a href="https://lucid.app/lucidchart/6a48afa7-1e3b-480f-ab15-1587b6981417/edit?viewport_loc=-2857%2C-2489%2C7516%2C3896%2C0_0&invitationId=inv_f42b5e9f-a717-4fcb-be57-2f106346f147">UML diagram link</a>
```

## Object-Oriented Design
| Class | Description |
|-------|-------------|
| `GameManager` | Controls main loop, updates game state, manages win/loss |
| `Character` | Base class for `Hero` and `Enemy` |
| `Hero` | Subclass with skill logic, animation, attack logic |
| `Enemy` | Subclass with movement, attack behavior |
| `Skill` | Encapsulates ability logic, effects, cooldown |
| `SkillEffect` | Parent class for skills like `GroupHealEffect`, `AreaDamageEffect`, etc. |
| `Base` | Handles health and damage for each side |
| `ResourceManager` | Manages energy regeneration and upgrade system |
| `Tracker` | Records gameplay stats to CSV |
| `HeroButton`, `UpgradeButton` | GUI components with cooldown/cost logic |
| `AnimationManager` | Loads and updates frame animations |

## Algorithms
- Hero/Enemy movement
- Cooldown and timestamp management
- Skill casting and projectile simulation
- Data snapshotting every 5 seconds
- Energy regeneration and upgrade scaling

## Data Analytics Component
- `game_data.csv` logs ability usage, enemies defeated, heroes defeated, etc.
- `StatsVisualizer` GUI shows data as:
  - Line charts (Energy usage)
  - Bar charts (Enemies vs Heroes defeated)
  - Strip plots (Most spawned hero)
  - Rolling averages (Skill usage trends)

## Data Table Summary
| Feature | Purpose | Source | Display Method |
|---------|---------|--------|----------------|
| Ability Usage | Balancing + feedback | Tracker | Line + Pie Charts |
| Energy Used | Resource management | ResourceManager | Line Chart |
| Enemies Defeated | Performance metric | Tracker | Bar Chart |
| Heroes Defeated | Difficulty gauge | Tracker | Bar Chart |
| Most Spawned Hero | Player preference | Tracker | Strip Plot |

## YouTube Video
```html
<a href="https://www.youtube.com/watch?v=your-video-id">Watch 5-min Presentation</a>
```

## Author
Sudha Sutaschuto (6710545920)

## License
MIT — see `LICENSE`
