# Phase 6 Multiplayer - Quick Reference Guide

## Turn Management Commands

### Start a Turn Queue
```bash
rpg start-turns <session_id> <character_ids>

# Example
rpg start-turns 1 "1,2,3"
```

### View Turn Order
```bash
rpg show-turns <session_id>

# Example
rpg show-turns 1
```

### Advance to Next Turn
```bash
rpg next-turn <session_id>

# Example
rpg next-turn 1
```

### Mark Player Ready
```bash
rpg set-ready <session_id> <character_id> [--ready/--no-ready]

# Example
rpg set-ready 1 2 --ready
```

### Check All Players Ready
```bash
rpg ready-check <session_id>

# Example
rpg ready-check 1
```

## Presence Commands

### View Player Presence
```bash
rpg show-presence <session_id>

# Example
rpg show-presence 1
```

Status indicators:
- 🟢 Online - Active and responding
- 🟡 Away - Heartbeat stale (30s+)
- 🔴 Offline - Disconnected (300s+)

## Reconnection Commands

### Create Reconnection Token
```bash
rpg create-token <player_id> <session_id>

# Example
rpg create-token 1 1
```

**Important**: Save the token! It's only shown once.

### Reconnect to Session
```bash
rpg reconnect <token>

# Example
rpg reconnect "7xK9mQ3vL2pN8wR5yT4uW8aV..."
```

## Synchronization Commands

### Check Sync Status
```bash
rpg sync-check <session_id>

# Example
rpg sync-check 1
```

## API Endpoints

### Turn Management

#### Start Turn Queue
```bash
POST /api/sessions/{session_id}/turns/start
Body: {
  "character_ids": [1, 2, 3],
  "combat_encounter_id": null  # Optional
}
```

#### Get Current Turn
```bash
GET /api/sessions/{session_id}/turns/current
```

#### Get All Turns
```bash
GET /api/sessions/{session_id}/turns
```

#### Advance Turn
```bash
POST /api/sessions/{session_id}/turns/advance
```

#### Set Ready Status
```bash
POST /api/sessions/{session_id}/turns/ready
Body: {
  "character_id": 1,
  "ready": true
}
```

#### Check All Ready
```bash
GET /api/sessions/{session_id}/turns/ready-check
```

#### Get Turn History
```bash
GET /api/sessions/{session_id}/turns/history?limit=50
```

### Presence Tracking

#### Track Connection
```bash
POST /api/sessions/{session_id}/presence/connect
Body: {
  "player_id": 1,
  "connection_id": "ws_123abc"
}
```

#### Update Heartbeat
```bash
POST /api/sessions/{session_id}/presence/heartbeat
Body: {
  "player_id": 1,
  "connection_id": "ws_123abc"
}
```

#### Get Presence Summary
```bash
GET /api/sessions/{session_id}/presence
```

#### Disconnect Player
```bash
POST /api/sessions/{session_id}/presence/disconnect
Body: {
  "player_id": 1,
  "connection_id": "ws_123abc"
}
```

### Synchronization

#### Check State Consistency
```bash
POST /api/sessions/{session_id}/sync/check
Body: {
  "current_turn_character_id": 1,
  "round_number": 1,
  "characters": {
    "1": {"current_hp": 45}
  }
}
```

#### Force Sync
```bash
GET /api/sessions/{session_id}/sync/force
```

#### Get Sync Stats
```bash
GET /api/sessions/{session_id}/sync/stats
```

### Reconnection

#### Create Token
```bash
POST /api/reconnection/token
Body: {
  "player_id": 1,
  "session_id": 1
}
```

#### Reconnect
```bash
POST /api/reconnection/reconnect
Body: {
  "token": "7xK9mQ3vL2pN8wR5..."
}
```

#### Get Token Info
```bash
GET /api/reconnection/token/{token}/info
```

## WebSocket Events

The server broadcasts these events to all connected clients:

### Turn Events
- `turn_queue_started` - New turn queue created
- `turn_advanced` - Turn moved to next player
- `player_ready_status` - Player marked ready/not ready

### Presence Events
- `player_connected` - Player connected
- `player_disconnected` - Player disconnected

### Condition Events
(From Phase 3, still active)
- `condition_applied`
- `condition_removed`

### Roll Events
(From Phase 3, still active)
- `dice_rolled`
- `attack_rolled`
- `damage_rolled`

## Python API Usage

### Turn Manager
```python
from turn_manager import TurnManager

# Initialize
turn_manager = TurnManager(db_session)

# Start turn queue
turns = turn_manager.start_turn_queue(
    session_id=1,
    player_character_ids=[1, 2, 3]
)

# Get current turn
current = turn_manager.get_current_turn(session_id=1)

# Advance turn
next_turn = turn_manager.advance_turn(session_id=1)

# Record action
action = turn_manager.record_action(
    session_id=1,
    character_id=1,
    action_type="attack",
    description="Attacks the goblin",
    cost="action"
)
```

### Presence Manager
```python
from presence_manager import PresenceManager

# Initialize
presence_manager = PresenceManager(db_session)

# Track connection
presence = presence_manager.track_connection(
    session_id=1,
    player_id=1,
    connection_id="ws_123"
)

# Update heartbeat
presence_manager.update_heartbeat(
    session_id=1,
    player_id=1,
    connection_id="ws_123"
)

# Get presence summary
summary = presence_manager.get_presence_summary(session_id=1)
print(f"Online: {summary['online']}, Away: {summary['away']}")
```

### Reconnection Manager
```python
from reconnection_manager import ReconnectionManager

# Initialize
reconnection_manager = ReconnectionManager(db_session)

# Create token
token = reconnection_manager.create_reconnection_token(
    player_id=1,
    session_id=1
)

# Later, reconnect
result = reconnection_manager.handle_reconnection(token)
if result["success"]:
    session_state = result["session_state"]
    print(f"Restored character: {session_state['character']['name']}")
```

## Troubleshooting

### Player Can't Connect
1. Check presence: `rpg show-presence <session_id>`
2. Verify session exists: `rpg list-sessions`
3. Check API health: `curl http://localhost:8000/health`

### Turn Stuck
1. Check current turn: `rpg show-turns <session_id>`
2. Force advance: `rpg next-turn <session_id>`
3. Check sync status: `rpg sync-check <session_id>`

### Reconnection Failed
1. Check token hasn't expired (24 hours)
2. Verify token hasn't been used (one-time use)
3. Create new token: `rpg create-token <player_id> <session_id>`

### State Out of Sync
1. Check consistency: API POST `/api/sessions/{id}/sync/check`
2. Force sync: API GET `/api/sessions/{id}/sync/force`
3. Refresh client state from response

## Performance Tips

1. **Heartbeat regularly** - Every 20-25 seconds to avoid "away" status
2. **Cleanup old tokens** - Run cleanup periodically
3. **Limit turn history** - Use `limit` parameter (default 50)
4. **Use WebSocket** - For real-time updates instead of polling

## Security Best Practices

1. **Never share tokens** - One per player, one-time use
2. **Store tokens securely** - In environment variables or secure storage
3. **Revoke compromised tokens** - Use revoke endpoint immediately
4. **Monitor presence** - Watch for suspicious connection patterns
5. **Validate state** - Regular sync checks prevent cheating

## Common Workflows

### Starting a Multiplayer Session
```bash
# 1. Create session
rpg create-session "Epic Adventure"

# 2. Create characters for each player
rpg create-character 1 "Legolas" Elf Ranger --dexterity 18
rpg create-character 2 "Aragorn" Human Fighter --strength 16
rpg create-character 3 "Gandalf" Human Wizard --intelligence 18

# 3. Start turn queue
rpg start-turns 1 "1,2,3"

# 4. Check presence
rpg show-presence 1

# 5. Begin gameplay!
rpg show-turns 1
```

### Handling Player Disconnect
```bash
# 1. Player disconnects (automatic in WebSocket)

# 2. Create reconnection token
rpg create-token 1 1

# 3. Send token to player (secure channel!)

# 4. Player reconnects
rpg reconnect "<token>"

# 5. Verify presence
rpg show-presence 1
```

### Turn-Based Combat
```bash
# 1. Start turn queue with combat encounter
rpg start-turns 1 "1,2,3" --combat-encounter 5

# 2. Check turn order
rpg show-turns 1

# 3. Player takes action (via game commands)

# 4. Advance turn
rpg next-turn 1

# 5. Repeat until combat ends
```

## Configuration

### Presence Timeouts
Edit `presence_manager.py`:
```python
self.heartbeat_timeout = 30  # seconds before "away"
self.offline_timeout = 300   # seconds before "offline"
```

### Token Expiry
Edit `reconnection_manager.py`:
```python
self.token_expiry_hours = 24  # hours until expiry
```

## Status Codes

### HTTP Status Codes
- `200` - Success
- `201` - Created (token, turn queue)
- `401` - Unauthorized (invalid token)
- `404` - Not found (session, turn, presence)
- `422` - Validation error

### Turn Statuses
- `waiting` - Not yet active
- `active` - Currently taking turn
- `ready` - Player marked ready
- `completed` - Turn finished
- `skipped` - Turn was skipped

### Presence Statuses
- `online` - Active and responding (green 🟢)
- `away` - Heartbeat stale (yellow 🟡)
- `offline` - Disconnected (red 🔴)

---

For more details, see:
- `docs/PHASE6_SUMMARY.md` - Complete implementation details
- `docs/PHASE6_COMPLETE.md` - Completion report
- `docs/ROADMAP.md` - Project roadmap
