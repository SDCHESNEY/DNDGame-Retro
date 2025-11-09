"""Command-line interface for the LLM Dungeon Master."""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from sqlmodel import create_engine, Session as DBSession, select
from typing import Optional

from .config import settings
from .models import Session, Player, Character, Message, SessionPlayer

app = typer.Typer(
    name="rpg",
    help="LLM Dungeon Master - A retro CLI-based D&D game",
    add_completion=False
)

console = Console()
engine = create_engine(settings.database_url, echo=False)


@app.command()
def version():
    """Show the version."""
    console.print("[bold green]LLM Dungeon Master v0.1.0[/bold green]")


@app.command()
def init():
    """Initialize the database."""
    from .models import SQLModel
    
    console.print("[yellow]Initializing database...[/yellow]")
    SQLModel.metadata.create_all(engine)
    console.print("[green]✓ Database initialized successfully![/green]")


@app.command()
def serve(
    host: str = typer.Option(None, help="Host to bind to"),
    port: int = typer.Option(None, help="Port to bind to"),
    reload: bool = typer.Option(False, help="Enable auto-reload")
):
    """Start the FastAPI server."""
    import uvicorn
    
    _host = host or settings.host
    _port = port or settings.port
    _reload = reload or settings.debug
    
    console.print(f"[green]Starting server on {_host}:{_port}[/green]")
    console.print(f"[blue]API docs available at http://{_host}:{_port}/docs[/blue]")
    
    uvicorn.run(
        "llm_dungeon_master.server:app",
        host=_host,
        port=_port,
        reload=_reload
    )


# Session commands
@app.command()
def create_session(
    name: str = typer.Argument(..., help="Name of the session"),
    dm_name: str = typer.Option("Dungeon Master", help="Name of the DM")
):
    """Create a new game session."""
    with DBSession(engine) as db:
        session = Session(name=name, dm_name=dm_name)
        db.add(session)
        db.commit()
        db.refresh(session)
        
        console.print(Panel(
            f"[green]Session created successfully![/green]\n\n"
            f"ID: {session.id}\n"
            f"Name: {session.name}\n"
            f"DM: {session.dm_name}",
            title="🎲 New Session",
            border_style="green"
        ))


@app.command()
def list_sessions():
    """List all game sessions."""
    with DBSession(engine) as db:
        statement = select(Session).order_by(Session.created_at.desc())
        sessions = db.exec(statement).all()
        
        if not sessions:
            console.print("[yellow]No sessions found. Create one with:[/yellow]")
            console.print("[blue]rpg create-session \"My Adventure\"[/blue]")
            return
        
        table = Table(title="🎲 Game Sessions")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("DM", style="magenta")
        table.add_column("Status", style="yellow")
        table.add_column("Created", style="blue")
        
        for session in sessions:
            status = "Active" if session.is_active else "Inactive"
            table.add_row(
                str(session.id),
                session.name,
                session.dm_name,
                status,
                session.created_at.strftime("%Y-%m-%d %H:%M")
            )
        
        console.print(table)


# Player commands
@app.command()
def create_player(name: str = typer.Argument(..., help="Player name")):
    """Create a new player."""
    with DBSession(engine) as db:
        player = Player(name=name)
        db.add(player)
        db.commit()
        db.refresh(player)
        
        console.print(f"[green]✓ Player '{name}' created with ID: {player.id}[/green]")


@app.command()
def list_players():
    """List all players."""
    with DBSession(engine) as db:
        statement = select(Player).order_by(Player.created_at.desc())
        players = db.exec(statement).all()
        
        if not players:
            console.print("[yellow]No players found.[/yellow]")
            return
        
        table = Table(title="👥 Players")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Created", style="blue")
        
        for player in players:
            table.add_row(
                str(player.id),
                player.name,
                player.created_at.strftime("%Y-%m-%d %H:%M")
            )
        
        console.print(table)


# Character commands
@app.command()
def character_classes():
    """List all available character classes."""
    from .character_builder import CharacterBuilder
    
    with DBSession(engine) as db:
        builder = CharacterBuilder(db)
        classes = builder.list_available_classes()
        
        if not classes:
            console.print("[yellow]No character classes found[/yellow]")
            return
        
        console.print("\n[bold green]Available Character Classes:[/bold green]")
        for cls in classes:
            console.print(f"  • [cyan]{cls}[/cyan]")
        console.print()


@app.command()
def create_character(
    player_id: int = typer.Argument(..., help="Player ID"),
    name: str = typer.Argument(..., help="Character name"),
    race: str = typer.Argument(..., help="Character race"),
    char_class: str = typer.Argument(..., help="Character class"),
    strength: int = typer.Option(10, help="Strength score (8-15)"),
    dexterity: int = typer.Option(10, help="Dexterity score (8-15)"),
    constitution: int = typer.Option(10, help="Constitution score (8-15)"),
    intelligence: int = typer.Option(10, help="Intelligence score (8-15)"),
    wisdom: int = typer.Option(10, help="Wisdom score (8-15)"),
    charisma: int = typer.Option(10, help="Charisma score (8-15)"),
    background: Optional[str] = typer.Option(None, help="Character background"),
):
    """Create a new character from a class template using point buy."""
    from .character_builder import CharacterBuilder, ValidationError
    
    with DBSession(engine) as db:
        # Check if player exists
        player = db.get(Player, player_id)
        if not player:
            console.print(f"[red]Error: Player with ID {player_id} not found[/red]")
            raise typer.Exit(1)
        
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
                background=background
            )
            
            # Get character summary
            summary = builder.get_character_summary(character)
            
            # Display character sheet
            abilities_text = "\n".join([
                f"{ability.upper()}: {summary['ability_scores'][ability]['score']} "
                f"({summary['ability_scores'][ability]['modifier']:+d})"
                for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
            ])
            
            console.print(Panel(
                f"[green]Character created successfully![/green]\n\n"
                f"[bold]{character.name}[/bold]\n"
                f"Level {character.level} {character.race} {character.char_class}\n\n"
                f"[bold]Ability Scores:[/bold]\n{abilities_text}\n\n"
                f"[bold]Combat Stats:[/bold]\n"
                f"HP: {character.current_hp}/{character.max_hp}\n"
                f"AC: {character.armor_class}\n"
                f"Initiative: {character.initiative_bonus:+d}\n"
                f"Proficiency: +{character.proficiency_bonus}",
                title=f"🗡️ {character.name}",
                border_style="green"
            ))
            
        except ValidationError as e:
            console.print(f"[red]Validation Error: {e}[/red]")
            raise typer.Exit(1)
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)


@app.command()
def list_characters(player_id: Optional[int] = typer.Option(None, help="Filter by player ID")):
    """List all characters."""
    with DBSession(engine) as db:
        statement = select(Character).order_by(Character.created_at.desc())
        if player_id:
            statement = statement.where(Character.player_id == player_id)
        
        characters = db.exec(statement).all()
        
        if not characters:
            console.print("[yellow]No characters found.[/yellow]")
            return
        
        table = Table(title="🗡️ Characters")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Race", style="yellow")
        table.add_column("Class", style="magenta")
        table.add_column("Level", style="blue")
        table.add_column("HP", style="red")
        
        for char in characters:
            table.add_row(
                str(char.id),
                char.name,
                char.race,
                char.char_class,
                str(char.level),
                f"{char.current_hp}/{char.max_hp}"
            )
        
        console.print(table)


@app.command()
def show_character(character_id: int = typer.Argument(..., help="Character ID")):
    """Show detailed character information."""
    from .character_builder import CharacterBuilder
    
    with DBSession(engine) as db:
        character = db.get(Character, character_id)
        if not character:
            console.print(f"[red]Error: Character with ID {character_id} not found[/red]")
            raise typer.Exit(1)
        
        builder = CharacterBuilder(db)
        summary = builder.get_character_summary(character)
        
        # Build ability scores display
        abilities = []
        for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
            score = summary["ability_scores"][ability]["score"]
            mod = summary["ability_scores"][ability]["modifier"]
            abilities.append(f"{ability.upper()[:3]}: {score} ({mod:+d})")
        
        abilities_row1 = " | ".join(abilities[:3])
        abilities_row2 = " | ".join(abilities[3:])
        
        # Build features display
        features_text = ""
        if summary["features"]:
            features_text = "\n\n[bold]Features:[/bold]\n"
            for feat in summary["features"][:5]:  # Show first 5
                features_text += f"• {feat['name']} ({feat['source']})\n"
        
        # Build proficiencies display
        prof_text = ""
        if summary["proficiencies"]["skills"]:
            skills = ", ".join(summary["proficiencies"]["skills"])
            prof_text += f"\n\n[bold]Skills:[/bold] {skills}"
        
        # Build spell slots display
        spell_slots_text = ""
        if summary["spell_slots"]:
            spell_slots_text = "\n\n[bold]Spell Slots:[/bold]\n"
            for level, slots in summary["spell_slots"].items():
                spell_slots_text += f"Level {level}: {slots['current']}/{slots['max']} "
        
        # Create character sheet
        info = f"""[bold green]{character.name}[/bold green]
[yellow]Level {character.level} {character.race} {character.char_class}[/yellow]
{character.background or ""}

[bold]Ability Scores:[/bold]
{abilities_row1}
{abilities_row2}

[bold]Combat Stats:[/bold]
HP: {character.current_hp}/{character.max_hp} | AC: {character.armor_class} | Initiative: {character.initiative_bonus:+d}
Speed: {character.speed} ft | Proficiency: +{character.proficiency_bonus} | XP: {character.experience_points}{features_text}{prof_text}{spell_slots_text}
"""
        
        console.print(Panel(info, title="📜 Character Sheet", border_style="blue"))


@app.command()
def validate_character(character_id: int = typer.Argument(..., help="Character ID")):
    """Validate a character's stats and configuration."""
    from .character_builder import CharacterBuilder
    
    with DBSession(engine) as db:
        character = db.get(Character, character_id)
        if not character:
            console.print(f"[red]Error: Character with ID {character_id} not found[/red]")
            raise typer.Exit(1)
        
        builder = CharacterBuilder(db)
        is_valid, errors = builder.validate_character(character)
        
        if is_valid:
            console.print(f"[green]✓ Character '{character.name}' is valid![/green]")
        else:
            console.print(f"[red]✗ Character '{character.name}' has validation errors:[/red]")
            for error in errors:
                console.print(f"  • {error}")
            raise typer.Exit(1)


# Multiplayer commands
@app.command()
def show_turns(session_id: int = typer.Argument(..., help="Session ID")):
    """Show the current turn order and initiative."""
    from .turn_manager import TurnManager
    
    with DBSession(engine) as db:
        turn_manager = TurnManager(db)
        turns = turn_manager.get_turn_queue(session_id)
        
        if not turns:
            console.print("[yellow]No turns found. Start a turn queue first.[/yellow]")
            return
        
        table = Table(title="🎲 Turn Order")
        table.add_column("Order", style="cyan")
        table.add_column("Character", style="green")
        table.add_column("Initiative", style="magenta")
        table.add_column("Round", style="blue")
        table.add_column("Status", style="yellow")
        
        for turn in turns:
            status_style = "bold green" if turn.status == "active" else "dim"
            status_symbol = "→ " if turn.status == "active" else "  "
            table.add_row(
                f"{status_symbol}{turn.turn_order + 1}",
                turn.character_name,
                str(turn.initiative),
                str(turn.round_number),
                turn.status,
                style=status_style
            )
        
        console.print(table)


@app.command()
def start_turns(
    session_id: int = typer.Argument(..., help="Session ID"),
    character_ids: str = typer.Argument(..., help="Character IDs (comma-separated)")
):
    """Start a turn queue for a session."""
    from .turn_manager import TurnManager
    
    char_ids = [int(cid.strip()) for cid in character_ids.split(",")]
    
    with DBSession(engine) as db:
        turn_manager = TurnManager(db)
        turns = turn_manager.start_turn_queue(session_id, char_ids)
        
        console.print(f"[green]✓ Turn queue started for session {session_id}[/green]")
        console.print(f"  {len(turns)} characters in initiative order")
        
        current = turn_manager.get_current_turn(session_id)
        if current:
            console.print(f"  [bold]Current turn: {current.character_name}[/bold]")


@app.command()
def next_turn(session_id: int = typer.Argument(..., help="Session ID")):
    """Advance to the next turn."""
    from .turn_manager import TurnManager
    
    with DBSession(engine) as db:
        turn_manager = TurnManager(db)
        next_turn = turn_manager.advance_turn(session_id)
        
        console.print(Panel(
            f"[bold green]It's now {next_turn.character_name}'s turn![/bold green]\n\n"
            f"Round: {next_turn.round_number}\n"
            f"Initiative: {next_turn.initiative}",
            title="🎲 Turn Advanced",
            border_style="green"
        ))


@app.command()
def set_ready(
    session_id: int = typer.Argument(..., help="Session ID"),
    character_id: int = typer.Argument(..., help="Character ID"),
    ready: bool = typer.Option(True, help="Ready status")
):
    """Mark a player as ready for their turn."""
    from .turn_manager import TurnManager
    
    with DBSession(engine) as db:
        turn_manager = TurnManager(db)
        success = turn_manager.set_player_ready(session_id, character_id, ready)
        
        if success:
            status = "ready" if ready else "not ready"
            console.print(f"[green]✓ Character {character_id} marked as {status}[/green]")
        else:
            console.print(f"[red]Error: Could not update ready status[/red]")


@app.command()
def ready_check(session_id: int = typer.Argument(..., help="Session ID")):
    """Check if all players are ready."""
    from .turn_manager import TurnManager
    
    with DBSession(engine) as db:
        turn_manager = TurnManager(db)
        status = turn_manager.check_all_ready(session_id)
        
        table = Table(title="🎲 Ready Check")
        table.add_column("Character", style="green")
        table.add_column("Status", style="yellow")
        
        for player in status["players"]:
            ready_status = "✓ Ready" if player["is_ready"] else "⏳ Waiting"
            table.add_row(player["character_name"], ready_status)
        
        console.print(table)
        
        if status["all_ready"]:
            console.print("[bold green]All players are ready![/bold green]")
        else:
            console.print(f"[yellow]{status['ready_count']}/{status['total_count']} players ready[/yellow]")


@app.command()
def show_presence(session_id: int = typer.Argument(..., help="Session ID")):
    """Show player presence status."""
    from .presence_manager import PresenceManager
    
    with DBSession(engine) as db:
        presence_manager = PresenceManager(db)
        summary = presence_manager.get_presence_summary(session_id)
        
        table = Table(title="👥 Player Presence")
        table.add_column("Player", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Last Seen", style="blue")
        
        for player_info in summary["players"]:
            status = player_info["status"]
            status_emoji = {
                "online": "🟢",
                "away": "🟡",
                "offline": "🔴"
            }.get(status, "⚪")
            
            last_seen = player_info.get("last_seen")
            last_seen_str = last_seen.strftime("%H:%M:%S") if last_seen else "Never"
            
            table.add_row(
                player_info["player_name"],
                f"{status_emoji} {status}",
                last_seen_str
            )
        
        console.print(table)
        console.print(f"\n[dim]Online: {summary['online']} | "
                     f"Away: {summary['away']} | "
                     f"Offline: {summary['offline']}[/dim]")


@app.command()
def create_token(
    player_id: int = typer.Argument(..., help="Player ID"),
    session_id: int = typer.Argument(..., help="Session ID")
):
    """Create a reconnection token for a player."""
    from .reconnection_manager import ReconnectionManager
    
    with DBSession(engine) as db:
        reconnection_manager = ReconnectionManager(db)
        token = reconnection_manager.create_reconnection_token(player_id, session_id)
        
        console.print(Panel(
            f"[green]Reconnection token created![/green]\n\n"
            f"[bold]Token:[/bold] {token}\n\n"
            f"[dim]Save this token - it will only be shown once!\n"
            f"Valid for {reconnection_manager.token_expiry_hours} hours.[/dim]",
            title="🔑 Reconnection Token",
            border_style="green"
        ))


@app.command()
def reconnect(token: str = typer.Argument(..., help="Reconnection token")):
    """Reconnect to a session using a token."""
    from .reconnection_manager import ReconnectionManager
    
    with DBSession(engine) as db:
        reconnection_manager = ReconnectionManager(db)
        result = reconnection_manager.handle_reconnection(token)
        
        if not result.get("success"):
            console.print(f"[red]Error: {result.get('error')}[/red]")
            raise typer.Exit(1)
        
        console.print(Panel(
            f"[green]Reconnected successfully![/green]\n\n"
            f"Session: {result['session_name']}\n"
            f"Player: {result['player_name']}\n"
            f"Reconnected at: {result['reconnected_at'].strftime('%H:%M:%S')}",
            title="🔄 Reconnection Successful",
            border_style="green"
        ))
        
        # Show session state
        state = result.get("session_state", {})
        if state.get("character"):
            char = state["character"]
            console.print(f"\n[bold]Your Character:[/bold] {char['name']} (Level {char['level']} {char['class']})")
            console.print(f"HP: {char['current_hp']}/{char['max_hp']} | AC: {char['armor_class']}")
        
        if state.get("current_turn"):
            turn = state["current_turn"]
            console.print(f"\n[bold]Current Turn:[/bold] {turn['character_name']} (Round {turn['round_number']})")


@app.command()
def sync_check(session_id: int = typer.Argument(..., help="Session ID")):
    """Check synchronization status."""
    from .sync_manager import SyncManager
    
    with DBSession(engine) as db:
        sync_manager = SyncManager(db)
        stats = sync_manager.get_sync_stats(session_id)
        
        console.print(f"[bold]Synchronization Status for Session {session_id}[/bold]\n")
        console.print(f"Active conflicts: {stats['active_conflicts']}")
        
        if stats['active_conflicts'] > 0:
            console.print("\n[yellow]Conflicts by type:[/yellow]")
            for conflict_type, count in stats['conflicts_by_type'].items():
                console.print(f"  • {conflict_type}: {count}")


# ============================================================================
# Content Generation Commands
# ============================================================================

@app.command()
def gen_encounter(
    levels: str = typer.Argument(..., help="Party levels (comma-separated, e.g., '5,5,6,7')"),
    difficulty: str = typer.Option("medium", help="Difficulty: easy, medium, hard, deadly"),
    environment: str = typer.Option("dungeon", help="Environment: dungeon, forest, mountains, etc.")
):
    """Generate a random encounter."""
    from .content import EncounterGenerator, EncounterDifficulty, Environment
    
    # Parse party levels
    party_levels = [int(l.strip()) for l in levels.split(",")]
    
    # Parse difficulty
    try:
        diff = EncounterDifficulty(difficulty.lower())
    except ValueError:
        console.print(f"[red]Invalid difficulty: {difficulty}[/red]")
        console.print("Valid values: easy, medium, hard, deadly")
        raise typer.Exit(1)
    
    # Parse environment
    try:
        env = Environment(environment.lower())
    except ValueError:
        console.print(f"[red]Invalid environment: {environment}[/red]")
        console.print("Valid values: dungeon, forest, mountains, swamp, desert, urban, underdark, coastal")
        raise typer.Exit(1)
    
    # Generate encounter
    generator = EncounterGenerator()
    encounter = generator.generate_encounter(party_levels, diff, env)
    
    # Display
    output = generator.format_encounter(encounter)
    console.print(Panel(output, title="[bold cyan]Encounter Generated[/bold cyan]", border_style="cyan"))


@app.command()
def gen_loot(
    cr: float = typer.Argument(..., help="Challenge Rating"),
    hoard: bool = typer.Option(False, help="Generate hoard treasure instead of individual")
):
    """Generate random loot/treasure."""
    from .content import LootGenerator
    
    generator = LootGenerator()
    treasure = generator.generate_treasure(cr, hoard)
    
    # Display
    output = generator.format_treasure(treasure)
    console.print(Panel(output, title="[bold yellow]Treasure Generated[/bold yellow]", border_style="yellow"))


@app.command()
def gen_npc(
    role: Optional[str] = typer.Option(None, help="NPC role: merchant, guard, noble, etc."),
    race: Optional[str] = typer.Option(None, help="NPC race: human, elf, dwarf, etc.")
):
    """Generate a random NPC."""
    from .content import NPCGenerator, NPCRole
    
    # Parse role
    npc_role = None
    if role:
        try:
            npc_role = NPCRole(role.lower())
        except ValueError:
            console.print(f"[red]Invalid role: {role}[/red]")
            console.print("Valid values: merchant, guard, noble, commoner, priest, warrior, rogue, mage, innkeeper, blacksmith")
            raise typer.Exit(1)
    
    generator = NPCGenerator()
    npc = generator.generate_npc(npc_role, race)
    
    # Display
    output = generator.format_npc(npc)
    console.print(Panel(output, title="[bold magenta]NPC Generated[/bold magenta]", border_style="magenta"))


@app.command()
def gen_dungeon(
    theme: Optional[str] = typer.Option(None, help="Theme: crypt, mine, fortress, cave, temple, tower"),
    rooms: int = typer.Option(6, help="Number of rooms")
):
    """Generate a random dungeon."""
    from .content import LocationGenerator, DungeonTheme
    
    # Parse theme
    dungeon_theme = None
    if theme:
        try:
            dungeon_theme = DungeonTheme(theme.lower())
        except ValueError:
            console.print(f"[red]Invalid theme: {theme}[/red]")
            console.print("Valid values: crypt, mine, fortress, cave, temple, tower")
            raise typer.Exit(1)
    
    generator = LocationGenerator()
    location = generator.generate_dungeon(dungeon_theme, rooms)
    
    # Display
    output = generator.format_location(location)
    console.print(Panel(output, title="[bold red]Dungeon Generated[/bold red]", border_style="red"))


@app.command()
def gen_settlement(
    size: str = typer.Option("town", help="Size: village, town, city")
):
    """Generate a random settlement."""
    from .content import LocationGenerator
    
    if size not in ["village", "town", "city"]:
        console.print(f"[red]Invalid size: {size}[/red]")
        console.print("Valid values: village, town, city")
        raise typer.Exit(1)
    
    generator = LocationGenerator()
    location = generator.generate_settlement(size)
    
    # Display
    output = generator.format_location(location)
    console.print(Panel(output, title="[bold green]Settlement Generated[/bold green]", border_style="green"))


@app.command()
def gen_wilderness(
    terrain: str = typer.Option("forest", help="Terrain: forest, mountains, swamp")
):
    """Generate a random wilderness area."""
    from .content import LocationGenerator
    
    if terrain not in ["forest", "mountains", "swamp"]:
        console.print(f"[red]Invalid terrain: {terrain}[/red]")
        console.print("Valid values: forest, mountains, swamp")
        raise typer.Exit(1)
    
    generator = LocationGenerator()
    location = generator.generate_wilderness(terrain)
    
    # Display
    output = generator.format_location(location)
    console.print(Panel(output, title="[bold blue]Wilderness Generated[/bold blue]", border_style="blue"))


# ============================================================================
# Quality of Life Commands
# ============================================================================

@app.command()
def session_save(
    session_id: int = typer.Argument(..., help="Session ID to save"),
    note: Optional[str] = typer.Option(None, help="Optional save note")
):
    """Save session state to file."""
    from .qol import SessionStateManager
    
    with DBSession(engine) as db:
        manager = SessionStateManager(db)
        
        try:
            metadata = {"note": note} if note else None
            filepath = manager.save_session(session_id, metadata)
            console.print(f"[green]✓ Session saved to: {filepath}[/green]")
        except Exception as e:
            console.print(f"[red]Error saving session: {e}[/red]")
            raise typer.Exit(1)


@app.command()
def session_load(
    filepath: str = typer.Argument(..., help="Path to save file")
):
    """Load session state from file."""
    from pathlib import Path
    from .qol import SessionStateManager
    
    with DBSession(engine) as db:
        manager = SessionStateManager(db)
        
        try:
            snapshot = manager.load_session(Path(filepath))
            console.print(f"[green]✓ Session loaded: {snapshot.session_name}[/green]")
            console.print(f"  Session ID: {snapshot.session_id}")
            console.print(f"  Saved: {snapshot.saved_at}")
            console.print(f"  Players: {len(snapshot.players)}")
            console.print(f"  Characters: {len(snapshot.characters)}")
        except Exception as e:
            console.print(f"[red]Error loading session: {e}[/red]")
            raise typer.Exit(1)


@app.command()
def session_saves(
    session_id: Optional[int] = typer.Option(None, help="Filter by session ID")
):
    """List available save files."""
    from .qol import SessionStateManager
    
    with DBSession(engine) as db:
        manager = SessionStateManager(db)
        saves = manager.list_saves(session_id)
        
        if not saves:
            console.print("[yellow]No save files found[/yellow]")
            return
        
        console.print(f"[bold]Available Saves ({len(saves)}):[/bold]\n")
        
        for save in saves[:10]:  # Show recent 10
            info = manager.get_save_info(save)
            console.print(f"  [cyan]{info['filename']}[/cyan]")
            console.print(f"    Session: {info['session_name']} (ID: {info['session_id']})")
            console.print(f"    Saved: {info['saved_at']}")
            console.print(f"    {info['num_characters']} characters, {info['num_messages']} messages\n")


@app.command()
def history_search(
    session_id: int = typer.Argument(..., help="Session ID"),
    query: str = typer.Argument(..., help="Search query"),
    sender: Optional[str] = typer.Option(None, help="Filter by sender"),
    limit: int = typer.Option(20, help="Maximum results")
):
    """Search message history."""
    from .qol import MessageHistoryManager
    
    with DBSession(engine) as db:
        manager = MessageHistoryManager(db)
        messages = manager.search_messages(session_id, query, sender=sender, limit=limit)
        
        if not messages:
            console.print("[yellow]No messages found[/yellow]")
            return
        
        console.print(f"[bold]Found {len(messages)} messages:[/bold]\n")
        
        for msg in messages:
            timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M") if msg.timestamp else "Unknown"
            console.print(f"[cyan][{timestamp}] {msg.sender}:[/cyan]")
            console.print(f"  {msg.content[:100]}...\n")


@app.command()
def history_export(
    session_id: int = typer.Argument(..., help="Session ID"),
    output: str = typer.Argument(..., help="Output file path"),
    format: str = typer.Option("text", help="Format: text, json, markdown")
):
    """Export message history."""
    from .qol import MessageHistoryManager
    
    with DBSession(engine) as db:
        manager = MessageHistoryManager(db)
        
        try:
            content = manager.export_history(session_id, format)
            
            with open(output, 'w') as f:
                f.write(content)
            
            console.print(f"[green]✓ History exported to: {output}[/green]")
        except Exception as e:
            console.print(f"[red]Error exporting history: {e}[/red]")
            raise typer.Exit(1)


@app.command()
def stats_show(
    session_id: Optional[int] = typer.Option(None, help="Session ID"),
    character_id: Optional[int] = typer.Option(None, help="Character ID")
):
    """Show gameplay statistics."""
    from .qol import StatisticsTracker
    
    with DBSession(engine) as db:
        tracker = StatisticsTracker(db)
        
        if character_id:
            stats = tracker.get_character_stats(character_id)
            report = tracker.format_stats_report(stats)
        elif session_id:
            stats = tracker.get_session_stats(session_id)
            report = tracker.format_stats_report(stats)
        else:
            console.print("[red]Please specify --session-id or --character-id[/red]")
            raise typer.Exit(1)
        
        console.print(Panel(report, title="[bold cyan]Statistics[/bold cyan]", border_style="cyan"))


@app.command()
def stats_leaderboard(
    session_id: int = typer.Argument(..., help="Session ID"),
    metric: str = typer.Option("messages", help="Metric: messages, rolls, crits")
):
    """Show leaderboard for a metric."""
    from .qol import StatisticsTracker
    
    with DBSession(engine) as db:
        tracker = StatisticsTracker(db)
        rankings = tracker.get_leaderboard(session_id, metric)
        
        if not rankings:
            console.print("[yellow]No data for leaderboard[/yellow]")
            return
        
        table = Table(title=f"{metric.title()} Leaderboard")
        table.add_column("Rank", style="cyan")
        table.add_column("Player", style="green")
        table.add_column("Count", style="yellow")
        
        for i, entry in enumerate(rankings[:10], 1):
            table.add_row(str(i), entry['player'], str(entry['count']))
        
        console.print(table)


@app.command()
def alias_add(
    alias: str = typer.Argument(..., help="Alias shortcut"),
    command: str = typer.Argument(..., help="Full command")
):
    """Add a command alias."""
    from .qol import AliasManager
    
    manager = AliasManager()
    manager.add_alias(alias, command)
    console.print(f"[green]✓ Alias added: {alias} -> {command}[/green]")


@app.command()
def alias_remove(
    alias: str = typer.Argument(..., help="Alias to remove")
):
    """Remove a command alias."""
    from .qol import AliasManager
    
    manager = AliasManager()
    if manager.remove_alias(alias):
        console.print(f"[green]✓ Alias removed: {alias}[/green]")
    else:
        console.print(f"[yellow]Alias not found or cannot be removed: {alias}[/yellow]")


@app.command()
def alias_list(
    custom_only: bool = typer.Option(False, help="Show only custom aliases")
):
    """List all command aliases."""
    from .qol import AliasManager
    
    manager = AliasManager()
    output = manager.format_aliases()
    console.print(output)


@app.command()
def play(
    session_id: Optional[int] = typer.Option(None, help="Session ID to join"),
    color_scheme: str = typer.Option("green", help="Color scheme: green, amber, cga, c64, apple")
):
    """Start playing (interactive mode with retro interface)."""
    from rich.prompt import Prompt
    from .cli_ui import Display, TitleScreen, MainMenu, CharacterSheetScreen, CombatScreen
    from .cli_ui import DiceAnimation, CombatAnimation, CommandParser
    from .cli_ui.colors import ColorScheme
    
    # Map color scheme names to enum
    scheme_map = {
        "green": ColorScheme.GREEN_PHOSPHOR,
        "amber": ColorScheme.AMBER_MONITOR,
        "cga": ColorScheme.IBM_CGA,
        "c64": ColorScheme.COMMODORE_64,
        "apple": ColorScheme.APPLE_II,
    }
    
    scheme = scheme_map.get(color_scheme.lower(), ColorScheme.GREEN_PHOSPHOR)
    display = Display(color_scheme=scheme)
    parser = CommandParser()
    
    # Show title screen
    title_screen = TitleScreen(display)
    title_screen.show()
    
    # Main game loop
    running = True
    while running:
        # Show main menu
        main_menu = MainMenu(display)
        choice = main_menu.show()
        
        if choice == "p":
            # Play mode
            if not session_id:
                display.clear()
                display.show_info("No session selected. Create one first with: rpg create-session")
                display.pause()
                continue
            
            # TODO: Connect to WebSocket and start game session
            display.clear()
            display.show_warning("Game session mode coming soon!")
            display.console.print("\n[cyan]This will connect to the server and start playing.[/cyan]")
            display.console.print("[dim]For now, demonstrating the UI components...[/dim]\n")
            
            # Demo dice rolling
            dice = DiceAnimation(display)
            display.console.print("\n[bold]Rolling for initiative...[/bold]")
            result = dice.roll(sides=20, modifier=3, label="Initiative")
            display.pause()
            
        elif choice == "c":
            # Character management
            display.clear()
            
            with DBSession(engine) as db:
                statement = select(Character).order_by(Character.created_at.desc()).limit(10)
                characters = db.exec(statement).all()
                
                if not characters:
                    display.show_info("No characters found. Create one with: rpg create-character")
                    display.pause()
                    continue
                
                # Show character selection
                display.console.print("\n[bold]Your Characters:[/bold]\n")
                for i, char in enumerate(characters, 1):
                    display.console.print(
                        f"  [{i}] {char.name} - Level {char.level} {char.race} {char.char_class}",
                        style=display.theme.text
                    )
                display.console.print()
                
                char_choice = Prompt.ask(
                    "Select a character (number) or press Enter to go back",
                    default=""
                )
                
                if char_choice.strip() and char_choice.isdigit():
                    idx = int(char_choice) - 1
                    if 0 <= idx < len(characters):
                        # Show character sheet
                        character = characters[idx]
                        
                        # Convert character to dict for display
                        char_dict = {
                            "name": character.name,
                            "character_class": character.char_class,
                            "level": character.level,
                            "race": character.race,
                            "hp_current": character.current_hp,
                            "hp_max": character.max_hp,
                            "armor_class": character.armor_class,
                            "initiative_bonus": character.initiative_bonus,
                            "speed": character.speed,
                            "strength": character.strength,
                            "dexterity": character.dexterity,
                            "constitution": character.constitution,
                            "intelligence": character.intelligence,
                            "wisdom": character.wisdom,
                            "charisma": character.charisma,
                            "skill_proficiencies": character.skill_proficiencies or [],
                            "equipment": character.equipment or [],
                            "background": character.background,
                        }
                        
                        char_screen = CharacterSheetScreen(display)
                        char_screen.show(char_dict)
            
        elif choice == "s":
            # Sessions
            display.clear()
            
            with DBSession(engine) as db:
                statement = select(Session).order_by(Session.created_at.desc()).limit(10)
                sessions = db.exec(statement).all()
                
                if not sessions:
                    display.show_info("No sessions found. Create one with: rpg create-session")
                    display.pause()
                    continue
                
                # Show sessions
                table = Table(
                    title="🎲 Game Sessions",
                    title_style=display.theme.title,
                    border_style=display.theme.border
                )
                table.add_column("ID", style=display.theme.primary)
                table.add_column("Name", style=display.theme.text)
                table.add_column("DM", style=display.theme.secondary)
                table.add_column("Status", style=display.theme.info)
                
                for sess in sessions:
                    status = "Active" if sess.is_active else "Inactive"
                    table.add_row(str(sess.id), sess.name, sess.dm_name, status)
                
                display.print_table(table)
                display.pause()
        
        elif choice == "t":
            # Change theme
            display.clear()
            display.console.print("\n[bold]Available Color Schemes:[/bold]\n")
            display.console.print("  [1] Green Phosphor (classic terminal)")
            display.console.print("  [2] Amber Monitor (warm vintage)")
            display.console.print("  [3] IBM CGA (blue/cyan/magenta)")
            display.console.print("  [4] Commodore 64 (blue/purple)")
            display.console.print("  [5] Apple II (green)")
            display.console.print()
            
            theme_choice = Prompt.ask(
                "Select theme (1-5)",
                choices=["1", "2", "3", "4", "5"],
                default="1"
            )
            
            theme_map = {
                "1": ColorScheme.GREEN_PHOSPHOR,
                "2": ColorScheme.AMBER_MONITOR,
                "3": ColorScheme.IBM_CGA,
                "4": ColorScheme.COMMODORE_64,
                "5": ColorScheme.APPLE_II,
            }
            
            scheme = theme_map[theme_choice]
            display = Display(color_scheme=scheme)
            display.show_success("Theme changed successfully!")
            display.pause()
        
        elif choice == "q":
            # Quit
            display.clear()
            display.console.print("\n[bold]Thanks for playing![/bold]", style=display.theme.title)
            display.console.print("\n" + display.get_dragon_ascii(), style=display.theme.secondary)
            display.console.print("\n[dim]May your dice roll true![/dim]\n", style=display.theme.dim)
            running = False


if __name__ == "__main__":
    app()
