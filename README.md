# 🎲 LLM Dungeon Master - Retro Edition

A retro terminal-based D&D 5e game with an AI-powered Dungeon Master. Experience classic text-based RPG gameplay with modern AI narration, complete D&D 5e rules, and authentic vintage terminal aesthetics.

![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)
![Tests](https://img.shields.io/badge/tests-258%20passing-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ✨ Features

### 🎮 Retro CLI Interface
- **5 Authentic Color Schemes**: Green Phosphor, Amber Monitor, IBM CGA, Commodore 64, Apple II
- **ASCII Art**: Title screens, character sheets, combat displays with vintage graphics
- **Animations**: Dice rolling, combat effects, spell casting with frame-by-frame rendering
- **Natural Language Commands**: "attack goblin", "cast fireball on orc", "go north"
- **Interactive Menus**: Keyboard-driven navigation with rich formatting

### ⚔️ Complete D&D 5e Rules Engine
- **Dice Rolling**: Full notation support (XdY+Z), advantage/disadvantage, critical hits
- **Combat System**: Initiative tracking, turn order, attacks, damage, healing, death saves
- **15 Conditions**: All D&D 5e conditions with accurate effects (Blinded, Poisoned, Stunned, etc.)
- **Provably Random**: Cryptographically secure dice rolls using Python's `secrets` module

### 🎭 Character System
- **10 Core Classes**: Fighter, Wizard, Rogue, Cleric, Ranger, Paladin, Barbarian, Bard, Sorcerer, Warlock
- **Point-Buy Generation**: 27 points, 8-15 range, automatic stat calculation
- **Character Validation**: Ensures D&D 5e compliance
- **Level-Up System**: HP advancement, proficiency bonus, class features
- **Full Character Sheets**: Color-coded stats, equipment, features, spells

### 🌐 Real-Time Multiplayer
- **WebSocket Support**: Real-time game sessions with live updates
- **REST API**: 30+ endpoints for complete game management
- **Session Management**: Multiple concurrent games, player tracking
- **Event Broadcasting**: Dice rolls, combat actions, condition changes

## 📦 Installation

### Prerequisites
- Python 3.12 or higher
- pip (Python package manager)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/SDCHESNEY/DNDGame-Retro.git
cd DNDGame-Retro

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Initialize database
rpg init

# Start playing!
rpg play
```

## 🎯 Usage

### Interactive Play Mode

Launch the retro terminal interface:

```bash
# Start with green phosphor (classic terminal)
rpg play

# Choose your color scheme
rpg play --color-scheme amber   # Warm vintage amber
rpg play --color-scheme cga     # IBM CGA colors
rpg play --color-scheme c64     # Commodore 64
rpg play --color-scheme apple   # Apple II green
```

Navigate through menus:
- **[P]lay** - Start or continue a game session
- **[C]haracters** - View and manage characters
- **[S]essions** - Browse game sessions
- **[T]heme** - Switch color schemes
- **[Q]uit** - Exit the game

### Character Management

```bash
# List available classes
rpg character-classes

# Create a character
rpg create-character 1 "Thorin Ironforge" Dwarf Fighter \
  --strength 15 --dexterity 13 --constitution 14 \
  --intelligence 10 --wisdom 12 --charisma 8 \
  --background "Folk Hero"

# View character sheet
rpg show-character 1

# List all characters
rpg list-characters

# Validate character
rpg validate-character 1
```

### Session Management

```bash
# Create a new game session
rpg create-session "Epic Campaign"

# List all sessions
rpg list-sessions

# Create players
rpg create-player "Alice"
rpg create-player "Bob"

# List players
rpg list-players
```

### API Server

Start the FastAPI server for programmatic access or web frontend:

```bash
# Start server
rpg serve --port 8000

# With auto-reload for development
rpg serve --port 8000 --reload

# API documentation available at:
# http://localhost:8000/docs
```

## 🎨 Color Schemes

Choose from 5 authentic retro terminal color schemes:

| Scheme | Description | Primary Color | Style |
|--------|-------------|---------------|-------|
| **Green Phosphor** | Classic monochrome terminal | `#00ff00` | Vintage mainframe |
| **Amber Monitor** | Warm CRT monitor | `#ffaa00` | 1980s business terminal |
| **IBM CGA** | Bold 4-color palette | Blue/Cyan/Magenta | Early PC gaming |
| **Commodore 64** | Iconic home computer | Purple/Blue | 1980s home computing |
| **Apple II** | Classic Apple green | `#33ff33` | Educational computing |

## 🎮 Natural Language Commands

The command parser understands natural language:

```bash
# Combat
"attack goblin"
"hit the orc with my sword"
"strike dragon"

# Spells
"cast fireball"
"cast shield on myself"
"use magic missile on the enemy"

# Movement
"north"
"go south"
"move east"
"walk west"

# Interaction
"look around"
"examine the chest"
"talk to the guard"
"speak with merchant"

# Items
"use healing potion"
"drink elixir"

# System
"inventory" or "i"
"rest"
"help" or "?"
"quit" or "q"
```

## 🏗️ Architecture

### Project Structure

```
DNDGame-Retro/
├── src/llm_dungeon_master/
│   ├── cli.py                    # Typer CLI interface
│   ├── server.py                 # FastAPI + WebSocket server
│   ├── models.py                 # SQLModel database models
│   ├── config.py                 # Configuration management
│   ├── character_builder.py     # Character creation system
│   ├── cli_ui/                   # Retro terminal interface
│   │   ├── colors.py             # Color schemes
│   │   ├── display.py            # ASCII art and formatting
│   │   ├── screens.py            # UI screens
│   │   ├── animations.py         # Dice and combat animations
│   │   └── commands.py           # Command parser
│   ├── rules/                    # D&D 5e rules engine
│   │   ├── dice.py               # Dice rolling system
│   │   ├── combat.py             # Combat mechanics
│   │   └── conditions.py         # Status conditions
│   └── templates/                # Character class templates
│       ├── fighter.json
│       ├── wizard.json
│       └── ... (8 more classes)
├── test/                         # 258 comprehensive tests
├── data/                         # SQLite database
├── docs/                         # Documentation
└── pyproject.toml               # Project configuration
```

### Technology Stack

- **Python 3.12+**: Core language
- **FastAPI**: REST API and WebSocket server
- **SQLModel**: Database ORM (SQLAlchemy + Pydantic)
- **Typer**: CLI framework with rich formatting
- **Rich**: Terminal styling and formatting
- **Pydantic**: Data validation
- **pytest**: Testing framework (258 tests)

## 📊 API Overview

### REST Endpoints (30+)

**Sessions:**
- `POST /api/sessions` - Create session
- `GET /api/sessions` - List sessions
- `GET /api/sessions/{id}` - Get session details

**Characters:**
- `GET /api/characters/classes` - List available classes
- `POST /api/characters/from-template` - Create from template
- `GET /api/characters` - List characters
- `GET /api/characters/{id}` - Get character
- `GET /api/characters/{id}/summary` - Formatted summary
- `PUT /api/characters/{id}` - Update character
- `DELETE /api/characters/{id}` - Delete character
- `POST /api/characters/{id}/level-up` - Advance level

**Dice Rolling:**
- `POST /api/dice/roll` - Roll dice
- `POST /api/dice/check` - Ability check
- `POST /api/dice/attack` - Attack roll
- `POST /api/dice/damage` - Damage roll

**Combat:**
- `POST /api/combat/start` - Start combat
- `POST /api/combat/{id}/next-turn` - Advance turn
- `POST /api/combat/{id}/attack` - Execute attack
- `POST /api/combat/{id}/damage` - Apply damage
- `POST /api/combat/{id}/heal` - Apply healing

**Conditions:**
- `POST /api/conditions/apply` - Apply condition
- `GET /api/conditions/{character_id}` - Get conditions
- `DELETE /api/conditions/{id}` - Remove condition

### WebSocket
- `/ws/{session_id}` - Real-time game events

Full API documentation: `http://localhost:8000/docs` (when server is running)

## 🧪 Testing

The project has comprehensive test coverage with 258 passing tests:

```bash
# Run all tests
pytest

# Run specific test file
pytest test/test_cli_ui.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src/llm_dungeon_master
```

### Test Breakdown
- **Phase 1-2**: 66 tests (Database, Models, Sessions, API, WebSocket)
- **Phase 3**: 79 tests (Dice, Combat, Conditions)
- **Phase 4**: 40 tests (Character Builder, Templates)
- **Phase 5**: 18 tests (CLI UI, Commands, Animations)

**Total: 258 passing tests** ✅

## 🗺️ Roadmap

### ✅ Completed Phases

- **Phase 1**: Foundation (Database, Models, Basic API)
- **Phase 2**: Core Features (Sessions, Players, WebSocket)
- **Phase 3**: D&D 5e Rules Engine (Dice, Combat, Conditions)
- **Phase 4**: Character System (10 Classes, Point-Buy, Templates)
- **Phase 5**: Retro CLI Interface (5 Color Schemes, ASCII Art, Animations)

### 🚧 Future Phases

**Phase 6: AI Dungeon Master**
- OpenAI GPT integration
- Dynamic story generation
- NPC dialogue and personalities
- Combat narration
- World-building and lore

**Phase 7: Advanced Features**
- Spell system with full SRD spells
- Magic items and treasure
- Character progression (levels 1-20)
- Multiclassing support
- Custom campaigns

**Phase 8: Multiplayer Enhancements**
- Party management
- Shared inventory
- Turn-based multiplayer combat
- Voice chat integration
- Spectator mode

## 📖 Documentation

Comprehensive documentation available in the `docs/` directory:

- **[ROADMAP.md](docs/ROADMAP.md)** - Project roadmap and status
- **[PHASE3_SUMMARY.md](docs/PHASE3_SUMMARY.md)** - Rules engine implementation
- **[PHASE4_SUMMARY.md](docs/PHASE4_SUMMARY.md)** - Character system details
- **[PHASE5_SUMMARY.md](docs/PHASE5_SUMMARY.md)** - CLI interface documentation
- **[PHASE3_COMPLETE.md](docs/PHASE3_COMPLETE.md)** - Phase 3 completion report
- **[PHASE4_COMPLETE.md](docs/PHASE4_COMPLETE.md)** - Phase 4 completion report
- **[PHASE5_COMPLETE.md](docs/PHASE5_COMPLETE.md)** - Phase 5 completion report

## 🎯 Example Session

```bash
# Initialize and create your first character
$ rpg init
✓ Database initialized successfully!

$ rpg create-player "Alice"
✓ Player 'Alice' created with ID: 1

$ rpg create-character 1 "Elara Moonwhisper" Elf Wizard \
  --strength 8 --dexterity 14 --constitution 12 \
  --intelligence 15 --wisdom 13 --charisma 10

Character created successfully!

Elara Moonwhisper
Level 1 Elf Wizard

Ability Scores:
STR: 8 (-1) | DEX: 14 (+2) | CON: 12 (+1)
INT: 15 (+2) | WIS: 13 (+1) | CHA: 10 (+0)

Combat Stats:
HP: 7/7 | AC: 12 | Initiative: +2 | Proficiency: +2

# Start the game
$ rpg play

[ASCII title screen with dragon art appears]

╔═══════════════════════════════════════════════════╗
║   🎲 Welcome to LLM Dungeon Master! 🎲          ║
║                                                   ║
║   [P]lay    - Start adventure                    ║
║   [C]haracters - View your heroes                ║
║   [S]essions - Browse campaigns                  ║
║   [T]heme - Change colors                        ║
║   [Q]uit - Exit                                  ║
╚═══════════════════════════════════════════════════╝

Select an option: c

[Character sheet displays with color-coded stats]
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ test/

# Lint code
ruff check src/ test/
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **D&D 5e SRD**: Rules and mechanics from Wizards of the Coast
- **Rich Library**: Amazing terminal formatting by Will McGugan
- **FastAPI**: Modern, fast web framework by Sebastián Ramírez
- **Retro Computing**: Inspired by classic terminals and early RPGs

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/SDCHESNEY/DNDGame-Retro/issues)
- **Documentation**: See `docs/` directory
- **API Docs**: `http://localhost:8000/docs` (when server running)

## 🎲 Quick Command Reference

```bash
# Game Management
rpg init                    # Initialize database
rpg play                    # Start interactive mode
rpg serve                   # Start API server

# Characters
rpg character-classes       # List available classes
rpg create-character        # Create new character
rpg list-characters         # List all characters
rpg show-character <id>     # View character sheet
rpg validate-character <id> # Validate character

# Sessions
rpg create-session <name>   # Create new session
rpg list-sessions           # List all sessions

# Players
rpg create-player <name>    # Create new player
rpg list-players            # List all players

# System
rpg version                 # Show version
rpg --help                  # Show help
```

---

**Built with ❤️ by passionate D&D and retro computing enthusiasts**

*May your dice roll true and your adventures be legendary!* 🎲✨
