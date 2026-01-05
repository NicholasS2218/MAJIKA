import math

# ============================================================================
# SIMULATION FUNCTIONS
# ============================================================================

def get_growth_rate(level):
    """
    Get the growth rate multiplier based on level.
    - Levels 1-20: 200% (2.0x)
    - Levels 21-50: 70% (0.7x)
    - Levels 51-75: 20% (0.2x)
    - Levels 76-100: 10% (0.1x)
    """
    if level <= 20:
        return 2
    elif level <= 50:
        return 0.7
    elif level <= 75:
        return 0.2
    else:
        return 0.1


def simulate_generic_levelup(start_level, end_level, initial_hp, initial_mp, 
                             initial_vit, initial_mind, hp_formula, mp_formula):
    """
    Simulate level ups where VIT and MIND increase by 1 every level.
    Uses scaled growth rates based on level ranges.
    """
    maxHP = initial_hp
    maxMP = initial_mp
    vit = initial_vit
    mind = initial_mind
    
    for level in range(start_level + 1, end_level + 1):
        growth_rate = get_growth_rate(level)
        
        # 3% growth scaled by growth rate
        tallyHP = math.ceil(maxHP * 0.03 * growth_rate)
        tallyMP = math.ceil(maxMP * 0.03 * growth_rate)
        maxHP += tallyHP
        maxMP += tallyMP
        
        # Stat increases
        vit += 1
        mind += 1
        
        # Stat bonuses scaled by growth rate
        hp_bonus = int(hp_formula(vit) * growth_rate)
        mp_bonus = int(mp_formula(mind) * growth_rate)
        maxHP += hp_bonus
        maxMP += mp_bonus
    
    return maxHP, maxMP, vit, mind


def simulate_progression_levelup(start_level, end_level, initial_hp, initial_mp,
                                 initial_vit, initial_mind, stat_progression, 
                                 hp_formula, mp_formula):
    """
    Simulate level ups based on a stat progression dictionary.
    Uses scaled growth rates based on level ranges.
    """
    maxHP = initial_hp
    maxMP = initial_mp
    vit = initial_vit
    mind = initial_mind
    
    for level in range(start_level + 1, end_level + 1):
        growth_rate = get_growth_rate(level)
        
        # 3% growth scaled by growth rate
        tallyHP = math.ceil(maxHP * 0.03 * growth_rate)
        tallyMP = math.ceil(maxMP * 0.03 * growth_rate)
        maxHP += tallyHP
        maxMP += tallyMP
        
        # Get stat gains for this level (cycles every 10 levels)
        lvl_key = str((level - 1) % 10 + 1)
        gains = stat_progression.get(lvl_key, {})
        
        # Apply stat gains scaled by growth rate
        if "vit" in gains:
            vit += gains["vit"]
            hp_bonus = int(hp_formula(vit) * growth_rate)
            maxHP += hp_bonus
        
        if "mind" in gains:
            mind += gains["mind"]
            mp_bonus = int(mp_formula(mind) * growth_rate)
            maxMP += mp_bonus
    
    return maxHP, maxMP, vit, mind


# ============================================================================
# FORMULA FINDER
# ============================================================================

def find_formula(target_level, target_vit, target_mind, target_hp, target_mp,
                initial_hp=20, initial_mp=10, initial_vit=1, initial_mind=1):
    """
    Find formulas that hit target HP and MP at a specific level.
    Tests power-based and linear formulas with various multipliers.
    """
    powers_to_test = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
    best_result = None
    best_diff = float('inf')
    
    print("🔍 Searching through formula combinations...")
    
    for hp_power in powers_to_test:
        for mp_power in powers_to_test:
            # Search for multipliers (wider range)
            for hp_mult in [x * 0.5 for x in range(1, 200)]:
                for mp_mult in [x * 0.5 for x in range(1, 200)]:
                    hp_formula = lambda v: hp_mult * (v ** hp_power)
                    mp_formula = lambda m: mp_mult * (m ** mp_power)
                    
                    hp, mp, vit, mind = simulate_generic_levelup(
                        1, target_level, initial_hp, initial_mp, 
                        initial_vit, initial_mind, hp_formula, mp_formula
                    )
                    
                    hp_diff = abs(hp - target_hp)
                    mp_diff = abs(mp - target_mp)
                    total_diff = hp_diff + mp_diff
                    
                    if total_diff < best_diff:
                        best_diff = total_diff
                        best_result = {
                            'hp_mult': hp_mult,
                            'hp_power': hp_power,
                            'mp_mult': mp_mult,
                            'mp_power': mp_power,
                            'hp': hp,
                            'mp': mp,
                            'vit': vit,
                            'mind': mind,
                            'diff': total_diff
                        }
                        
                        if total_diff < 5:
                            print(f"   Found good match: HP={hp}, MP={mp} (diff: {total_diff:.1f})")
                            return (hp_mult, hp_power, mp_mult, mp_power)
    
    print(f"   Best match found: HP={best_result['hp']}, MP={best_result['mp']} (diff: {best_result['diff']:.1f})")
    return (best_result['hp_mult'], best_result['hp_power'], 
            best_result['mp_mult'], best_result['mp_power'])


# ============================================================================
# DISPLAY FUNCTIONS
# ============================================================================

def print_generic_progression(end_level, hp_mult, hp_power, mp_mult, mp_power,
                              initial_hp=20, initial_mp=10, initial_vit=1, initial_mind=1):
    """
    Print detailed progression for generic +1 VIT/MIND per level.
    """
    hp_formula = lambda v: hp_mult * (v ** hp_power)
    mp_formula = lambda m: mp_mult * (m ** mp_power)
    
    maxHP = initial_hp
    maxMP = initial_mp
    vit = initial_vit
    mind = initial_mind
    
    print(f"\n{'='*90}")
    print(f"📊 GENERIC PROGRESSION: Level 1 → {end_level}")
    print(f"{'='*90}")
    print(f"Starting: HP={maxHP}, MP={maxMP}, VIT={vit}, MIND={mind}")
    print(f"Formula: HP = {hp_mult:.1f} × (VIT^{hp_power}), MP = {mp_mult:.1f} × (MIND^{mp_power})")
    print(f"Growth: Lv1-50 (100%), Lv51-75 (50%), Lv76-100 (20%)")
    print(f"Gains: +1 VIT and +1 MIND every level\n")
    print("-" * 90)
    
    for level in range(2, end_level + 1):
        growth_rate = get_growth_rate(level)
        
        tallyHP = math.ceil(maxHP * 0.03 * growth_rate)
        tallyMP = math.ceil(maxMP * 0.03 * growth_rate)
        maxHP += tallyHP
        maxMP += tallyMP
        
        vit += 1
        mind += 1
        
        hp_bonus = int(hp_formula(vit) * growth_rate)
        mp_bonus = int(mp_formula(mind) * growth_rate)
        
        maxHP += hp_bonus
        maxMP += mp_bonus
        tallyHP += hp_bonus
        tallyMP += mp_bonus
        
        # Print milestones
        if level in [5, 10, 13, 25, 50, 51, 75, 76, 100] or level == end_level:
            rate_info = f" [{int(growth_rate*100)}%]"
            print(f"Lv{level:3d}: HP={maxHP:5d} (+{tallyHP:4d}) | MP={maxMP:4d} (+{tallyMP:3d}) | VIT={vit:3d} | MIND={mind:3d}{rate_info}")
    
    print("-" * 90)
    print(f"Final: HP={maxHP}, MP={maxMP}, VIT={vit}, MIND={mind}\n")
    
    return maxHP, maxMP, vit, mind


def print_progression_based(end_level, stat_progression, hp_mult, hp_power, mp_mult, mp_power,
                            initial_hp=20, initial_mp=10, initial_vit=1, initial_mind=1):
    """
    Print detailed progression based on stat progression dictionary.
    """
    hp_formula = lambda v: hp_mult * (v ** hp_power)
    mp_formula = lambda m: mp_mult * (m ** mp_power)
    
    maxHP = initial_hp
    maxMP = initial_mp
    vit = initial_vit
    mind = initial_mind
    
    print(f"\n{'='*90}")
    print(f"📊 PROGRESSION-BASED: Level 1 → {end_level}")
    print(f"{'='*90}")
    print(f"Starting: HP={maxHP}, MP={maxMP}, VIT={vit}, MIND={mind}")
    print(f"Formula: HP = {hp_mult:.1f} × (VIT^{hp_power}), MP = {mp_mult:.1f} × (MIND^{mp_power})")
    print(f"Growth: Lv1-50 (100%), Lv51-75 (50%), Lv76-100 (20%)")
    print(f"Using custom stat progression pattern\n")
    print("-" * 90)
    
    for level in range(2, end_level + 1):
        growth_rate = get_growth_rate(level)
        
        tallyHP = math.ceil(maxHP * 0.03 * growth_rate)
        tallyMP = math.ceil(maxMP * 0.03 * growth_rate)
        maxHP += tallyHP
        maxMP += tallyMP
        
        lvl_key = str((level - 1) % 10 + 1)
        gains = stat_progression.get(lvl_key, {})
        
        vit_gain = 0
        mind_gain = 0
        
        if "vit" in gains:
            vit += gains["vit"]
            vit_gain = gains["vit"]
            hp_bonus = int(hp_formula(vit) * growth_rate)
            maxHP += hp_bonus
            tallyHP += hp_bonus
        
        if "mind" in gains:
            mind += gains["mind"]
            mind_gain = gains["mind"]
            mp_bonus = int(mp_formula(mind) * growth_rate)
            maxMP += mp_bonus
            tallyMP += mp_bonus
        
        # Print milestones
        if level in [5, 10, 13, 25, 50, 51, 75, 76, 100] or level == end_level:
            vit_info = f" (+{vit_gain})" if vit_gain > 0 else ""
            mind_info = f" (+{mind_gain})" if mind_gain > 0 else ""
            rate_info = f" [{int(growth_rate*100)}%]"
            print(f"Lv{level:3d}: HP={maxHP:5d} (+{tallyHP:4d}) | MP={maxMP:4d} (+{tallyMP:3d}) | VIT={vit:3d}{vit_info} | MIND={mind:3d}{mind_info}{rate_info}")
    
    print("-" * 90)
    print(f"Final: HP={maxHP}, MP={maxMP}, VIT={vit}, MIND={mind}\n")
    
    return maxHP, maxMP, vit, mind


# ============================================================================
# MAIN
# ============================================================================

def main():
    """
    Main function to run simulations.
    """
    print("=" * 90)
    print("🎯 LEVEL UP SIMULATOR - EXPONENTIAL WITH DIMINISHING RETURNS")
    print("=" * 90)
    print("\nGoal: Level 100 with VIT 99 & MIND 99 → HP ≈ 999, MP ≈ 499")
    print("Growth Rates: Lv1-50 (100%), Lv51-75 (50%), Lv76-100 (20%)\n")
    
    # Find optimal formulas
    # hp_mult, hp_power, mp_mult, mp_power = find_formula(
    #     target_level=100,
    #     target_vit=99,
    #     target_mind=99,
    #     target_hp=999,
    #     target_mp=499
    # )
    
    hp_mult = 1.0
    hp_power = 0.5
    mp_mult = 0.7
    mp_power = 0.5

    print("\n" + "=" * 90)
    print("✅ FOUND FORMULAS:")
    print("=" * 90)
    print(f"HP bonus = {hp_mult:.1f} × (vit^{hp_power}) × growth_rate")
    print(f"MP bonus = {mp_mult:.1f} × (mind^{mp_power}) × growth_rate")
    print("\nPython code:")
    print(f"  growth_rate = 1.0 if level <= 50 else 0.5 if level <= 75 else 0.2")
    print(f"  hp_bonus = int({hp_mult:.1f} * (vit ** {hp_power}) * growth_rate)")
    print(f"  mp_bonus = int({mp_mult:.1f} * (mind ** {mp_power}) * growth_rate)")
    
    # Test with generic progression
    hp_10, mp_10, vit_10, mind_10 = print_generic_progression(10, hp_mult, hp_power, mp_mult, mp_power)
    hp_20, mp_20, vit_20, mind_20 = print_generic_progression(20, hp_mult, hp_power, mp_mult, mp_power)
    hp_50, mp_50, vit_50, mind_50 = print_generic_progression(50, hp_mult, hp_power, mp_mult, mp_power)
    hp_75, mp_75, vit_75, mind_75 = print_generic_progression(75, hp_mult, hp_power, mp_mult, mp_power)
    hp_100, mp_100, vit_100, mind_100 = print_generic_progression(100, hp_mult, hp_power, mp_mult, mp_power)
    
    # Test with Aemelia's progression
    member_progress = {
        "1" : {"vit": 1, "st": 1, "dex": 1}, 
        "2" : {"st" : 1, "dex": 1}, 
        "3" : {"vit" : 1, "mind": 1, "mag": 1},
        "4" : {"vit" : 1, "agi": 1},
        "5" : {"vit": 1, "st": 1, "dex": 1},
        "6" : {"st" : 1, "agi": 1},
        "7" : {"st" :1, "dex" : 1, "mag": 1},
        "8" : {"vit": 1, "arc": 1},
        "9" : {"vit": 1, "st": 1, "dex": 1},
        "10" : {"arc": 1, "agi": 1}
    }
    
    print("\n" + "=" * 90)
    print("🧪 TEST: Aemelia's Custom Stat Progression")
    print("=" * 90)
    npc_lvl = 13
    npc_hp, npc_mp, npc_vit, npc_mind = print_progression_based(
        npc_lvl, member_progress, hp_mult, hp_power, mp_mult, mp_power
    )
    
    # Summary
    print("\n" + "=" * 90)
    print("📊 SUMMARY")
    print("=" * 90)
    print("\nGeneric (+1 VIT/MIND per level):")
    print(f"  Level 10:  HP={hp_10:,}, MP={mp_10:,}, VIT={vit_10}, MIND={mind_10}")
    print(f"  Level 20:  HP={hp_20:,}, MP={mp_20:,}, VIT={vit_20}, MIND={mind_20}")
    print(f"  Level 50:  HP={hp_50:,}, MP={mp_50:,}, VIT={vit_50}, MIND={mind_50}")
    print(f"  Level 75:  HP={hp_75:,}, MP={mp_75:,}, VIT={vit_75}, MIND={mind_75}")
    print(f"  Level 100: HP={hp_100:,}, MP={mp_100:,}, VIT={vit_100}, MIND={mind_100}")
    
    print("\nCustom progression:")
    print(f"  Level {npc_lvl}:  HP={npc_hp:,}, MP={npc_mp:,}, VIT={npc_vit}, MIND={npc_mind}")
    print("=" * 90)


if __name__ == "__main__":
    main()