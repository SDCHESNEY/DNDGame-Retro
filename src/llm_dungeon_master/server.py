"""FastAPI server with REST API and WebSocket support."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, create_engine, Session as DBSession, select
from pydantic import BaseModel
from datetime import datetime

from .config import settings
from .models import Session, Player, Character, Message, SessionPlayer
from .llm_provider import get_llm_provider
from .prompts import get_dm_system_message, get_start_session_message


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
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


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


# WebSocket endpoint
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: int):
    """WebSocket endpoint for real-time game communication."""
    await manager.connect(websocket, session_id)
    llm_provider = get_llm_provider()
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "system",
            "content": f"Connected to session {session_id}"
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Save player message to database
            with DBSession(engine) as db:
                player_msg = Message(
                    session_id=session_id,
                    sender_name=data.get("sender", "Player"),
                    content=data.get("content", ""),
                    message_type="player"
                )
                db.add(player_msg)
                db.commit()
            
            # Broadcast player message to all clients
            await manager.broadcast(session_id, {
                "type": "message",
                "sender": data.get("sender", "Player"),
                "content": data.get("content", ""),
                "message_type": "player"
            })
            
            # Get conversation history
            with DBSession(engine) as db:
                statement = (
                    select(Message)
                    .where(Message.session_id == session_id)
                    .order_by(Message.created_at.desc())
                    .limit(10)
                )
                recent_messages = list(reversed(db.exec(statement).all()))
            
            # Build conversation for LLM
            conversation = [get_dm_system_message()]
            for msg in recent_messages:
                role = "assistant" if msg.message_type == "dm" else "user"
                conversation.append({
                    "role": role,
                    "content": f"{msg.sender_name}: {msg.content}"
                })
            
            # Get DM response
            dm_response = await llm_provider.generate_response(conversation)
            
            # Save DM response to database
            with DBSession(engine) as db:
                dm_msg = Message(
                    session_id=session_id,
                    sender_name="Dungeon Master",
                    content=dm_response,
                    message_type="dm"
                )
                db.add(dm_msg)
                db.commit()
            
            # Broadcast DM response
            await manager.broadcast(session_id, {
                "type": "message",
                "sender": "Dungeon Master",
                "content": dm_response,
                "message_type": "dm"
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
