"""FastAPI server with REST API and WebSocket support."""

from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, create_engine, Session as DBSession, select
from pydantic import BaseModel
from datetime import datetime, UTC

from .config import settings
from .models import (
    Session, Player, Character, Message, SessionPlayer, Roll, 
    CombatEncounter, CombatantState, CharacterCondition
)
from .llm_provider import get_llm_provider
from .prompts import get_dm_system_message, get_start_session_message
from .dm_service import DMService, RateLimitExceeded, TokenLimitExceeded
from .rules.dice import (
    roll_dice, resolve_check, resolve_attack, roll_damage, 
    AdvantageType, RollResult
)
from .rules.combat import CombatManager, ActionType
from .rules.conditions import ConditionManager, ConditionType, DurationType


# Database setup
engine = create_engine(settings.database_url, echo=settings.debug)


def create_db_and_tables():
    """Create database tables."""
    SQLModel.metadata.create_all(engine)


def get_db():
    """Get database session."""
    with DBSession(engine) as session:
        yield session


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for the application."""
    # Startup
    create_db_and_tables()
    yield
    # Shutdown
    pass


# FastAPI app
app = FastAPI(
    title="LLM Dungeon Master",
    description="A retro CLI-based D&D game with LLM-powered Dungeon Master",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# WebSocket connection manager
class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: int):
        """Connect a websocket to a session."""
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, session_id: int):
        """Disconnect a websocket from a session."""
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
    
    async def broadcast(self, session_id: int, message: dict):
        """Broadcast a message to all connections in a session."""
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                await connection.send_json(message)


manager = ConnectionManager()

# Services
dm_service = DMService()
combat_manager = CombatManager()
condition_manager = ConditionManager()


# Pydantic models for API
class SessionCreate(BaseModel):
    name: str
    dm_name: str = "Dungeon Master"


class PlayerCreate(BaseModel):
    name: str


class CharacterCreate(BaseModel):
    player_id: int
    name: str
    race: str
    char_class: str
    level: int = 1
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10


class MessageCreate(BaseModel):
    sender_name: str
    content: str
    message_type: str = "player"


class DiceRollRequest(BaseModel):
    formula: str
    advantage: int = 0  # -1=disadvantage, 0=normal, 1=advantage
    character_id: Optional[int] = None
    context: Optional[str] = None


class CheckRequest(BaseModel):
    ability_score: int
    dc: int
    proficiency_bonus: int = 0
    advantage: int = 0
    character_id: Optional[int] = None
    context: Optional[str] = None


class AttackRequest(BaseModel):
    attack_bonus: int
    target_ac: int
    advantage: int = 0
    character_id: Optional[int] = None
    target_name: Optional[str] = None


class DamageRequest(BaseModel):
    formula: str
    is_critical: bool = False


class CombatStartRequest(BaseModel):
    character_ids: list[int]


class CombatAttackRequest(BaseModel):
    attacker_id: int
    target_id: int
    attack_bonus: int
    damage_formula: str
    advantage: int = 0


class ConditionRequest(BaseModel):
    character_id: int
    character_name: str
    condition_type: str
    source: str
    duration_type: str
    duration_value: int = 0
    save_dc: Optional[int] = None
    save_ability: Optional[str] = None


# API Routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to LLM Dungeon Master API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now(UTC).isoformat()}


# Session endpoints
@app.post("/api/sessions", response_model=Session)
async def create_session(session: SessionCreate, db: DBSession = Depends(get_db)):
    """Create a new game session."""
    db_session = Session(name=session.name, dm_name=session.dm_name)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


@app.get("/api/sessions", response_model=list[Session])
async def list_sessions(db: DBSession = Depends(get_db)):
    """List all game sessions."""
    statement = select(Session)
    sessions = db.exec(statement).all()
    return sessions


@app.get("/api/sessions/{session_id}", response_model=Session)
async def get_session(session_id: int, db: DBSession = Depends(get_db)):
    """Get a specific session."""
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# Player endpoints
@app.post("/api/players", response_model=Player)
async def create_player(player: PlayerCreate, db: DBSession = Depends(get_db)):
    """Create a new player."""
    db_player = Player(name=player.name)
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player


@app.get("/api/players", response_model=list[Player])
async def list_players(db: DBSession = Depends(get_db)):
    """List all players."""
    statement = select(Player)
    players = db.exec(statement).all()
    return players


# Character endpoints
@app.post("/api/characters", response_model=Character)
async def create_character(character: CharacterCreate, db: DBSession = Depends(get_db)):
    """Create a new character."""
    db_character = Character(**character.model_dump())
    db_character.current_hp = db_character.max_hp
    db.add(db_character)
    db.commit()
    db.refresh(db_character)
    return db_character


@app.get("/api/characters", response_model=list[Character])
async def list_characters(player_id: int = None, db: DBSession = Depends(get_db)):
    """List all characters, optionally filtered by player."""
    statement = select(Character)
    if player_id:
        statement = statement.where(Character.player_id == player_id)
    characters = db.exec(statement).all()
    return characters


@app.get("/api/characters/{character_id}", response_model=Character)
async def get_character(character_id: int, db: DBSession = Depends(get_db)):
    """Get a specific character."""
    character = db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


@app.put("/api/characters/{character_id}", response_model=Character)
async def update_character(
    character_id: int,
    character_update: CharacterCreate,
    db: DBSession = Depends(get_db)
):
    """Update a character."""
    db_character = db.get(Character, character_id)
    if not db_character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    update_data = character_update.model_dump()
    for key, value in update_data.items():
        setattr(db_character, key, value)
    
    db.add(db_character)
    db.commit()
    db.refresh(db_character)
    return db_character


@app.delete("/api/characters/{character_id}")
async def delete_character(character_id: int, db: DBSession = Depends(get_db)):
    """Delete a character."""
    character = db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    db.delete(character)
    db.commit()
    return {"message": f"Character {character.name} deleted successfully"}


@app.get("/api/characters/classes")
async def list_character_classes():
    """List available character classes."""
    from .character_builder import CharacterBuilder
    from sqlmodel import Session as DBSession
    
    with DBSession(engine) as db:
        builder = CharacterBuilder(db)
        classes = builder.list_available_classes()
        return {"classes": classes}


@app.post("/api/characters/from-template")
async def create_character_from_template(
    player_id: int,
    name: str,
    race: str,
    char_class: str,
    strength: int,
    dexterity: int,
    constitution: int,
    intelligence: int,
    wisdom: int,
    charisma: int,
    background: Optional[str] = None,
    skills: Optional[list[str]] = None,
    db: DBSession = Depends(get_db)
):
    """Create a character from a class template with point buy."""
    from .character_builder import CharacterBuilder, ValidationError
    
    builder = CharacterBuilder(db)
    
    ability_scores = {
        "strength": strength,
        "dexterity": dexterity,
        "constitution": constitution,
        "intelligence": intelligence,
        "wisdom": wisdom,
        "charisma": charisma
    }
    
    try:
        character = builder.create_from_template(
            player_id=player_id,
            name=name,
            race=race,
            char_class=char_class,
            ability_scores=ability_scores,
            background=background,
            skills=skills
        )
        return character
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/characters/{character_id}/summary")
async def get_character_summary(character_id: int, db: DBSession = Depends(get_db)):
    """Get a detailed summary of a character."""
    from .character_builder import CharacterBuilder
    
    character = db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    builder = CharacterBuilder(db)
    summary = builder.get_character_summary(character)
    return summary


@app.post("/api/characters/{character_id}/validate")
async def validate_character(character_id: int, db: DBSession = Depends(get_db)):
    """Validate a character's stats and configuration."""
    from .character_builder import CharacterBuilder
    
    character = db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    builder = CharacterBuilder(db)
    is_valid, errors = builder.validate_character(character)
    
    return {
        "is_valid": is_valid,
        "errors": errors
    }


@app.post("/api/characters/{character_id}/level-up", response_model=Character)
async def level_up_character(character_id: int, db: DBSession = Depends(get_db)):
    """Level up a character."""
    from .character_builder import CharacterBuilder, ValidationError
    
    character = db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    builder = CharacterBuilder(db)
    
    try:
        character = builder.apply_level_up(character)
        return character
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Message endpoints
@app.get("/api/sessions/{session_id}/messages", response_model=list[Message])
async def get_messages(session_id: int, limit: int = 50, db: DBSession = Depends(get_db)):
    """Get messages for a session."""
    statement = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    messages = db.exec(statement).all()
    return list(reversed(messages))


@app.post("/api/sessions/{session_id}/messages", response_model=Message)
async def create_message(
    session_id: int,
    message: MessageCreate,
    db: DBSession = Depends(get_db)
):
    """Create a new message in a session."""
    db_message = Message(
        session_id=session_id,
        sender_name=message.sender_name,
        content=message.content,
        message_type=message.message_type
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # Broadcast to WebSocket connections
    await manager.broadcast(session_id, {
        "type": "message",
        "sender": message.sender_name,
        "content": message.content,
        "message_type": message.message_type,
        "timestamp": db_message.created_at.isoformat()
    })
    
    return db_message


# DM Service endpoints
@app.post("/api/sessions/{session_id}/start")
async def start_dm_session(session_id: int, db: DBSession = Depends(get_db)):
    """Start a session with DM opening message."""
    try:
        response = await dm_service.start_session(db=db, session_id=session_id)
        return {"message": response}
    except RateLimitExceeded as e:
        raise HTTPException(status_code=429, detail=str(e))
    except TokenLimitExceeded as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions/{session_id}/action")
async def process_action(
    session_id: int,
    player_name: str,
    action: str,
    db: DBSession = Depends(get_db)
):
    """Process a player action and get DM response."""
    try:
        response = await dm_service.process_player_action(
            db=db,
            session_id=session_id,
            player_name=player_name,
            action=action
        )
        return {"message": response}
    except RateLimitExceeded as e:
        raise HTTPException(status_code=429, detail=str(e))
    except TokenLimitExceeded as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/tokens")
async def get_token_usage(session_id: int):
    """Get token usage statistics for a session."""
    return dm_service.get_token_usage(session_id)


# Dice rolling endpoints
@app.post("/api/sessions/{session_id}/roll")
async def roll_dice_endpoint(
    session_id: int,
    request: DiceRollRequest,
    db: DBSession = Depends(get_db)
):
    """Roll dice with optional advantage/disadvantage."""
    try:
        advantage = AdvantageType(request.advantage)
        result = roll_dice(request.formula, advantage)
        
        # Save roll to database
        db_roll = Roll(
            session_id=session_id,
            character_id=request.character_id,
            roll_type="generic",
            formula=request.formula,
            result=result.total,
            rolls=str(result.rolls),
            advantage_type=request.advantage,
            is_critical=result.is_critical,
            is_critical_fail=result.is_critical_fail,
            context=request.context
        )
        db.add(db_roll)
        db.commit()
        
        # Broadcast to WebSocket
        await manager.broadcast(session_id, {
            "type": "roll",
            "roll_type": "generic",
            "formula": request.formula,
            "result": result.total,
            "rolls": result.rolls,
            "is_critical": result.is_critical,
            "is_critical_fail": result.is_critical_fail,
            "context": request.context
        })
        
        return {
            "formula": result.formula,
            "total": result.total,
            "rolls": result.rolls,
            "advantage_type": result.advantage_type.value,
            "is_critical": result.is_critical,
            "is_critical_fail": result.is_critical_fail
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/sessions/{session_id}/check")
async def ability_check_endpoint(
    session_id: int,
    request: CheckRequest,
    db: DBSession = Depends(get_db)
):
    """Resolve an ability check."""
    try:
        advantage = AdvantageType(request.advantage)
        result = resolve_check(
            request.ability_score,
            request.dc,
            request.proficiency_bonus,
            advantage
        )
        
        # Save roll to database
        db_roll = Roll(
            session_id=session_id,
            character_id=request.character_id,
            roll_type="check",
            formula="1d20",
            result=result.roll,
            rolls=str([result.roll]),
            modifier=result.modifier,
            advantage_type=request.advantage,
            is_critical=result.is_critical,
            is_critical_fail=result.is_critical_fail,
            context=request.context
        )
        db.add(db_roll)
        db.commit()
        
        # Broadcast to WebSocket
        await manager.broadcast(session_id, {
            "type": "check",
            "success": result.success,
            "roll": result.roll,
            "dc": result.dc,
            "total": result.total,
            "modifier": result.modifier,
            "is_critical": result.is_critical,
            "is_critical_fail": result.is_critical_fail,
            "context": request.context
        })
        
        return {
            "success": result.success,
            "roll": result.roll,
            "dc": result.dc,
            "total": result.total,
            "modifier": result.modifier,
            "advantage_type": result.advantage_type.value,
            "is_critical": result.is_critical,
            "is_critical_fail": result.is_critical_fail
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/sessions/{session_id}/attack")
async def attack_roll_endpoint(
    session_id: int,
    request: AttackRequest,
    db: DBSession = Depends(get_db)
):
    """Resolve an attack roll."""
    try:
        advantage = AdvantageType(request.advantage)
        result = resolve_attack(request.attack_bonus, request.target_ac, advantage)
        
        # Save roll to database
        db_roll = Roll(
            session_id=session_id,
            character_id=request.character_id,
            roll_type="attack",
            formula="1d20",
            result=result.roll,
            rolls=str([result.roll]),
            modifier=request.attack_bonus,
            advantage_type=request.advantage,
            is_critical=result.is_critical,
            is_critical_fail=result.is_critical_fail,
            context=f"Attack vs {request.target_name}" if request.target_name else "Attack"
        )
        db.add(db_roll)
        db.commit()
        
        # Broadcast to WebSocket
        await manager.broadcast(session_id, {
            "type": "attack",
            "hit": result.success,
            "roll": result.roll,
            "target_ac": result.dc,
            "total": result.total,
            "is_critical": result.is_critical,
            "is_critical_fail": result.is_critical_fail,
            "target_name": request.target_name
        })
        
        return {
            "hit": result.success,
            "roll": result.roll,
            "target_ac": result.dc,
            "total": result.total,
            "advantage_type": result.advantage_type.value,
            "is_critical": result.is_critical,
            "is_critical_fail": result.is_critical_fail
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/sessions/{session_id}/damage")
async def damage_roll_endpoint(
    session_id: int,
    request: DamageRequest,
    db: DBSession = Depends(get_db)
):
    """Roll damage with optional critical hit."""
    try:
        result = roll_damage(request.formula, request.is_critical)
        
        return {
            "formula": result.formula,
            "total": result.total,
            "rolls": result.rolls,
            "is_critical": request.is_critical
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Combat endpoints
@app.post("/api/sessions/{session_id}/combat/start")
async def start_combat(
    session_id: int,
    request: CombatStartRequest,
    db: DBSession = Depends(get_db)
):
    """Start a combat encounter."""
    try:
        combat_state = combat_manager.start_combat(db, session_id, request.character_ids)
        
        # Save to database
        db_encounter = CombatEncounter(
            session_id=session_id,
            name=f"Combat {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}",
            round_number=combat_state.round_number,
            current_turn_index=combat_state.current_turn_index
        )
        db.add(db_encounter)
        db.commit()
        db.refresh(db_encounter)
        
        # Save combatants
        for combatant in combat_state.combatants:
            db_combatant = CombatantState(
                encounter_id=db_encounter.id,
                character_id=combatant.character_id,
                name=combatant.name,
                initiative=combatant.initiative,
                current_hp=combatant.current_hp,
                max_hp=combatant.max_hp,
                armor_class=combatant.armor_class
            )
            db.add(db_combatant)
        db.commit()
        
        # Broadcast to WebSocket
        await manager.broadcast(session_id, {
            "type": "combat_start",
            "encounter_id": db_encounter.id,
            "round": combat_state.round_number,
            "initiative_order": combat_manager.get_initiative_order(session_id),
            "log": combat_state.combat_log
        })
        
        return {
            "encounter_id": db_encounter.id,
            "round": combat_state.round_number,
            "initiative_order": combat_manager.get_initiative_order(session_id),
            "current_combatant": combat_state.current_combatant.name if combat_state.current_combatant else None,
            "combat_log": combat_state.combat_log
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/sessions/{session_id}/combat")
async def get_combat(session_id: int):
    """Get current combat state."""
    combat_state = combat_manager.get_combat(session_id)
    if not combat_state:
        raise HTTPException(status_code=404, detail="No active combat")
    
    return {
        "round": combat_state.round_number,
        "initiative_order": combat_manager.get_initiative_order(session_id),
        "current_combatant": combat_state.current_combatant.name if combat_state.current_combatant else None,
        "combat_log": combat_state.combat_log,
        "is_combat_over": combat_state.is_combat_over
    }


@app.post("/api/sessions/{session_id}/combat/next-turn")
async def next_turn(session_id: int):
    """Advance to the next turn in combat."""
    combat_state = combat_manager.next_turn(session_id)
    if not combat_state:
        raise HTTPException(status_code=404, detail="No active combat")
    
    # Broadcast to WebSocket
    await manager.broadcast(session_id, {
        "type": "combat_next_turn",
        "round": combat_state.round_number,
        "current_combatant": combat_state.current_combatant.name if combat_state.current_combatant else None,
        "is_combat_over": combat_state.is_combat_over
    })
    
    return {
        "round": combat_state.round_number,
        "current_combatant": combat_state.current_combatant.name if combat_state.current_combatant else None,
        "is_combat_over": combat_state.is_combat_over,
        "combat_log": combat_state.combat_log[-5:]  # Last 5 log entries
    }


@app.post("/api/sessions/{session_id}/combat/attack")
async def combat_attack(
    session_id: int,
    request: CombatAttackRequest
):
    """Resolve an attack in combat."""
    try:
        advantage = AdvantageType(request.advantage)
        result = combat_manager.resolve_attack(
            session_id,
            request.attacker_id,
            request.target_id,
            request.attack_bonus,
            request.damage_formula,
            advantage
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Combat not found or invalid combatants")
        
        # Broadcast to WebSocket
        await manager.broadcast(session_id, {
            "type": "combat_attack",
            "attacker": result.attacker_name,
            "target": result.target_name,
            "hit": result.hit,
            "damage": result.damage,
            "is_critical": result.is_critical,
            "attack_roll": result.attack_roll
        })
        
        return {
            "hit": result.hit,
            "damage": result.damage,
            "is_critical": result.is_critical,
            "attack_roll": result.attack_roll,
            "target_ac": result.target_ac,
            "attacker_name": result.attacker_name,
            "target_name": result.target_name
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/sessions/{session_id}/combat/end")
async def end_combat(session_id: int, db: DBSession = Depends(get_db)):
    """End the current combat encounter."""
    if not combat_manager.end_combat(session_id):
        raise HTTPException(status_code=404, detail="No active combat")
    
    # Update database
    statement = (
        select(CombatEncounter)
        .where(CombatEncounter.session_id == session_id)
        .where(CombatEncounter.is_active == True)
    )
    encounter = db.exec(statement).first()
    if encounter:
        encounter.is_active = False
        encounter.ended_at = datetime.now(UTC)
        db.commit()
    
    # Broadcast to WebSocket
    await manager.broadcast(session_id, {
        "type": "combat_end",
        "message": "Combat has ended"
    })
    
    return {"message": "Combat ended"}


# Condition endpoints
@app.post("/api/sessions/{session_id}/conditions")
async def apply_condition(
    session_id: int,
    request: ConditionRequest,
    db: DBSession = Depends(get_db)
):
    """Apply a condition to a character."""
    try:
        condition_type = ConditionType(request.condition_type)
        duration_type = DurationType(request.duration_type)
        
        condition = condition_manager.apply_condition(
            request.character_id,
            request.character_name,
            condition_type,
            request.source,
            duration_type,
            request.duration_value,
            request.save_dc,
            request.save_ability
        )
        
        # Save to database
        db_condition = CharacterCondition(
            character_id=request.character_id,
            session_id=session_id,
            condition_type=condition_type.value,
            source=request.source,
            duration_type=duration_type.value,
            duration_value=request.duration_value,
            rounds_remaining=condition.rounds_remaining,
            save_dc=request.save_dc,
            save_ability=request.save_ability
        )
        db.add(db_condition)
        db.commit()
        
        # Broadcast to WebSocket
        await manager.broadcast(session_id, {
            "type": "condition_applied",
            "character_id": request.character_id,
            "character_name": request.character_name,
            "condition": condition_type.value,
            "description": condition.description
        })
        
        return {
            "condition_type": condition_type.value,
            "description": condition.description,
            "duration_type": duration_type.value,
            "rounds_remaining": condition.rounds_remaining
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid condition or duration type: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/characters/{character_id}/conditions")
async def get_character_conditions(character_id: int):
    """Get all conditions affecting a character."""
    char_conditions = condition_manager.get_conditions(character_id)
    if not char_conditions:
        return {"character_id": character_id, "conditions": [], "effects": {}}
    
    effects = condition_manager.check_condition_effects(character_id)
    
    return {
        "character_id": character_id,
        "character_name": char_conditions.character_name,
        "conditions": [
            {
                "type": c.condition_type.value,
                "description": c.description,
                "source": c.source,
                "rounds_remaining": c.rounds_remaining
            }
            for c in char_conditions.active_conditions
        ],
        "effects": effects
    }


@app.delete("/api/characters/{character_id}/conditions/{condition_type}")
async def remove_condition(
    character_id: int,
    condition_type: str,
    session_id: int,
    db: DBSession = Depends(get_db)
):
    """Remove a condition from a character."""
    try:
        ct = ConditionType(condition_type)
        success = condition_manager.remove_condition(character_id, ct)
        
        if not success:
            raise HTTPException(status_code=404, detail="Condition not found")
        
        # Update database
        statement = (
            select(CharacterCondition)
            .where(CharacterCondition.character_id == character_id)
            .where(CharacterCondition.session_id == session_id)
            .where(CharacterCondition.condition_type == condition_type)
            .where(CharacterCondition.is_active == True)
        )
        db_condition = db.exec(statement).first()
        if db_condition:
            db_condition.is_active = False
            db_condition.removed_at = datetime.now(UTC)
            db.commit()
        
        # Broadcast to WebSocket
        await manager.broadcast(session_id, {
            "type": "condition_removed",
            "character_id": character_id,
            "condition": condition_type
        })
        
        return {"message": f"Condition {condition_type} removed"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid condition type")


# WebSocket endpoint
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: int):
    """WebSocket endpoint for real-time game communication."""
    await manager.connect(websocket, session_id)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "system",
            "content": f"Connected to session {session_id}"
        })
        
        # Send token usage info
        token_stats = dm_service.get_token_usage(session_id)
        await websocket.send_json({
            "type": "system",
            "content": f"Token usage: {token_stats['used']}/{token_stats['limit']}"
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get("type", "action")
            sender = data.get("sender", "Player")
            content = data.get("content", "")
            
            # Broadcast player message to all clients
            await manager.broadcast(session_id, {
                "type": "message",
                "sender": sender,
                "content": content,
                "message_type": "player"
            })
            
            try:
                # Process based on message type
                if message_type == "action":
                    # Handle player action with DMService
                    with DBSession(engine) as db:
                        # Use streaming response
                        full_response = []
                        async for chunk in dm_service.generate_stream(
                            db=db,
                            session_id=session_id,
                            player_name=sender,
                            action=content
                        ):
                            full_response.append(chunk)
                            # Stream chunk to all clients
                            await manager.broadcast(session_id, {
                                "type": "stream",
                                "sender": "Dungeon Master",
                                "content": chunk
                            })
                        
                        # Send end of stream marker
                        await manager.broadcast(session_id, {
                            "type": "stream_end",
                            "sender": "Dungeon Master",
                            "full_content": "".join(full_response)
                        })
                
                elif message_type == "roll":
                    # Handle dice roll
                    roll_type = data.get("roll_type", "check")
                    result = data.get("result", 10)
                    dice = data.get("dice", "1d20")
                    modifier = data.get("modifier", 0)
                    
                    with DBSession(engine) as db:
                        dm_response = await dm_service.handle_roll(
                            db=db,
                            session_id=session_id,
                            player_name=sender,
                            roll_type=roll_type,
                            result=result,
                            dice=dice,
                            modifier=modifier
                        )
                    
                    # Broadcast DM response
                    await manager.broadcast(session_id, {
                        "type": "message",
                        "sender": "Dungeon Master",
                        "content": dm_response,
                        "message_type": "dm"
                    })
                
                # Send updated token usage
                token_stats = dm_service.get_token_usage(session_id)
                await websocket.send_json({
                    "type": "token_usage",
                    "used": token_stats['used'],
                    "limit": token_stats['limit'],
                    "remaining": token_stats['remaining']
                })
                
            except RateLimitExceeded as e:
                await websocket.send_json({
                    "type": "error",
                    "content": f"Rate limit exceeded: {str(e)}"
                })
            
            except TokenLimitExceeded as e:
                await websocket.send_json({
                    "type": "error",
                    "content": f"Token limit exceeded: {str(e)}"
                })
            
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "content": f"Error processing message: {str(e)}"
                })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
        await manager.broadcast(session_id, {
            "type": "system",
            "content": "A player has disconnected"
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "llm_dungeon_master.server:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
