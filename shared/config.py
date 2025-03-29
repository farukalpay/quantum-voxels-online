# shared/config.py
config = {
    'chunkSize': 16,
    'worldHeight': 48,
    'worldWidth': 64,
    'worldDepth': 64,
    'renderDistance': 5,
    'gravity': 9.81,
    'jumpForce': 5,
    'moveSpeed': 5,
    'mouseSensitivity': 0.002,
    'breakSpeed': 1.5,
    'reachDistance': 5,
    'maxInventorySlots': 9,
    'worldGenSeed': 12345,
    'expandWorldDistance': 16,
    'forceDenseTerrain': True,
    'defaultViewMode': 'third-person',
    'dayNightCycle': True,
    'cycleDuration': 120,
    'enableWeatherEffects': False,
    'blockTypes': {
        'air': {'id': 0, 'name': 'Air', 'emoji': '🌫️', 'color': '0x000000', 'transparent': True, 'walkable': True, 'className': ''},
        'dirt': {'id': 1, 'name': 'Dirt', 'emoji': '🟤', 'color': '0x8B4513', 'transparent': False, 'walkable': False, 'breakTime': 0.5, 'className': 'block-dirt'},
        'stone': {'id': 2, 'name': 'Stone', 'emoji': '⚪', 'color': '0x888888', 'transparent': False, 'walkable': False, 'breakTime': 1.0, 'className': 'block-stone'},
        'glass': {'id': 3, 'name': 'Glass', 'emoji': '💎', 'color': '0x88CCFF', 'transparent': True, 'opacity': 0.5, 'walkable': False, 'breakTime': 0.3, 'className': 'block-glass'},
        'quantum': {'id': 4, 'name': 'Quantum Block', 'emoji': '🔮', 'color': '0xAA00FF', 'transparent': False, 'walkable': False, 'glow': True, 'breakTime': 2.0, 'className': 'block-quantum'},
        'teleport': {'id': 5, 'name': 'Teleport Block', 'emoji': '✨', 'color': '0x00FFAA', 'transparent': True, 'opacity': 0.7, 'walkable': False, 'special': 'teleport', 'breakTime': 1.5, 'className': 'block-teleport'}
    }
}