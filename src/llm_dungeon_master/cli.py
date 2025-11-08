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
def create_character(
    player_id: int = typer.Argument(..., help="Player ID"),
    name: str = typer.Argument(..., help="Character name"),
    race: str = typer.Option("Human", help="Character race"),
    char_class: str = typer.Option("Fighter", help="Character class"),
):
    """Create a new character."""
    with DBSession(engine) as db:
        # Check if player exists
        player = db.get(Player, player_id)
        if not player:
            console.print(f"[red]Error: Player with ID {player_id} not found[/red]")
            raise typer.Exit(1)
        
        character = Character(
            player_id=player_id,
            name=name,
            race=race,
            char_class=char_class,
            level=1,
            max_hp=10,
            current_hp=10,
            armor_class=10
        )
        db.add(character)
        db.commit()
        db.refresh(character)
        
        console.print(Panel(
            f"[green]Character created successfully![/green]\n\n"
            f"Name: {character.name}\n"
            f"Race: {character.race}\n"
            f"Class: {character.char_class}\n"
            f"Level: {character.level}\n"
            f"HP: {character.current_hp}/{character.max_hp}\n"
            f"AC: {character.armor_class}",
            title=f"🗡️ {character.name}",
            border_style="green"
        ))


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
    with DBSession(engine) as db:
        character = db.get(Character, character_id)
        if not character:
            console.print(f"[red]Error: Character with ID {character_id} not found[/red]")
            raise typer.Exit(1)
        
        # Create character sheet
        info = f"""[bold green]{character.name}[/bold green]
[yellow]Level {character.level} {character.race} {character.char_class}[/yellow]

[bold]Ability Scores:[/bold]
STR: {character.strength} | DEX: {character.dexterity} | CON: {character.constitution}
INT: {character.intelligence} | WIS: {character.wisdom} | CHA: {character.charisma}

[bold]Combat Stats:[/bold]
HP: {character.current_hp}/{character.max_hp} | AC: {character.armor_class}
"""
        
        console.print(Panel(info, title="📜 Character Sheet", border_style="blue"))


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
