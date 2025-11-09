"""FastAPI server with REST API and WebSocket support."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, create_engine, Session as DBSession, select
from pydantic import BaseModel
from datetime import datetime, UTC

from .config import settings
from .models import Session, Player, Character, Message, SessionPlayer
from .llm_provider import get_llm_provider
from .prompts import get_dm_system_message, get_start_session_message
from .dm_service import DMService, RateLimitExceeded, TokenLimitExceeded


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

# DM Service
dm_service = DMService()


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
