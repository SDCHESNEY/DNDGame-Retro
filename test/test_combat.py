"""Tests for combat management system."""

import pytest
from sqlmodel import create_engine, SQLModel, Session as DBSession
from llm_dungeon_master.models import Character, Player, Session
from llm_dungeon_master.rules.combat import CombatManager, AdvantageType


@pytest.fixture
def db():
    """Create an in-memory database for testing."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with DBSession(engine) as session:
        yield session


@pytest.fixture
def test_characters(db):
    """Create test characters."""
    # Create player
    player = Player(name="Test Player")
    db.add(player)
    db.commit()
    db.refresh(player)
    
    # Create characters
    fighter = Character(
        player_id=player.id,
        name="Fighter",
        race="Human",
        char_class="Fighter",
        level=5,
        strength=16,
        dexterity=14,
        constitution=15,
        max_hp=40,
        current_hp=40,
        armor_class=18
    )
    
    wizard = Character(
        player_id=player.id,
        name="Wizard",
        race="Elf",
        char_class="Wizard",
        level=5,
        strength=8,
        dexterity=14,
        constitution=12,
        intelligence=18,
        max_hp=25,
        current_hp=25,
        armor_class=12
    )
    
    goblin = Character(
        player_id=player.id,
        name="Goblin",
        race="Goblin",
        char_class="Monster",
        level=1,
        strength=8,
        dexterity=14,
        constitution=10,
        max_hp=7,
        current_hp=7,
        armor_class=15
    )
    
    db.add(fighter)
    db.add(wizard)
    db.add(goblin)
    db.commit()
    db.refresh(fighter)
    db.refresh(wizard)
    db.refresh(goblin)
    
    return fighter, wizard, goblin


@pytest.fixture
def test_session(db):
    """Create a test session."""
    session = Session(name="Test Combat Session")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


class TestCombatManager:
    """Test combat manager functionality."""
    
    def test_start_combat(self, db, test_session, test_characters):
        """Test starting a combat encounter."""
        fighter, wizard, goblin = test_characters
        combat_manager = CombatManager()
        
        combat_state = combat_manager.start_combat(
            db, 
            test_session.id, 
            [fighter.id, wizard.id, goblin.id]
        )
        
        assert combat_state.session_id == test_session.id
        assert combat_state.round_number == 1
        assert len(combat_state.combatants) == 3
        assert len(combat_state.combat_log) > 0
        
        # Check combatants are sorted by initiative
        initiatives = [c.initiative for c in combat_state.combatants]
        assert initiatives == sorted(initiatives, reverse=True)
    
    def test_get_combat(self, db, test_session, test_characters):
        """Test getting active combat."""
        fighter, wizard, goblin = test_characters
        combat_manager = CombatManager()
        
        # Start combat
        combat_state = combat_manager.start_combat(
            db, 
            test_session.id, 
            [fighter.id, wizard.id]
        )
        
        # Get combat
        retrieved = combat_manager.get_combat(test_session.id)
        assert retrieved is not None
        assert retrieved.session_id == test_session.id
        assert len(retrieved.combatants) == 2
    
    def test_next_turn(self, db, test_session, test_characters):
        """Test advancing to next turn."""
        fighter, wizard, goblin = test_characters
        combat_manager = CombatManager()
        
        combat_state = combat_manager.start_combat(
            db, 
            test_session.id, 
            [fighter.id, wizard.id]
        )
        
        initial_index = combat_state.current_turn_index
        initial_round = combat_state.round_number
        
        # Advance turn
        combat_state = combat_manager.next_turn(test_session.id)
        
        assert combat_state.current_turn_index != initial_index or combat_state.round_number > initial_round
    
    def test_round_progression(self, db, test_session, test_characters):
        """Test that rounds progress correctly."""
        fighter, wizard, goblin = test_characters
        combat_manager = CombatManager()
        
        combat_state = combat_manager.start_combat(
            db, 
            test_session.id, 
            [fighter.id, wizard.id]
        )
        
        initial_round = combat_state.round_number
        
        # Advance through all combatants
        for _ in range(len(combat_state.combatants)):
            combat_state = combat_manager.next_turn(test_session.id)
        
        # Should be in next round
        assert combat_state.round_number == initial_round + 1
    
    def test_resolve_attack_hit(self, db, test_session, test_characters):
        """Test resolving an attack that hits."""
        fighter, wizard, goblin = test_characters
        combat_manager = CombatManager()
        
        combat_state = combat_manager.start_combat(
            db, 
            test_session.id, 
            [fighter.id, goblin.id]
        )
        
        # Fighter attacks goblin with high bonus (should usually hit AC 15)
        initial_hp = None
        for combatant in combat_state.combatants:
            if combatant.character_id == goblin.id:
                initial_hp = combatant.current_hp
                break
        
        result = combat_manager.resolve_attack(
            test_session.id,
            fighter.id,
            goblin.id,
            attack_bonus=8,  # High bonus
            damage_formula="1d8+3",
            advantage=AdvantageType.NORMAL
        )
        
        assert result is not None
        # Check if attack hit (might miss on natural 1)
        if result.hit:
            assert result.damage > 0
            # Verify HP was reduced
            combat_state = combat_manager.get_combat(test_session.id)
            for combatant in combat_state.combatants:
                if combatant.character_id == goblin.id:
                    assert combatant.current_hp < initial_hp
    
    def test_resolve_attack_miss(self, db, test_session, test_characters):
        """Test resolving an attack that misses."""
        fighter, wizard, goblin = test_characters
        combat_manager = CombatManager()
        
        combat_state = combat_manager.start_combat(
            db, 
            test_session.id, 
            [fighter.id, wizard.id]
        )
        
        # Attack with very low bonus against wizard's AC (should miss often)
        # We can't guarantee a miss, but we test the logic
        results = []
        for _ in range(10):
            # Restart combat each time
            combat_manager = CombatManager()
            combat_manager.start_combat(db, test_session.id, [fighter.id, wizard.id])
            result = combat_manager.resolve_attack(
                test_session.id,
                fighter.id,
                wizard.id,
                attack_bonus=-5,  # Very low bonus
                damage_formula="1d4",
                advantage=AdvantageType.DISADVANTAGE
            )
            results.append(result)
        
        # Should have at least some misses
        misses = [r for r in results if not r.hit]
        assert len(misses) > 0
    
    def test_apply_damage(self, db, test_session, test_characters):
        """Test applying damage directly."""
        fighter, wizard, goblin = test_characters
        combat_manager = CombatManager()
        
        combat_state = combat_manager.start_combat(
            db, 
            test_session.id, 
            [goblin.id]
        )
        
        initial_hp = combat_state.combatants[0].current_hp
        
        # Apply damage
        is_alive = combat_manager.apply_damage(test_session.id, goblin.id, 5)
        
        combat_state = combat_manager.get_combat(test_session.id)
        assert combat_state.combatants[0].current_hp == initial_hp - 5
        assert is_alive  # Goblin should still be alive
    
    def test_defeat_combatant(self, db, test_session, test_characters):
        """Test defeating a combatant."""
        fighter, wizard, goblin = test_characters
        combat_manager = CombatManager()
        
        combat_state = combat_manager.start_combat(
            db, 
            test_session.id, 
            [goblin.id]
        )
        
        # Apply enough damage to defeat goblin
        is_alive = combat_manager.apply_damage(test_session.id, goblin.id, 100)
        
        assert not is_alive
        
        combat_state = combat_manager.get_combat(test_session.id)
        assert combat_state.combatants[0].current_hp == 0
        assert not combat_state.combatants[0].is_alive
    
    def test_apply_healing(self, db, test_session, test_characters):
        """Test applying healing."""
        fighter, wizard, goblin = test_characters
        combat_manager = CombatManager()
        
        combat_state = combat_manager.start_combat(
            db, 
            test_session.id, 
            [fighter.id]
        )
        
        # Damage fighter first
        combat_manager.apply_damage(test_session.id, fighter.id, 10)
        
        combat_state = combat_manager.get_combat(test_session.id)
        damaged_hp = combat_state.combatants[0].current_hp
        
        # Heal fighter
        success = combat_manager.apply_healing(test_session.id, fighter.id, 5)
        
        assert success
        combat_state = combat_manager.get_combat(test_session.id)
        assert combat_state.combatants[0].current_hp == damaged_hp + 5
    
    def test_healing_cap_at_max_hp(self, db, test_session, test_characters):
        """Test that healing doesn't exceed max HP."""
        fighter, wizard, goblin = test_characters
        combat_manager = CombatManager()
        
        combat_state = combat_manager.start_combat(
            db, 
            test_session.id, 
            [fighter.id]
        )
        
        max_hp = combat_state.combatants[0].max_hp
        
        # Try to overheal
        combat_manager.apply_healing(test_session.id, fighter.id, 100)
        
        combat_state = combat_manager.get_combat(test_session.id)
        assert combat_state.combatants[0].current_hp == max_hp
    
    def test_combat_ends_when_one_left(self, db, test_session, test_characters):
        """Test that combat ends when only one combatant remains."""
        fighter, wizard, goblin = test_characters
        combat_manager = CombatManager()
        
        combat_state = combat_manager.start_combat(
            db, 
            test_session.id, 
            [fighter.id, goblin.id]
        )
        
        # Defeat goblin
        combat_manager.apply_damage(test_session.id, goblin.id, 100)
        
        # Advance turn
        combat_state = combat_manager.next_turn(test_session.id)
        
        # Combat should be over (or None if already ended)
        if combat_state:
            assert combat_state.is_combat_over
        else:
            # Combat was already removed
            assert combat_manager.get_combat(test_session.id) is None
    
    def test_end_combat(self, db, test_session, test_characters):
        """Test manually ending combat."""
        fighter, wizard, goblin = test_characters
        combat_manager = CombatManager()
        
        combat_manager.start_combat(
            db, 
            test_session.id, 
            [fighter.id, wizard.id]
        )
        
        # End combat
        success = combat_manager.end_combat(test_session.id)
        
        assert success
        assert combat_manager.get_combat(test_session.id) is None
    
    def test_get_initiative_order(self, db, test_session, test_characters):
        """Test getting initiative order."""
        fighter, wizard, goblin = test_characters
        combat_manager = CombatManager()
        
        combat_manager.start_combat(
            db, 
            test_session.id, 
            [fighter.id, wizard.id, goblin.id]
        )
        
        order = combat_manager.get_initiative_order(test_session.id)
        
        assert len(order) == 3
        assert all("name" in entry for entry in order)
        assert all("initiative" in entry for entry in order)
        assert all("hp" in entry for entry in order)
        assert all("ac" in entry for entry in order)
        assert all("is_current" in entry for entry in order)
        assert all("is_alive" in entry for entry in order)
        
        # First entry should be current combatant
        assert order[0]["is_current"]
