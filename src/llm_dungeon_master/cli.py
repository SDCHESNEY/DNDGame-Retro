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


@app.command()
def play(session_id: Optional[int] = typer.Option(None, help="Session ID to join")):
    """Start playing (interactive mode)."""
    console.print(Panel(
        "[bold green]🎲 Welcome to LLM Dungeon Master! 🎲[/bold green]\n\n"
        "[yellow]Interactive play mode coming soon![/yellow]\n\n"
        "For now, use these commands:\n"
        "  • [cyan]rpg create-session \"My Game\"[/cyan] - Start a new game\n"
        "  • [cyan]rpg list-sessions[/cyan] - See all games\n"
        "  • [cyan]rpg serve[/cyan] - Start the API server\n",
        border_style="green"
    ))


if __name__ == "__main__":
    app()
