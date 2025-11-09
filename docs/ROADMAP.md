# Development Roadmap

## Phase 1: Core MVP (Week 1-2) ✅ COMPLETE

### Infrastructure ✅
- [x] Project setup with UV and Python 3.12
- [x] FastAPI server with REST + WebSocket
- [x] SQLModel database models
- [x] Typer CLI interface
- [x] Configuration management
- [x] LLM provider abstraction
- [x] DM prompt templates

## Phase 2: LLM Integration (Week 3) ✅ COMPLETE

### Server-Side DM 🎯
- [x] Connect WebSocket messages to LLM provider
- [x] Stream DM responses to clients
- [x] Implement conversation history management
- [x] Add retry logic with exponential backoff
- [x] Rate limiting per session
- [x] Token usage tracking and limits
- [x] Error handling for API failures

### Files Created/Modified:
```python
# ✅ src/llm_dungeon_master/dm_service.py
class DMService:
    async def process_player_action(db, session_id, player_name, action) -> str
    async def start_session(db, session_id) -> str
    async def handle_roll(db, session_id, player_name, roll_type, result, dice, modifier) -> str
    async def generate_stream(db, session_id, player_name, action) -> AsyncIterator[str]
    def get_token_usage(session_id) -> dict
    # Rate limiting, token tracking, retry logic with exponential backoff

# ✅ Modified: server.py
# - WebSocket handler integrated with DMService
# - Streaming responses to clients
# - Error handling for rate limits and token limits
# - New API endpoints: /api/sessions/{id}/start, /api/sessions/{id}/action, /api/sessions/{id}/tokens

# ✅ test/test_dm_service.py - 20 comprehensive tests
```

### Acceptance Criteria: ✅ ALL MET
- ✅ Player sends message → DM responds within 5 seconds
- ✅ DM maintains context from previous messages (20 message history)
- ✅ Graceful degradation if LLM API fails (retry logic with exponential backoff)
- ✅ Cost tracking with token usage statistics
- ✅ Rate limiting (20 requests/min per session, configurable)
- ✅ Token limits (100k tokens per session, configurable)
- ✅ Streaming responses supported
- ✅ All 66 tests passing (20 new DM service tests + 4 new API tests)

## Phase 3: Rules Engine (Week 4) 🚧

### Dice & Checks 🎲
- [ ] Server-side dice roller with cryptographic RNG
- [ ] Ability check resolution (Strength, Dex, etc.)
- [ ] Saving throw system
- [ ] Attack rolls vs AC
- [ ] Damage calculation
- [ ] Advantage/disadvantage handling

### Combat System ⚔️
- [ ] Initiative tracking
- [ ] Turn order management
- [ ] Action economy (action, bonus action, reaction)
- [ ] Condition application and tracking
- [ ] HP management and death saves

### Files to Create:
```python
# src/llm_dungeon_master/rules/dice.py
def roll_dice(formula: str, advantage: AdvantageType = NORMAL) -> RollResult
def resolve_check(ability_score, dc, proficiency_bonus) -> CheckResult
def resolve_attack(attack_bonus, target_ac, advantage) -> CheckResult
def roll_damage(damage_formula, critical) -> RollResult

# src/llm_dungeon_master/rules/combat.py
class CombatManager:
    def start_combat(session_id, characters) -> CombatState
    def next_turn(session_id) -> CombatState
    def resolve_attack(session_id, attacker_id, target_id) -> AttackResult
    def apply_damage(session_id, character_id, damage) -> bool

# src/llm_dungeon_master/rules/conditions.py
class ConditionManager:
    def apply_condition(character_id, condition_type, duration) -> bool
    def get_conditions(character_id) -> List[Condition]
    def advance_round(character_id) -> List[ConditionType]
    def check_condition_effects(character_id) -> Dict[str, any]

# Enhanced: server.py
# - Add 8+ new API endpoints for dice rolling, combat, conditions
# - WebSocket integration for real-time dice events
# - Database persistence for all game state

# Enhanced: models.py
# - Add Roll, CombatEncounter, CharacterCondition models
# - JSON serialization for complex game state
```

### Acceptance Criteria:
- [ ] Dice rolls are provably random and logged
- [ ] Combat encounters work end-to-end
- [ ] Conditions affect gameplay correctly
- [ ] DM can reference rules in responses
- [ ] WebSocket integration for real-time events
- [ ] REST API endpoints for all features
- [ ] Database persistence for game state

## Phase 4: Character System (Week 5) 🚧

### Character Creation 🎭
- [ ] Character templates (10 D&D classes)
- [ ] Point-buy stat generation
- [ ] Background and skill selection
- [ ] Starting equipment by class
- [ ] Character validation

### Character Management 📋
- [ ] CLI character builder
- [ ] Character selection for sessions
- [ ] Character sheet display
- [ ] Inventory management
- [ ] Level up mechanics

### Files to Create:
```python
# src/llm_dungeon_master/character_builder.py
class CharacterBuilder:
    def create_from_template(template: str) -> Character
    def validate_character(character: Character) -> bool
    def apply_level_up(character: Character) -> Character

# src/llm_dungeon_master/templates/
# - fighter.json
# - wizard.json
# - rogue.json
# - cleric.json
# - ranger.json
# - paladin.json
# - barbarian.json
# - bard.json
# - sorcerer.json
# - warlock.json

# Enhanced: cli.py
# - Add: rpg character-create
# - Add: rpg character-list
# - Add: rpg character-show
# - Add: rpg character-classes
# - Add: rpg character-validate

# Enhanced: models.py
# - Extended Character model with experience points, death saves, spell slots
# - Add CharacterSpell, CharacterFeature, CharacterEquipment models
# - Add CharacterProgression, CharacterBackground models

# Enhanced: server.py
# - Add 7 character management API endpoints
# - Character CRUD operations
# - Level-up and validation endpoints
```

### Acceptance Criteria:
- [ ] Create character in under 2 minutes
- [ ] All SRD classes available
- [ ] Character stats follow D&D 5e rules
- [ ] Export/import as JSON

## Phase 5: Retro CLI Interface (Week 6-7) 🎮

### Terminal-Based UI 🎯
- [ ] ASCII art title screen and menus
- [ ] Text-based session management
- [ ] Command parser with natural language support
- [ ] Auto-complete for commands
- [ ] Color-coded output (ANSI colors)
- [ ] ASCII character sheet display
- [ ] Text-based combat display

### Classic Features 🕹️
- [ ] Text-based dice roller with ASCII animations
- [ ] Initiative tracker in terminal
- [ ] Party status display (ASCII table)
- [ ] Inventory screen with borders
- [ ] Map display with ASCII graphics
- [ ] Save/load game state

### Technology Choices:
- **Rich** library for styled terminal output
- **Prompt Toolkit** for interactive input
- **Click** or **Typer** for command parsing (already using Typer)
- **Colorama** for ANSI color support

### Files to Create:
```python
# src/llm_dungeon_master/cli_ui/
├── __init__.py
├── display.py          # ASCII art, tables, formatting
├── screens.py          # Title, character sheet, combat screens
├── commands.py         # Command parser and handlers
├── animations.py       # Dice rolls, combat effects
└── colors.py           # Color schemes and themes

# Enhanced: cli.py
# - Add interactive game mode
# - Add screen-based navigation
# - Add command history
# - Add ASCII art displays
```

### Acceptance Criteria:
- [ ] Launch game with ASCII title screen
- [ ] Navigate menus with arrow keys or commands
- [ ] View character sheet in formatted ASCII
- [ ] Combat displayed with text animations
- [ ] Feels like classic 80s text adventures

## Phase 6: Multiplayer Polish (Week 8) 🎮

### Turn Management 🎲
- [ ] Turn queue system with initiative ordering
- [ ] Turn status tracking (active, waiting, ready)
- [ ] Turn timers with configurable duration
- [ ] Ready checks before combat
- [ ] Turn advancement and history
- [ ] Real-time turn updates in terminal

### Presence & Synchronization 🔄
- [ ] Player presence tracking (online/away/offline)
- [ ] Connection status in CLI display
- [ ] Conflict detection and resolution
- [ ] Reconnection token system
- [ ] Session state synchronization
- [ ] Terminal refresh on state changes

### Files to Create/Modify:
```python
# src/llm_dungeon_master/turn_manager.py
class TurnManager:
    def start_turn_queue(session_id, player_characters) -> List[Turn]
    def get_current_turn(session_id) -> Turn
    def advance_turn(session_id) -> Turn
    def set_player_ready(session_id, player_id) -> bool

# src/llm_dungeon_master/presence_manager.py
class PresenceManager:
    def track_connection(session_id, player_id, connection_id) -> PlayerPresence
    def update_status(player_id, status) -> bool
    def get_presence_summary(session_id) -> Dict
    def check_all_ready(session_id) -> Dict

# src/llm_dungeon_master/sync_manager.py
class SyncManager:
    def detect_conflicts(session_id, actions) -> List[ConflictResolution]
    def resolve_conflict(conflict_id, strategy) -> bool
    def get_sync_stats(session_id) -> Dict

# src/llm_dungeon_master/reconnection_manager.py
class ReconnectionManager:
    def create_reconnection_token(player_id, session_id) -> str
    def handle_reconnection(token) -> Dict
    def restore_session_state(player_id, session_id) -> Dict

# Enhanced: models.py
# - Add Turn, PlayerPresence, TurnAction models
# - Add TurnStatus, PresenceStatus enums
# - Add multiplayer state tracking

# Enhanced: cli.py
# - Add turn-based command mode
# - Display current turn and initiative order
# - Show player presence indicators
# - Add turn advancement commands
# - Display sync conflicts in terminal
```

### Acceptance Criteria:
- [ ] 4+ players can play simultaneously via CLI
- [ ] Turn order displayed in terminal
- [ ] Player presence shown with ASCII indicators
- [ ] Reconnection works from terminal
- [ ] Conflict resolution displayed clearly
- [ ] Terminal updates in real-time
- [ ] Commands work during any player's turn

## Phase 7: Content & Polish (Week 9-10) 📚

### Content Generation 🎲
- [ ] Random encounter generator with CR balancing
- [ ] Comprehensive loot table system
- [ ] NPC generator with personalities
- [ ] Location/dungeon generator
- [ ] Settlement and wilderness generators
- [ ] Shop and treasure generation
- [ ] Encounter chains and dungeon levels

### Quality of Life ✨
- [ ] Session state management (save/load)
- [ ] Message history with scrollback
- [ ] Search chat history functionality
- [ ] Dice roll statistics tracking
- [ ] Achievement tracking system
- [ ] Player analytics in terminal
- [ ] Command aliases and shortcuts
- [ ] Macro system for common actions

### Admin Tools 🛠️
- [ ] CLI admin commands
- [ ] Session management from terminal
- [ ] Statistics display in terminal
- [ ] Error handling and logging

### Files to Create:
```python
# src/llm_dungeon_master/content/
# - __init__.py
# - encounters.py (Professional encounter generation)
# - loot.py (Complete treasure system)
# - npcs.py (Rich NPC generation)
# - locations.py (Detailed location generation)

# Enhanced: cli.py
# - Add content generation commands
# - Display encounters in ASCII format
# - Show loot tables in terminal
# - NPC stat blocks in text format
# - Location descriptions with formatting
# - Statistics dashboard command
# - Achievement display command
```

### Acceptance Criteria:
- [ ] Generate balanced encounters by party level
- [ ] Loot generation follows DMG guidelines
- [ ] NPCs have personality and background
- [ ] Locations have rich descriptions
- [ ] All content displayed beautifully in terminal
- [ ] Statistics displayed with ASCII charts
- [ ] Achievement notifications in terminal
- [ ] Content generation feels instantaneous

## Phase 8: Production Ready (Week 11-12) 🚀

### Deployment 📦
- [ ] Docker containerization (Dockerfile)
- [ ] Docker Compose for multi-service orchestration
- [ ] PostgreSQL service container (production database)
- [ ] Redis service container (caching and session management)
- [ ] FastAPI server container
- [ ] Volume management for data persistence
- [ ] Health checks for all services
- [ ] Environment-based configuration (.env)
- [ ] Development and production profiles
- [ ] Container networking setup
- [ ] Backup/restore scripts for Docker volumes

### Monitoring 📊
- [ ] Structured JSON logging with rotation
- [ ] Docker container logs aggregation
- [ ] Health check endpoints (/health, /ready, /live)
- [ ] Database connectivity monitoring
- [ ] Redis connection monitoring
- [ ] Container resource usage tracking
- [ ] LLM API usage and cost tracking
- [ ] Error reporting and alerting
- [ ] CLI command to view container logs

### Security 🔒
- [ ] Docker secrets management
- [ ] Non-root container users
- [ ] Network isolation between containers
- [ ] CORS middleware configuration
- [ ] Rate limiting (API and WebSocket)
- [ ] Input validation (Pydantic)
- [ ] SQL injection protection (SQLModel)
- [ ] Secure credential storage in environment variables
- [ ] SSL/TLS support (optional with reverse proxy)
- [ ] Container security scanning

### Documentation 📖
- [ ] Player's guide (CLI commands)
- [ ] DM's guide (running games)
- [ ] Installation guide
- [ ] Configuration reference
- [ ] Troubleshooting guide
- [ ] Quick start tutorial

### Files to Create:
```dockerfile
# Dockerfile
# - Multi-stage build with Python 3.12
# - UV package manager for fast installs
# - Non-root user for security
# - Health checks configured
# - Optimized layer caching
# - Development and production stages

# docker-compose.yml
# - FastAPI server service
# - PostgreSQL database service
# - Redis cache service
# - Volume definitions (db data, logs, uploads)
# - Network configuration
# - Environment variable injection
# - Development profile (hot reload)
# - Production profile (optimized)
# - Health check definitions

# .dockerignore
# - Exclude unnecessary files from build
# - Reduce image size
# - Speed up build times

# scripts/docker/
# - start-dev.sh (Start development containers)
# - start-prod.sh (Start production containers)
# - backup.sh (Backup Docker volumes)
# - restore.sh (Restore from backup)
# - logs.sh (View container logs)
# - shell.sh (Open shell in container)

# src/llm_dungeon_master/logging_config.py
# - Structured JSON logging (production)
# - Simple formatted logging (development)
# - Log rotation (10MB files, 5 backups)
# - Console and file handlers
# - Configurable log levels per environment

# Enhanced: config.py
# - Environment-based configuration
# - Docker-friendly defaults
# - Database URL parsing (PostgreSQL/SQLite)
# - Redis connection settings
# - CORS configuration
# - Rate limiting settings
# - Monitoring settings

# Enhanced: .env.example
# - Docker environment template
# - Database credentials
# - Redis configuration
# - LLM API keys
# - Server configuration
# - Logging settings
# - Security options

# Documentation/
# - DEPLOYMENT.md (Docker deployment guide)
# - DOCKER.md (Docker commands and troubleshooting)
# - PLAYER_GUIDE.md (how to play via CLI)
# - DM_GUIDE.md (how to run games)
# - COMMANDS.md (all CLI commands)
```

### Acceptance Criteria:
- [ ] Docker build succeeds for all services
- [ ] docker-compose up starts all containers
- [ ] Health checks pass for all services
- [ ] Database persists data across restarts
- [ ] Redis caching operational
- [ ] Logs are structured and rotated
- [ ] Container networking allows service communication
- [ ] Environment variables configure services
- [ ] Backup and restore scripts work
- [ ] Works on macOS, Linux, Windows (with Docker)
- [ ] Documentation complete with examples
- [ ] Development mode supports hot reload

### Deployment:

**Docker Deployment (Recommended):**
```bash
# Clone repository
git clone <repo>
cd DNDGame-Retro

# Configure environment
cp .env.example .env
# Edit .env with your settings (LLM API key, passwords, etc.)

# Development Mode (with hot reload)
docker-compose up -d

# Production Mode (optimized)
docker-compose --profile production up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Backup data
./scripts/docker/backup.sh

# Restore data
./scripts/docker/restore.sh backup-2025-11-08.tar.gz
```

**Services:**
- **FastAPI Server**: http://localhost:8000
- **PostgreSQL**: localhost:5432 (internal)
- **Redis**: localhost:6379 (internal)
- **Health Check**: http://localhost:8000/health

**Local Development (without Docker):**
```bash
# Clone and setup
git clone <repo>
cd DNDGame-Retro
uv venv
source .venv/bin/activate
uv pip install -e .

# Configure
cp .env.example .env
# Edit .env (can use SQLite instead of PostgreSQL)

# Run server
rpg serve

# In another terminal, play!
rpg play
```

## Beyond MVP (Future)

### Advanced Features 💡
- [ ] Voice mode (speech-to-text, text-to-speech)
- [ ] ASCII art image generation for scenes
- [ ] Custom homebrew content
- [ ] Campaign templates
- [ ] Terminal multiplayer over SSH
- [ ] MUD-style persistent world
- [ ] BBS-style bulletin board system

### Scalability 💡
- [ ] Horizontal scaling with Docker Swarm/Kubernetes
- [ ] Load balancing for multiple server instances
- [ ] Redis session store for multi-container deployments
- [ ] Database connection pooling
- [ ] Read replicas for PostgreSQL
- [ ] LLM response caching in Redis
- [ ] Background job processing with Celery
- [ ] CDN for static assets
- [ ] Database sharding for large deployments

## Testing Strategy

### Current 🚧
- [x] Smoke tests for imports
- [ ] Unit tests for models
- [ ] Unit tests for rules engine
- [ ] CLI command tests
- [ ] Integration tests

### Future 🔜
- [ ] CLI interaction tests
- [ ] Load testing
- [ ] LLM contract tests
- [ ] Terminal output tests

## Performance Targets

- ⚡ Command response: <50ms
- ⚡ DM response: <5s (depends on LLM)
- ⚡ Terminal refresh: <16ms (60 FPS)
- ⚡ Screen render: Instant
- ⚡ Support: 50+ concurrent CLI sessions
- ⚡ Database: <10ms queries

## Cost Estimates

**Self-Hosted (Docker):**
- Server: $10-40/month (VPS with 2GB RAM, 2 vCPU)
  - DigitalOcean Droplet: $12/month
  - AWS EC2 t3.small: $15/month
  - Linode: $10/month
- LLM API: $0.10-0.50/month per active user
- Storage: <1GB per 100 games
- **Total**: $10-50/month for self-hosting

**Cloud Deployment:**
- Container hosting: $20-100/month
  - AWS ECS/Fargate: $30-60/month
  - Google Cloud Run: $20-40/month
  - Azure Container Instances: $25-50/month
- Managed PostgreSQL: $15-30/month
- Managed Redis: $10-20/month
- LLM API: Variable by usage
- **Total**: $65-200/month for managed cloud

**Local Development:**
- Docker Desktop: Free
- LLM API: Pay per use
- **Total**: $0/month (just API costs)

## Success Metrics

### Week 4 (Post-LLM Integration)
- [ ] 1 complete solo session via CLI
- [ ] DM responses are coherent
- [ ] Dice rolls work correctly

### Week 8 (Post-CLI UI)
- [ ] Beautiful terminal interface
- [ ] Multiplayer session in terminal
- [ ] All core features accessible via CLI

### Week 12 (Production)
- [ ] Easy installation process
- [ ] 10+ concurrent CLI sessions
- [ ] Stable local gameplay
- [ ] <5s average DM response

## Risk Mitigation

### Technical Risks
- **LLM costs too high** → Cache responses, use smaller models for simple tasks
- **Performance issues** → Optimize terminal rendering, cache content
- **Terminal compatibility** → Test on multiple terminal emulators

### Product Risks
- **DM quality poor** → Iterate on prompts, add examples
- **User confusion** → Add in-game tutorial, help command
- **CLI too complex** → Add command suggestions, auto-complete

## Quick Wins (Can Do This Week)

1. **CLI Chat Interface** (6 hours)
   - Create basic terminal UI with Rich
   - Display messages with color coding
   - Accept player input
   - Connect to LLM

2. **Basic Dice Roller** (2 hours)
   - Create rules/dice.py
   - Add CLI command for rolling
   - Display results with ASCII art

3. **Character Templates** (3 hours)
   - Create JSON templates for 5 classes
   - Add CLI command to list templates
   - Add CLI command to create from template

4. **ASCII Character Sheet** (4 hours)
   - Display character stats in formatted table
   - Show inventory with borders
   - Add HP bar visualization
   - Color-coded ability scores

## Current Priority Queue

1. 🚧 **Core MVP** (Phase 1-3 - Server, LLM, Rules Engine)
2. 🎯 **Character System** (Phase 4 - Character creation and management)
3. � **Retro CLI Interface** (Phase 5 - Terminal-based gameplay)
4. � **Multiplayer Polish** (Phase 6 - Turn-based CLI gameplay)
5. 📚 **Content & Polish** (Phase 7 - Terminal content generation)
6. 🚀 **Production Ready** (Phase 8 - Simple deployment and docs)

---

## � Project Status: RETRO CLI REBOOT

**Refocusing on authentic 80s terminal experience!** The LLM Dungeon Master is being rebuilt as a pure command-line D&D game inspired by classic text adventures and MUDs.

🎯 **Phases to Build:**
1. Core MVP - FastAPI server, LLM integration, D&D 5e rules engine
2. Character System - Templates, creation, management
3. Retro CLI - Terminal UI with Rich/Prompt Toolkit, ASCII art
4. Multiplayer - Turn-based gameplay in terminal
5. Content Generation - Encounters, NPCs, loot, locations
6. Production Ready - Simple deployment, documentation

**Philosophy:**
- Terminal-first design
- No web browsers required
- Local-first gameplay
- Authentic retro feel
- Fast and lightweight
