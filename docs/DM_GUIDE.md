# Dungeon Master's Guide - LLM Dungeon Master

Guide for running game sessions as a Dungeon Master.

## Quick Start

### Setting Up a Session

```bash
# 1. Start the server
rpg serve

# 2. Create a session
rpg create-session "Epic Quest" "DM Name"

# 3. Invite players to create characters
# Players create characters for the session

# 4. Start the adventure
rpg play
```

## DM Tools

### Content Generation

#### Encounters

```bash
# Generate balanced encounter
rpg gen-encounter 5,5,6,7 --difficulty hard --environment dungeon

# Difficulty levels: easy, medium, hard, deadly
# Environments: dungeon, forest, mountain, urban, desert, underdark, planar, aquatic
```

#### NPCs

```bash
# Generate NPC
rpg gen-npc --role merchant --race dwarf

# Roles: merchant, guard, noble, commoner, sage, priest, thief, innkeeper, blacksmith, farmer
# Races: Human, Elf, Dwarf, Halfling, Gnome, Half-Orc
```

#### Locations

```bash
# Generate dungeon
rpg gen-dungeon --theme crypt --rooms 12

# Themes: temple, crypt, mine, fortress, laboratory, natural_cave

# Generate settlement
rpg gen-settlement --size town

# Sizes: village, town, city

# Generate wilderness
rpg gen-wilderness --terrain forest

# Terrains: forest, mountains, plains
```

#### Treasure

```bash
# Generate loot
rpg gen-loot 8 --hoard

# Treasure types: individual, hoard
# Challenge rating determines rarity
```

### Session Management

```bash
# Save session state
rpg session-save <session-id> --note "End of session 5"

# Load previous state
rpg session-load <save-file>

# List all saves
rpg session-saves <session-id>
```

### History and Recap

```bash
# Search for specific events
rpg history-search <session-id> "dragon attack"

# Export session recap
rpg history-export <session-id> session5_recap.md --format markdown

# Export formats: text, json, markdown
```

### Statistics and Analytics

```bash
# View session statistics
rpg stats-show --session-id <session-id>

# Player leaderboards
rpg stats-leaderboard <session-id> --metric crits
rpg stats-leaderboard <session-id> --metric damage
rpg stats-leaderboard <session-id> --metric nat20s

# Player activity
rpg history-show <session-id> --sender "Player Name"
```

## Running Combats

### Starting Combat

```bash
# 1. Generate or describe encounter
rpg gen-encounter <party-levels> --difficulty <difficulty>

# 2. Roll initiative for all
# The system handles this automatically

# 3. Track turn order
# System manages turns automatically
```

### Combat Flow

1. **Initiative**: Automatic roll and ordering
2. **Player Turns**: Players declare actions
3. **DM Narration**: Describe results
4. **Monster Turns**: DM controls monsters
5. **Conditions**: System tracks automatically
6. **HP Management**: Automatic tracking

### Combat Commands

```bash
# Attack rolls
rpg attack-roll 1d20+5 --ac 15

# Damage rolls
rpg roll 2d6+3

# Apply damage
# (Handled through API/WebSocket)

# Apply conditions
# System handles via API
```

## Balancing Encounters

### CR Calculation

The system uses D&D 5e rules for encounter balancing:

```python
# Party of level 5 characters (4 players)
Easy: CR 2-3
Medium: CR 4-5
Hard: CR 6-7
Deadly: CR 8+
```

### Adjusting Difficulty

- **Too Easy**: Add more enemies or increase CR
- **Too Hard**: Reduce enemy HP or give players advantages
- **Pacing**: Mix combat with exploration and roleplay

## Managing NPCs

### Personalities

Generated NPCs include:
- Physical description
- Personality traits
- Goals and motivations
- Secrets
- Stat blocks

### Using NPCs

```bash
# Generate NPC
rpg gen-npc --role sage --race elf

# Track important NPCs in session notes
# Use DM screen to reference quickly
```

## World Building

### Locations

```bash
# Create a dungeon
rpg gen-dungeon --theme temple --rooms 15

# The system generates:
- Room descriptions
- Connections
- Features
- Encounters
- Treasure
```

### Settlements

```bash
# Generate town
rpg gen-settlement --size town

# Includes:
- Population
- Notable locations
- Local government
- Economy
- Threats
```

## Campaign Management

### Session Planning

1. **Review Last Session**:
```bash
rpg history-export <session-id> last_session.md
```

2. **Prepare Content**:
```bash
rpg gen-encounter ...
rpg gen-npc ...
rpg gen-dungeon ...
```

3. **Save Preparation**:
- Keep notes in markdown
- Use session-save before starting

4. **Run Session**:
- Use generated content
- Improvise with LLM DM
- Track important events

5. **Wrap Up**:
```bash
rpg session-save <session-id> --note "Session 6 complete"
```

### Long-Term Tracking

- Export session histories regularly
- Keep campaign notes separately
- Track player choices and consequences

## DM Best Practices

### 1. Prepare but Stay Flexible

- Generate content ahead of time
- But let players surprise you
- LLM DM can improvise

### 2. Balance Content Types

- Combat: 30-40%
- Exploration: 30-40%
- Social: 20-30%

### 3. Player Engagement

- Give each player spotlight time
- Use their backstories
- Create personal quests

### 4. Pacing

- Vary intensity
- Short breaks between combat
- End on cliffhangers

### 5. Use the Tools

- Content generators save time
- Statistics show player engagement
- History helps continuity

## Common DM Scenarios

### Players Get Stuck

```bash
# Generate helpful NPC
rpg gen-npc --role sage

# Provide subtle hints through DM
# Let LLM suggest alternatives
```

### Combat Takes Too Long

- Set turn timers
- Encourage quick decisions
- Narrate quickly between turns

### Players Go Off-Script

- Let them! 
- Use content generators on the fly
- LLM DM adapts well

### Technical Issues

```bash
# Check server health
curl http://localhost:8000/health

# Restart if needed
docker-compose restart api

# Restore from backup if necessary
./scripts/docker/restore.sh <backup>
```

## Advanced DM Techniques

### Layered Adventures

1. Main quest line
2. Side quests
3. Character arcs
4. World events

### Dynamic Difficulty

Monitor player success rate:
```bash
rpg stats-show --session-id <id>
```

Adjust encounters based on performance.

### Narrative Hooks

- Generate mysterious NPCs
- Create location-based mysteries
- Link encounters to larger plot

## Multiplayer DMing

### Turn Management

- System handles turn order
- Encourage players to prepare
- Keep things moving

### Player Coordination

- Foster teamwork
- Reward creative combinations
- Allow tactical discussions

### Session Zero

Before campaign:
1. Set expectations
2. Character creation together
3. Establish world facts
4. Safety tools (X-card, lines/veils)

## DM Screen Reference

### Common DCs

| Task Difficulty | DC |
|----------------|-----|
| Very Easy | 5 |
| Easy | 10 |
| Medium | 15 |
| Hard | 20 |
| Very Hard | 25 |
| Nearly Impossible | 30 |

### Damage by Level

| Level | Easy | Medium | Hard |
|-------|------|--------|------|
| 1-4 | 1d4 | 1d6 | 1d8 |
| 5-10 | 2d6 | 2d8 | 2d10 |
| 11-16 | 4d6 | 4d8 | 4d10 |
| 17-20 | 6d6 | 6d8 | 6d10 |

### Typical DCs

- Unlock common lock: DC 10
- Climb rough surface: DC 10
- Swim in rough water: DC 15
- Climb smooth surface: DC 20
- Swim in stormy water: DC 20

## Troubleshooting

### Session Issues

**Players can't connect**:
- Check server is running
- Verify ports are open
- Check firewall settings

**Lag or slowness**:
- Check server resources
- Reduce concurrent requests
- Consider upgrading hosting

**LLM responses slow**:
- Check OpenAI API status
- Verify API key valid
- Try different model

### Content Issues

**Generated content not fitting**:
- Regenerate with different params
- Modify generated content
- Mix generated with custom

**Balance issues**:
- Monitor combat statistics
- Adjust CR on the fly
- Use player feedback

## Next Steps

- [Player's Guide](./PLAYER_GUIDE.md) - Share with players
- [Commands Reference](./COMMANDS.md) - Full command list
- [Deployment Guide](./DEPLOYMENT.md) - Advanced setup

---

**Happy Dungeon Mastering!** 🎲🐉📖
