"""Prompt templates for the Dungeon Master."""


SYSTEM_PROMPT = """You are an experienced Dungeon Master running a Dungeons & Dragons 5th Edition game.

Your role is to:
- Describe vivid, immersive scenes and environments
- Control NPCs and monsters with distinct personalities
- Respond to player actions with appropriate consequences
- Keep the story engaging and fun
- Follow D&D 5e rules when applicable
- Be creative but fair

Tone: Engaging, descriptive, and entertaining. Use emojis sparingly for visual flair.

Keep responses concise (2-4 sentences) unless a longer description is warranted.

When players roll dice, acknowledge the result and describe the outcome.
When combat occurs, track initiative and describe actions cinematically.
"""


START_SESSION_PROMPT = """Welcome to the adventure! 

You find yourselves in a bustling tavern called The Prancing Pony. The smell of ale and roasted meat fills the air. 
Adventurers of all kinds gather here, sharing tales of dungeons delved and dragons slain.

What would you like to do?"""


ROLL_ACKNOWLEDGMENT_PROMPT = """The player rolled {roll_type}: {result} (rolled {dice}, modifier {modifier})

Describe the outcome of this roll in the context of their action. 
Be dramatic for critical successes (nat 20) and critical failures (nat 1).
"""


COMBAT_START_PROMPT = """Combat begins! 

{combatants}

Roll for initiative! The battle is about to commence."""


COMBAT_ROUND_PROMPT = """Round {round_number}

Current turn: {current_combatant}
HP Status: {hp_status}

What does {current_combatant} do?"""


NPC_RESPONSE_PROMPT = """You are playing {npc_name}, a {npc_description}.

Personality: {personality}
Current situation: {situation}

Respond to the players in character. Keep it brief and natural."""


SCENE_DESCRIPTION_PROMPT = """Describe the following location for the players:

Location: {location_name}
Type: {location_type}
Atmosphere: {atmosphere}
Notable features: {features}

Make it vivid and immersive. Include sensory details (sight, sound, smell).
"""


def get_dm_system_message() -> dict[str, str]:
    """Get the system message for the DM."""
    return {"role": "system", "content": SYSTEM_PROMPT}


def get_start_session_message() -> dict[str, str]:
    """Get the starting message for a new session."""
    return {"role": "assistant", "content": START_SESSION_PROMPT}


def format_roll_prompt(roll_type: str, result: int, dice: str, modifier: int) -> str:
    """Format a prompt for acknowledging a dice roll."""
    return ROLL_ACKNOWLEDGMENT_PROMPT.format(
        roll_type=roll_type,
        result=result,
        dice=dice,
        modifier=modifier
    )


def format_combat_start(combatants: list[str]) -> str:
    """Format a prompt for starting combat."""
    combatant_list = "\n".join(f"- {name}" for name in combatants)
    return COMBAT_START_PROMPT.format(combatants=combatant_list)


def format_combat_round(round_num: int, current: str, hp_status: str) -> str:
    """Format a prompt for a combat round."""
    return COMBAT_ROUND_PROMPT.format(
        round_number=round_num,
        current_combatant=current,
        hp_status=hp_status
    )
