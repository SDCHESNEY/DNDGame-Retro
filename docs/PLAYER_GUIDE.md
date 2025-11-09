# Player's Guide - LLM Dungeon Master

Welcome to the LLM Dungeon Master! This guide will help you get started playing.

## Quick Start

### Starting a Game

```bash
# Launch the game
rpg play

# Or with a specific color scheme
rpg play --color-scheme green    # Green phosphor monitor
rpg play --color-scheme amber    # Amber monitor
rpg play --color-scheme cga      # IBM CGA colors
rpg play --color-scheme c64      # Commodore 64
rpg play --color-scheme apple    # Apple II
```

### Creating a Character

```bash
# List available classes
rpg character-classes

# Create a character from a template
rpg create-character <session-id> "Character Name" <race> <class> \
  --strength 15 --dexterity 14 --constitution 13 \
  --intelligence 12 --wisdom 10 --charisma 8

# Example: Create a Dwarf Fighter
rpg create-character 1 "Thorin Ironforge" Dwarf Fighter \
  --strength 16 --dexterity 12 --constitution 15 \
  --intelligence 10 --wisdom 12 --charisma 8

# View your character
rpg show-character 1
```

## Basic Commands

### Navigation and Exploration

```bash
north (n)      # Move north
south (s)      # Move south
east (e)       # Move east
west (w)       # Move west
up (u)         # Move up
down (d)       # Move down

look           # Look around
look at <item> # Examine something
search         # Search the area
```

### Combat

```bash
attack <target>              # Attack an enemy
cast <spell> on <target>     # Cast a spell
use <item>                   # Use an item
defend                       # Take defensive stance

# Examples
attack goblin
cast fireball on orc
use health potion
```

### Character Actions

```bash
inventory (i)  # View inventory
stats          # View character stats
skills         # View skills and abilities
spells         # View available spells
rest           # Take a short or long rest
```

### Social Interactions

```bash
talk to <npc>        # Start conversation
ask <npc> about <topic>
give <item> to <npc>
trade with <npc>
```

### Utility

```bash
help (?)       # Show help
quit           # Exit game
save           # Save game
load           # Load game
```

## Command Aliases

### Default Aliases

```bash
r20    -> roll 1d20           # Standard d20 roll
adv    -> roll 1d20 advantage # Roll with advantage
disadv -> roll 1d20 disadvantage
atk    -> attack-roll         # Attack roll
i      -> inventory          # Quick inventory
n/s/e/w -> north/south/east/west
```

### Creating Custom Aliases

```bash
# Add an alias
rpg alias-add "fs" "cast-spell fireball --level 3"

# Use it
fs

# List all aliases
rpg alias-list

# Remove an alias
rpg alias-remove "fs"
```

## Dice Rolling

```bash
# Roll dice
rpg roll 1d20         # Roll 1d20
rpg roll 2d6+5        # Roll 2d6 and add 5
rpg roll 4d6          # Roll 4d6

# With advantage/disadvantage
rpg roll 1d20 --advantage
rpg roll 1d20 --disadvantage

# Attack roll
rpg attack-roll 1d20+5 --ac 15

# Saving throw
rpg save-throw WIS --dc 14
```

## Tips for Players

### 1. Use Tab Completion

Many terminals support tab completion. Type part of a command and press Tab.

### 2. Read the DM's Descriptions

The DM provides rich descriptions. Read them carefully for clues.

### 3. Be Creative

Try unconventional solutions! The LLM DM can adapt to creative actions.

### 4. Communicate

If playing multiplayer, coordinate with your party.

### 5. Save Often

Use the save command before risky actions.

### 6. Use Aliases

Set up aliases for frequently-used commands to save time.

## Character Progression

### Gaining Experience

- Defeat enemies
- Complete quests
- Clever solutions
- Good roleplay

### Leveling Up

```bash
# Check experience
rpg show-character <id>

# Level up when ready
rpg level-up <character-id>
```

### Equipment

```bash
# View inventory
rpg inventory

# Equip items
rpg equip <item>

# Unequip
rpg unequip <slot>
```

## Multiplayer

### Joining a Session

```bash
# Create a player
rpg create-player "Your Name"

# Join a session
rpg join-session <session-id> <player-id>
```

### Turn-Based Play

- Wait for your turn in combat
- The DM will indicate whose turn it is
- Plan your actions while others play

### Communication

- Use the in-game chat
- Coordinate strategies
- Share resources

## Getting Help

### In-Game Help

```bash
help           # General help
help commands  # List all commands
help <command> # Help for specific command
```

### Common Issues

**Can't connect to server**:
```bash
# Check if server is running
curl http://localhost:8000/health

# Start server if needed
rpg serve
```

**Character creation fails**:
- Check point-buy totals (must equal 27)
- Ensure all required fields provided
- Valid race and class names

**Commands not working**:
- Check spelling
- Use `help <command>` for syntax
- Try the full command (not alias)

## Advanced Features

### Session Management

```bash
# Save current session
rpg session-save <session-id> --note "Before boss fight"

# Load a previous save
rpg session-load <path-to-save>

# List available saves
rpg session-saves <session-id>
```

### History and Search

```bash
# Search message history
rpg history-search <session-id> "dragon"

# Export session history
rpg history-export <session-id> recap.md --format markdown
```

### Statistics

```bash
# View your stats
rpg stats-show --session-id <session-id>

# View leaderboard
rpg stats-leaderboard <session-id> --metric crits
```

## Content Generation

As a player, you can suggest content to the DM:

```bash
# Generate an NPC
rpg gen-npc --role merchant --race dwarf

# Generate loot for treasure
rpg gen-loot 5 --hoard

# Generate a location
rpg gen-dungeon --theme crypt --rooms 8
```

## Roleplay Tips

### 1. Stay In Character

Speak and act as your character would.

### 2. Describe Your Actions

"I carefully examine the ancient door for traps before touching it."

### 3. Interact with NPCs

Ask questions, build relationships, gather information.

### 4. Make Choices

The DM presents options - choose based on your character's personality.

### 5. Embrace Failure

Failed rolls can lead to interesting stories!

## Example Session

```bash
# 1. Start the game
rpg play

# 2. Create or select character
# (Follow on-screen prompts)

# 3. Listen to DM's introduction
# The DM describes the starting scene

# 4. Take action
look around
talk to innkeeper

# 5. Explore
north
search

# 6. Combat!
attack goblin
cast healing word on ally

# 7. Loot and progress
take treasure
rest

# 8. Save progress
save
```

## Keybindings

| Key | Action |
|-----|--------|
| Enter | Submit command |
| ↑ / ↓ | Command history |
| Ctrl+C | Cancel/Interrupt |
| Ctrl+D | Quit game |
| Tab | Auto-complete (if supported) |

## Color Schemes

### Green Phosphor (`--color-scheme green`)
Classic terminal feel with green text on black background.

### Amber Monitor (`--color-scheme amber`)
Warm amber glow like old computer monitors.

### CGA Colors (`--color-scheme cga`)
IBM CGA palette - cyan, magenta, white on black.

### Commodore 64 (`--color-scheme c64`)
Retro blue and light blue like the C64.

### Apple II (`--color-scheme apple`)
Green on black like the Apple II.

## Troubleshooting

### Game Won't Start

```bash
# Check Python version
python --version  # Should be 3.12+

# Reinstall
uv pip install -e .

# Check server
rpg serve
```

### Performance Issues

- Close other applications
- Reduce session history (it accumulates)
- Restart the server

### API Errors

- Check your OpenAI API key in `.env`
- Verify you have API credits
- Check internet connection

## Next Steps

- [DM's Guide](./DM_GUIDE.md) - Learn to run games
- [Commands Reference](./COMMANDS.md) - Full command list
- [Docker Guide](./DOCKER.md) - Deployment options

---

**Have fun adventuring!** 🎲⚔️🐉
