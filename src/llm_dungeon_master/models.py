"""Database models for the LLM Dungeon Master."""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship


class Player(SQLModel, table=True):
    """A player in the game."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    characters: list["Character"] = Relationship(back_populates="player")
    sessions: list["SessionPlayer"] = Relationship(back_populates="player")


class Session(SQLModel, table=True):
    """A game session."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    dm_name: str = Field(default="Dungeon Master")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    
    # Relationships
    messages: list["Message"] = Relationship(back_populates="session")
    players: list["SessionPlayer"] = Relationship(back_populates="session")


class SessionPlayer(SQLModel, table=True):
    """Link between sessions and players."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="session.id")
    player_id: int = Field(foreign_key="player.id")
    character_id: Optional[int] = Field(default=None, foreign_key="character.id")
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    session: Session = Relationship(back_populates="players")
    player: Player = Relationship(back_populates="sessions")
    character: Optional["Character"] = Relationship()


class Character(SQLModel, table=True):
    """A player character."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: int = Field(foreign_key="player.id")
    name: str = Field(index=True)
    race: str
    char_class: str = Field(alias="class")
    level: int = Field(default=1)
    
    # Ability Scores
    strength: int = Field(default=10)
    dexterity: int = Field(default=10)
    constitution: int = Field(default=10)
    intelligence: int = Field(default=10)
    wisdom: int = Field(default=10)
    charisma: int = Field(default=10)
    
    # Combat Stats
    max_hp: int = Field(default=10)
    current_hp: int = Field(default=10)
    armor_class: int = Field(default=10)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    player: Player = Relationship(back_populates="characters")


class Message(SQLModel, table=True):
    """A message in a game session."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="session.id", index=True)
    sender_name: str
    content: str
    message_type: str = Field(default="player")  # player, dm, system
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    session: Session = Relationship(back_populates="messages")
