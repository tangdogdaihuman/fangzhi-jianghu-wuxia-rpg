"""wuxia_integration.py - Quest tracking and AI NPC integration"""
import json, os, sys

def init_quest_state(state):
    if not hasattr(state, 'quest_state'):
        state.quest_state = {
            'main_active': 'main_001',
            'main_completed': [],
            'side_active': [],
            'side_completed': [],
            'daily_progress': {},
            'achievements_unlocked': [],
            'stats': {'practice_count': 0, 'talk_count': 0, 'unique_locations': [], 'breakthroughs': 0},
        }

def get_available_quests(state):
    from wuxia_quests import MAIN_QUESTS, SIDE_QUESTS
    init_quest_state(state)
    qs = state.quest_state
    level = state.realm_index * 10 + 1
    available = {'main': [], 'side': [], 'daily': []}
    for q in MAIN_QUESTS:
        if q['id'] == qs['main_active'] and q['level_req'] <= level:
            available['main'].append(q)
    for q in SIDE_QUESTS:
        if q['level_req'] <= level:
            available['side'].append(q)
    return available

def update_quest_progress(state, action_type, target='', location=''):
    from wuxia_quests import MAIN_QUESTS, SIDE_QUESTS, ACHIEVEMENTS
    init_quest_state(state)
    qs = state.quest_state
    stats = qs['stats']
    if action_type == 'practice':
        stats['practice_count'] += 1
    elif action_type == 'talk':
        stats['talk_count'] += 1
    elif action_type == 'visit' and location:
        if location not in stats['unique_locations']:
            stats['unique_locations'].append(location)
    elif action_type == 'breakthrough':
        stats['breakthroughs'] += 1
    check_achievements(state)
    state.save()

def check_achievements(state):
    from wuxia_quests import ACHIEVEMENTS
    init_quest_state(state)
    qs = state.quest_state
    stats = qs['stats']
    for ach in ACHIEVEMENTS:
        if ach['id'] in qs['achievements_unlocked']:
            continue
        cond = ach['condition']
        met = True
        for k, v in cond.items():
            if k == 'unique_locations':
                if len(stats.get(k, [])) < v:
                    met = False
            elif k == 'npc_relationships':
                rel_count = sum(1 for r in state.relationship.values() if r >= 1)
                if rel_count < v:
                    met = False
            elif k == 'realm_index':
                if state.realm_index < v:
                    met = False
            else:
                if stats.get(k, 0) < v:
                    met = False
        if met:
            qs['achievements_unlocked'].append(ach['id'])
            rewards = ach['rewards']
            if 'xp' in rewards:
                state.cultivation += rewards['xp']
            if 'silver' in rewards:
                state.silver += rewards['silver']
            if 'gold' in rewards:
                state.gold += rewards['gold']

def get_quest_summary(state):
    init_quest_state(state)
    qs = state.quest_state
    from wuxia_quests import MAIN_QUESTS
    main_quest = None
    for q in MAIN_QUESTS:
        if q['id'] == qs['main_active']:
            main_quest = q
            break
    return {
        'main_quest': main_quest,
        'main_completed': qs['main_completed'],
        'side_active': qs['side_active'],
        'achievements': qs['achievements_unlocked'],
        'stats': qs['stats'],
    }
