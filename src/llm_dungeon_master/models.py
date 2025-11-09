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
    background: Optional[str] = None
    
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
    initiative_bonus: int = Field(default=0)
    speed: int = Field(default=30)
    
    # Progression
    experience_points: int = Field(default=0)
    proficiency_bonus: int = Field(default=2)
    
    # Death Saves
    death_save_successes: int = Field(default=0)
    death_save_failures: int = Field(default=0)
    
    # Spell Slots (for spellcasters)
    spell_slots_1: int = Field(default=0)
    spell_slots_2: int = Field(default=0)
    spell_slots_3: int = Field(default=0)
    spell_slots_4: int = Field(default=0)
    spell_slots_5: int = Field(default=0)
    spell_slots_6: int = Field(default=0)
    spell_slots_7: int = Field(default=0)
    spell_slots_8: int = Field(default=0)
    spell_slots_9: int = Field(default=0)
    
    # Current Spell Slots (used/available)
    current_spell_slots_1: int = Field(default=0)
    current_spell_slots_2: int = Field(default=0)
    current_spell_slots_3: int = Field(default=0)
    current_spell_slots_4: int = Field(default=0)
    current_spell_slots_5: int = Field(default=0)
    current_spell_slots_6: int = Field(default=0)
    current_spell_slots_7: int = Field(default=0)
    current_spell_slots_8: int = Field(default=0)
    current_spell_slots_9: int = Field(default=0)
    
    created_at: datetime = Field(default_factory=utc_now)
    
    # Relationships
    player: Player = Relationship(back_populates="characters")
    spells: list["CharacterSpell"] = Relationship(back_populates="character")
    features: list["CharacterFeature"] = Relationship(back_populates="character")
    equipment: list["CharacterEquipment"] = Relationship(back_populates="character")
    proficiencies: list["CharacterProficiency"] = Relationship(back_populates="character")


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


class CharacterSpell(SQLModel, table=True):
    """A spell known or prepared by a character."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    character_id: int = Field(foreign_key="character.id", index=True)
    spell_name: str
    spell_level: int  # 0 for cantrips
    school: str  # abjuration, conjuration, divination, etc.
    is_prepared: bool = Field(default=False)  # For prepared casters
    is_always_prepared: bool = Field(default=False)  # Domain spells, etc.
    casting_time: str = Field(default="1 action")
    range: str = Field(default="Self")
    components: str = Field(default="V, S")  # Verbal, Somatic, Material
    duration: str = Field(default="Instantaneous")
    description: str
    added_at: datetime = Field(default_factory=utc_now)
    
    # Relationships
    character: Character = Relationship(back_populates="spells")


class CharacterFeature(SQLModel, table=True):
    """A class feature, racial trait, or feat possessed by a character."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    character_id: int = Field(foreign_key="character.id", index=True)
    feature_name: str
    feature_type: str  # class_feature, racial_trait, feat, background
    source: str  # "Fighter 1", "Human", "Lucky (Feat)", etc.
    description: str
    uses_per_rest: Optional[int] = None  # e.g., Second Wind 1/short rest
    uses_remaining: Optional[int] = None
    added_at: datetime = Field(default_factory=utc_now)
    
    # Relationships
    character: Character = Relationship(back_populates="features")


class CharacterEquipment(SQLModel, table=True):
    """An item in a character's inventory."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    character_id: int = Field(foreign_key="character.id", index=True)
    item_name: str
    item_type: str  # weapon, armor, adventuring_gear, tool, treasure
    quantity: int = Field(default=1)
    weight: float = Field(default=0.0)
    cost_gp: float = Field(default=0.0)
    description: Optional[str] = None
    is_equipped: bool = Field(default=False)
    is_attuned: bool = Field(default=False)
    properties: Optional[str] = None  # JSON string for weapon/armor properties
    added_at: datetime = Field(default_factory=utc_now)
    
    # Relationships
    character: Character = Relationship(back_populates="equipment")


class CharacterProficiency(SQLModel, table=True):
    """A proficiency (skill, tool, language, etc.) for a character."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    character_id: int = Field(foreign_key="character.id", index=True)
    proficiency_type: str  # skill, tool, language, weapon, armor, saving_throw
    proficiency_name: str  # "Athletics", "Thieves' Tools", "Common", etc.
    expertise: bool = Field(default=False)  # Double proficiency bonus
    source: str  # "Class", "Race", "Background", etc.
    added_at: datetime = Field(default_factory=utc_now)
    
    # Relationships
    character: Character = Relationship(back_populates="proficiencies")
