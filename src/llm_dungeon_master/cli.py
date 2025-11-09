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
