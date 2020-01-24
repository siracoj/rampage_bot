"""
Static lists for validation / options
"""
CLASSES = ['warrior', 'warlock', 'druid', 'mage', 'shaman', 'priest', 'hunter', 'rogue']
ROLES = ['dps', 'tank', 'heals']

CLASS_ROLES = {
    'warlock': ['dps'],
    'mage': ['dps'],
    'hunter': ['dps'],
    'rogue': ['dps'],
    'priest': ['dps', 'heals'],
    'shaman': ['dps', 'heals'],
    'warrior': ['dps', 'tank'],
    'druid': ['dps', 'tank', 'heals'],
}

RAIDS = ['MC', 'ONY', 'BWL', 'PERMANENT']