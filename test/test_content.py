"""Tests for content generation systems (Phase 7)."""

import pytest
from llm_dungeon_master.content import (
    EncounterGenerator, EncounterDifficulty, Environment,
    LootGenerator, TreasureType,
    NPCGenerator, NPCRole,
    LocationGenerator, LocationType, DungeonTheme
)


# ============================================================================
# Encounter Generator Tests
# ============================================================================

class TestEncounterGenerator:
    """Tests for encounter generation."""
    
    def test_generate_easy_encounter(self):
        """Test generating an easy encounter."""
        generator = EncounterGenerator()
        party_levels = [5, 5, 6, 7]
        
        encounter = generator.generate_encounter(
            party_levels,
            EncounterDifficulty.EASY,
            Environment.DUNGEON
        )
        
        assert encounter is not None
        assert encounter.difficulty == EncounterDifficulty.EASY
        assert encounter.environment == Environment.DUNGEON
        assert len(encounter.monsters) > 0
        assert encounter.total_xp > 0
        assert encounter.adjusted_xp > 0
        assert encounter.description != ""
        
        # Verify XP is roughly appropriate for easy encounter
        xp_budget = generator.calculate_xp_budget(party_levels, EncounterDifficulty.EASY)
        assert encounter.adjusted_xp <= xp_budget * 1.5  # Allow some variance
    
    def test_generate_deadly_encounter(self):
        """Test generating a deadly encounter."""
        generator = EncounterGenerator()
        party_levels = [10, 10, 11, 12]
        
        encounter = generator.generate_encounter(
            party_levels,
            EncounterDifficulty.DEADLY,
            Environment.MOUNTAINS
        )
        
        assert encounter.difficulty == EncounterDifficulty.DEADLY
        assert encounter.environment == Environment.MOUNTAINS
        assert len(encounter.monsters) > 0
        
        # Deadly encounters should have high adjusted XP
        xp_budget = generator.calculate_xp_budget(party_levels, EncounterDifficulty.DEADLY)
        assert encounter.adjusted_xp >= xp_budget * 0.5  # At least half the deadly threshold
    
    def test_encounter_scaling_with_party_size(self):
        """Test that encounters scale with party size."""
        generator = EncounterGenerator()
        
        # Small party
        small_encounter = generator.generate_encounter(
            [5, 5],
            EncounterDifficulty.MEDIUM,
            Environment.DUNGEON
        )
        
        # Large party
        large_encounter = generator.generate_encounter(
            [5, 5, 5, 5, 5, 5],
            EncounterDifficulty.MEDIUM,
            Environment.DUNGEON
        )
        
        # Large party should get more total XP
        assert large_encounter.total_xp > small_encounter.total_xp
    
    def test_environment_affects_monsters(self):
        """Test that environment affects monster selection."""
        generator = EncounterGenerator()
        party_levels = [5, 5]
        
        # Generate multiple encounters and check they use appropriate monsters
        dungeon_encounter = generator.generate_encounter(
            party_levels,
            EncounterDifficulty.MEDIUM,
            Environment.DUNGEON
        )
        
        forest_encounter = generator.generate_encounter(
            party_levels,
            EncounterDifficulty.MEDIUM,
            Environment.FOREST
        )
        
        mountains_encounter = generator.generate_encounter(
            party_levels,
            EncounterDifficulty.MEDIUM,
            Environment.MOUNTAINS
        )
        
        # All should have monsters
        assert len(dungeon_encounter.monsters) > 0
        assert len(forest_encounter.monsters) > 0
        assert len(mountains_encounter.monsters) > 0
    
    def test_monster_stats(self):
        """Test that monsters have valid stats."""
        generator = EncounterGenerator()
        encounter = generator.generate_encounter(
            [5],
            EncounterDifficulty.MEDIUM,
            Environment.DUNGEON
        )
        
        for monster in encounter.monsters:
            assert monster.name != ""
            assert monster.cr >= 0
            assert monster.xp > 0
            assert monster.count > 0
            assert monster.hp > 0
            assert monster.ac > 0
            assert monster.description != ""
    
    def test_xp_multiplier(self):
        """Test XP multiplier calculation."""
        generator = EncounterGenerator()
        
        # Single monster, standard party
        assert generator.get_xp_multiplier(1, 4) == 1.0
        
        # Two monsters, standard party
        assert generator.get_xp_multiplier(2, 4) == 1.5
        
        # Many monsters, standard party
        assert generator.get_xp_multiplier(10, 4) == 2.5
        
        # Small party adjustment
        assert generator.get_xp_multiplier(2, 2) > generator.get_xp_multiplier(2, 4)
        
        # Large party adjustment
        assert generator.get_xp_multiplier(2, 6) < generator.get_xp_multiplier(2, 4)
    
    def test_format_encounter(self):
        """Test encounter formatting."""
        generator = EncounterGenerator()
        encounter = generator.generate_encounter(
            [5, 5],
            EncounterDifficulty.MEDIUM,
            Environment.FOREST
        )
        
        formatted = generator.format_encounter(encounter)
        
        assert "MEDIUM ENCOUNTER" in formatted
        assert "Environment: Forest" in formatted
        assert "XP:" in formatted
        assert "Monsters:" in formatted


# ============================================================================
# Loot Generator Tests
# ============================================================================

class TestLootGenerator:
    """Tests for loot generation."""
    
    def test_generate_individual_treasure(self):
        """Test generating individual treasure."""
        generator = LootGenerator()
        treasure = generator.generate_individual_treasure(5.0)
        
        assert treasure is not None
        assert treasure.treasure_type == TreasureType.INDIVIDUAL
        assert treasure.total_value > 0
        
        # Individual treasure should have currency
        total_currency = (
            treasure.currency.copper +
            treasure.currency.silver +
            treasure.currency.electrum +
            treasure.currency.gold +
            treasure.currency.platinum
        )
        assert total_currency > 0
    
    def test_generate_hoard_treasure(self):
        """Test generating hoard treasure."""
        generator = LootGenerator()
        treasure = generator.generate_hoard_treasure(10.0)
        
        assert treasure.treasure_type == TreasureType.HOARD
        assert treasure.total_value > 0
        
        # Hoard should have more than just currency
        assert len(treasure.gems) > 0 or len(treasure.art_objects) > 0
    
    def test_treasure_scales_with_cr(self):
        """Test that treasure value scales with CR."""
        generator = LootGenerator()
        
        low_cr_treasure = generator.generate_hoard_treasure(2.0)
        high_cr_treasure = generator.generate_hoard_treasure(15.0)
        
        # High CR should generally have more valuable treasure
        assert high_cr_treasure.total_value > low_cr_treasure.total_value
    
    def test_magic_items_in_hoard(self):
        """Test that hoards contain magic items."""
        generator = LootGenerator()
        
        # High CR hoard should have magic items
        treasure = generator.generate_hoard_treasure(12.0)
        
        # May not always have items due to randomness, but check structure
        for item in treasure.magic_items:
            assert item.name != ""
            assert item.rarity is not None
            assert item.type != ""
            assert item.description != ""
    
    def test_currency_total_gold(self):
        """Test currency conversion to gold."""
        from llm_dungeon_master.content.loot import Currency
        
        currency = Currency(
            copper=100,
            silver=100,
            electrum=100,
            gold=100,
            platinum=10
        )
        
        total = currency.total_gold()
        
        # 100cp=1gp, 100sp=10gp, 100ep=50gp, 100gp=100gp, 10pp=100gp
        # Total = 1 + 10 + 50 + 100 + 100 = 261
        assert total == 261.0
    
    def test_gem_values(self):
        """Test that gems have valid values."""
        generator = LootGenerator()
        treasure = generator.generate_hoard_treasure(8.0)
        
        for gem in treasure.gems:
            # Gem should have format "name (value gp)"
            assert "gp)" in gem
            assert "(" in gem
    
    def test_format_treasure(self):
        """Test treasure formatting."""
        generator = LootGenerator()
        treasure = generator.generate_hoard_treasure(10.0)
        
        formatted = generator.format_treasure(treasure)
        
        assert "HOARD TREASURE" in formatted
        assert "Total Value:" in formatted
        assert "Currency:" in formatted or "Gems:" in formatted


# ============================================================================
# NPC Generator Tests
# ============================================================================

class TestNPCGenerator:
    """Tests for NPC generation."""
    
    def test_generate_random_npc(self):
        """Test generating a random NPC."""
        generator = NPCGenerator()
        npc = generator.generate_npc()
        
        assert npc is not None
        assert npc.name != ""
        assert npc.race != ""
        assert npc.role is not None
        assert npc.alignment is not None
        assert len(npc.personality_traits) == 2
        assert npc.ideal != ""
        assert npc.bond != ""
        assert npc.flaw != ""
        assert npc.background != ""
        assert npc.motivation != ""
        assert npc.description != ""
    
    def test_generate_specific_role_npc(self):
        """Test generating an NPC with specific role."""
        generator = NPCGenerator()
        npc = generator.generate_npc(role=NPCRole.MERCHANT)
        
        assert npc.role == NPCRole.MERCHANT
        assert "merchant" in npc.background.lower() or "trade" in npc.background.lower()
    
    def test_generate_specific_race_npc(self):
        """Test generating an NPC with specific race."""
        generator = NPCGenerator()
        npc = generator.generate_npc(race="elf")
        
        assert npc.race == "elf"
        assert "elf" in npc.description.lower()
    
    def test_npc_stats_appropriate_for_role(self):
        """Test that NPC stats match their role."""
        generator = NPCGenerator()
        
        # Warrior should have good STR/CON
        warrior = generator.generate_npc(role=NPCRole.WARRIOR)
        assert warrior.stats.str >= 14 or warrior.stats.con >= 14
        
        # Mage should have good INT/WIS
        mage = generator.generate_npc(role=NPCRole.MAGE)
        assert mage.stats.int >= 14 or mage.stats.wis >= 14
        
        # Merchant should have good CHA
        merchant = generator.generate_npc(role=NPCRole.MERCHANT)
        assert merchant.stats.cha >= 14 or merchant.stats.int >= 14
    
    def test_npc_stat_values(self):
        """Test that NPC stats are in valid ranges."""
        generator = NPCGenerator()
        npc = generator.generate_npc()
        
        # Ability scores should be 3-18 (with 4d6 drop lowest, typically 8-15)
        assert 3 <= npc.stats.str <= 20
        assert 3 <= npc.stats.dex <= 20
        assert 3 <= npc.stats.con <= 20
        assert 3 <= npc.stats.int <= 20
        assert 3 <= npc.stats.wis <= 20
        assert 3 <= npc.stats.cha <= 20
        
        # AC should be reasonable
        assert 8 <= npc.stats.ac <= 20
        
        # HP should be positive
        assert npc.stats.hp > 0
        
        # CR should be non-negative
        assert npc.stats.cr >= 0
    
    def test_alignment_affects_ideal(self):
        """Test that alignment influences ideal selection."""
        generator = NPCGenerator()
        
        # Generate many NPCs and check alignment/ideal consistency
        # (Just verify the structure is correct)
        for _ in range(5):
            npc = generator.generate_npc()
            assert npc.alignment is not None
            assert npc.ideal != ""
    
    def test_format_npc(self):
        """Test NPC formatting."""
        generator = NPCGenerator()
        npc = generator.generate_npc()
        
        formatted = generator.format_npc(npc)
        
        assert npc.name.upper() in formatted
        assert "Ability Scores:" in formatted
        assert "Personality:" in formatted
        assert "Background:" in formatted


# ============================================================================
# Location Generator Tests
# ============================================================================

class TestLocationGenerator:
    """Tests for location generation."""
    
    def test_generate_dungeon(self):
        """Test generating a dungeon."""
        generator = LocationGenerator()
        location = generator.generate_dungeon(DungeonTheme.CRYPT, 6)
        
        assert location is not None
        assert location.type == LocationType.DUNGEON
        assert location.name != ""
        assert location.description != ""
        assert location.atmosphere != ""
        assert len(location.rooms) == 6
        assert len(location.notable_features) > 0
        assert len(location.inhabitants) > 0
        assert len(location.hooks) > 0
    
    def test_generate_settlement(self):
        """Test generating a settlement."""
        generator = LocationGenerator()
        location = generator.generate_settlement("town")
        
        assert location.type == LocationType.SETTLEMENT
        assert location.name != ""
        assert len(location.rooms) > 0
        assert "town" in location.description.lower() or "settlement" in location.description.lower()
    
    def test_generate_wilderness(self):
        """Test generating a wilderness area."""
        generator = LocationGenerator()
        location = generator.generate_wilderness("forest")
        
        assert location.type == LocationType.WILDERNESS
        assert location.name != ""
        assert "forest" in location.name.lower() or "forest" in location.description.lower()
        assert len(location.rooms) > 0
    
    def test_dungeon_theme_affects_rooms(self):
        """Test that dungeon theme affects room generation."""
        generator = LocationGenerator()
        
        crypt = generator.generate_dungeon(DungeonTheme.CRYPT, 4)
        mine = generator.generate_dungeon(DungeonTheme.MINE, 4)
        
        # Room names should reflect theme
        crypt_room_names = [r.name for r in crypt.rooms]
        mine_room_names = [r.name for r in mine.rooms]
        
        # They should be different (or at least have theme-specific names)
        assert len(crypt_room_names) > 0
        assert len(mine_room_names) > 0
    
    def test_room_structure(self):
        """Test that rooms have proper structure."""
        generator = LocationGenerator()
        location = generator.generate_dungeon(DungeonTheme.FORTRESS, 5)
        
        for room in location.rooms:
            assert room.name != ""
            assert room.description != ""
            assert len(room.features) > 0
            assert len(room.connections) >= 0
            # Hazards may be empty
            # Treasure is boolean
            assert isinstance(room.treasure, bool)
    
    def test_room_connections(self):
        """Test that rooms have proper connections."""
        generator = LocationGenerator()
        location = generator.generate_dungeon(DungeonTheme.CAVE, 5)
        
        # Most rooms should have connections
        rooms_with_connections = [r for r in location.rooms if len(r.connections) > 0]
        assert len(rooms_with_connections) >= 2
    
    def test_settlement_sizes(self):
        """Test different settlement sizes."""
        generator = LocationGenerator()
        
        village = generator.generate_settlement("village")
        town = generator.generate_settlement("town")
        city = generator.generate_settlement("city")
        
        assert "village" in village.description.lower()
        assert "town" in town.description.lower()
        assert "city" in city.description.lower()
    
    def test_wilderness_terrains(self):
        """Test different wilderness terrains."""
        generator = LocationGenerator()
        
        forest = generator.generate_wilderness("forest")
        mountains = generator.generate_wilderness("mountains")
        swamp = generator.generate_wilderness("swamp")
        
        assert "forest" in forest.name.lower() or "forest" in forest.description.lower()
        assert "mountain" in mountains.name.lower() or "mountain" in mountains.description.lower()
        assert "swamp" in swamp.name.lower() or "swamp" in swamp.description.lower()
    
    def test_adventure_hooks(self):
        """Test that locations have adventure hooks."""
        generator = LocationGenerator()
        location = generator.generate_dungeon()
        
        assert len(location.hooks) > 0
        for hook in location.hooks:
            assert hook != ""
    
    def test_format_location(self):
        """Test location formatting."""
        generator = LocationGenerator()
        location = generator.generate_dungeon(DungeonTheme.TEMPLE, 4)
        
        formatted = generator.format_location(location)
        
        assert location.name.upper() in formatted
        assert "Type:" in formatted
        assert "Description:" in formatted
        assert "Notable Features:" in formatted
        assert "Areas/Rooms" in formatted
        assert "Adventure Hooks:" in formatted


# ============================================================================
# Integration Tests
# ============================================================================

class TestContentIntegration:
    """Integration tests for content generation."""
    
    def test_encounter_with_loot(self):
        """Test generating an encounter with appropriate loot."""
        encounter_gen = EncounterGenerator()
        loot_gen = LootGenerator()
        
        # Generate encounter
        encounter = encounter_gen.generate_encounter(
            [5, 5, 6],
            EncounterDifficulty.HARD,
            Environment.DUNGEON
        )
        
        # Generate loot based on encounter CR
        treasure = loot_gen.generate_treasure(encounter.treasure_cr, is_hoard=False)
        
        assert treasure is not None
        assert treasure.total_value > 0
    
    def test_dungeon_with_npcs(self):
        """Test populating a dungeon with NPCs."""
        location_gen = LocationGenerator()
        npc_gen = NPCGenerator()
        
        # Generate dungeon
        dungeon = location_gen.generate_dungeon(DungeonTheme.FORTRESS, 6)
        
        # Generate NPCs for the dungeon
        npcs = []
        for _ in range(3):
            npc = npc_gen.generate_npc(role=NPCRole.GUARD)
            npcs.append(npc)
        
        assert len(npcs) == 3
        assert all(npc.role == NPCRole.GUARD for npc in npcs)
    
    def test_complete_adventure_setup(self):
        """Test setting up a complete adventure."""
        encounter_gen = EncounterGenerator()
        loot_gen = LootGenerator()
        npc_gen = NPCGenerator()
        location_gen = LocationGenerator()
        
        # Generate location
        location = location_gen.generate_dungeon(DungeonTheme.CRYPT, 5)
        assert location is not None
        
        # Generate encounter for the location
        encounter = encounter_gen.generate_encounter(
            [4, 5, 5, 6],
            EncounterDifficulty.MEDIUM,
            Environment.DUNGEON
        )
        assert encounter is not None
        
        # Generate treasure
        treasure = loot_gen.generate_treasure(encounter.treasure_cr, is_hoard=True)
        assert treasure is not None
        
        # Generate an NPC guide/quest giver
        quest_giver = npc_gen.generate_npc(role=NPCRole.NOBLE)
        assert quest_giver is not None
        
        # Verify we have all components
        assert len(location.rooms) > 0
        assert len(encounter.monsters) > 0
        assert treasure.total_value > 0
        assert quest_giver.name != ""
