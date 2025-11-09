"""Database models for the LLM Dungeon Master."""

from datetime import datetime, UTC
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship


def utc_now():
    """Get current UTC time."""
    return datetime.now(UTC)


class Player(SQLModel, table=True):
    """A player in the game."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    created_at: datetime = Field(default_factory=utc_now)
    
    # Relationships
    characters: list["Character"] = Relationship(back_populates="player")
    sessions: list["SessionPlayer"] = Relationship(back_populates="player")


class Session(SQLModel, table=True):
    """A game session."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    dm_name: str = Field(default="Dungeon Master")
    created_at: datetime = Field(default_factory=utc_now)
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
    joined_at: datetime = Field(default_factory=utc_now)
    
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
    
    created_at: datetime = Field(default_factory=utc_now)
    
    # Relationships
    player: Player = Relationship(back_populates="characters")


class Message(SQLModel, table=True):
    """A message in a game session."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="session.id", index=True)
    sender_name: str
    content: str
    message_type: str = Field(default="player")  # player, dm, system
    created_at: datetime = Field(default_factory=utc_now)
    
    # Relationships
    session: Session = Relationship(back_populates="messages")


class Roll(SQLModel, table=True):
    """A dice roll made during a session."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="session.id", index=True)
    character_id: Optional[int] = Field(default=None, foreign_key="character.id")
    roll_type: str  # attack, damage, check, save, initiative
    formula: str  # e.g., "2d6+3"
    result: int
    rolls: str  # JSON string of individual die rolls
    modifier: int = Field(default=0)
    advantage_type: int = Field(default=0)  # -1=disadvantage, 0=normal, 1=advantage
    is_critical: bool = Field(default=False)
    is_critical_fail: bool = Field(default=False)
    context: Optional[str] = None  # e.g., "Attack vs Goblin", "Perception check"
    created_at: datetime = Field(default_factory=utc_now)


class CombatEncounter(SQLModel, table=True):
    """A combat encounter in a session."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="session.id", index=True)
    name: str  # e.g., "Goblin Ambush"
    round_number: int = Field(default=1)
    current_turn_index: int = Field(default=0)
    is_active: bool = Field(default=True)
    started_at: datetime = Field(default_factory=utc_now)
    ended_at: Optional[datetime] = None
    
    # Relationships
    combatants: list["CombatantState"] = Relationship(back_populates="encounter")


class CombatantState(SQLModel, table=True):
    """State of a combatant in an encounter."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    encounter_id: int = Field(foreign_key="combatencounter.id", index=True)
    character_id: Optional[int] = Field(default=None, foreign_key="character.id")
    name: str
    initiative: int
    current_hp: int
    max_hp: int
    armor_class: int
    is_npc: bool = Field(default=False)
    is_alive: bool = Field(default=True)
    
    # Relationships
    encounter: CombatEncounter = Relationship(back_populates="combatants")


class CharacterCondition(SQLModel, table=True):
    """A condition affecting a character."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    character_id: int = Field(foreign_key="character.id", index=True)
    session_id: int = Field(foreign_key="session.id", index=True)
    condition_type: str  # blinded, charmed, frightened, etc.
    source: str  # What caused the condition
    duration_type: str  # rounds, minutes, hours, until_save, permanent
    duration_value: int = Field(default=0)
    rounds_remaining: Optional[int] = None
    save_dc: Optional[int] = None
    save_ability: Optional[str] = None  # Str, Dex, Con, etc.
    applied_at: datetime = Field(default_factory=utc_now)
    removed_at: Optional[datetime] = None
    is_active: bool = Field(default=True)
