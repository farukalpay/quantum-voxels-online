from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO, emit
import math
import random
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')  # Allow all origins for development

# Hardcoded configuration (equivalent to shared/config.js)
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
        'air': {'id': 0, 'name': 'Air', 'emoji': '🌫️', 'color': 0x000000, 'transparent': True, 'walkable': True, 'className': ''},
        'dirt': {'id': 1, 'name': 'Dirt', 'emoji': '🟤', 'color': 0x8B4513, 'transparent': False, 'walkable': False, 'breakTime': 0.5, 'className': 'block-dirt'},
        'stone': {'id': 2, 'name': 'Stone', 'emoji': '⚪', 'color': 0x888888, 'transparent': False, 'walkable': False, 'breakTime': 1.0, 'className': 'block-stone'},
        'glass': {'id': 3, 'name': 'Glass', 'emoji': '💎', 'color': 0x88CCFF, 'transparent': True, 'opacity': 0.5, 'walkable': False, 'breakTime': 0.3, 'className': 'block-glass'},
        'quantum': {'id': 4, 'name': 'Quantum Block', 'emoji': '🔮', 'color': 0xAA00FF, 'transparent': False, 'walkable': False, 'glow': True, 'breakTime': 2.0, 'className': 'block-quantum'},
        'teleport': {'id': 5, 'name': 'Teleport Block', 'emoji': '✨', 'color': 0x00FFAA, 'transparent': True, 'opacity': 0.7, 'walkable': False, 'special': 'teleport', 'breakTime': 1.5, 'className': 'block-teleport'},
        'grass': {'id': 6, 'name': 'Grass', 'emoji': '🌱', 'color': 0x4CAF50, 'transparent': False, 'walkable': False, 'breakTime': 0.5, 'className': 'block-grass'},
        'sand': {'id': 7, 'name': 'Sand', 'emoji': '🏝️', 'color': 0xF9E076, 'transparent': False, 'walkable': False, 'breakTime': 0.4, 'className': 'block-sand'},
        'water': {'id': 8, 'name': 'Water', 'emoji': '💧', 'color': 0x3498DB, 'transparent': True, 'opacity': 0.7, 'walkable': True, 'special': 'liquid', 'breakTime': None, 'className': 'block-water'}
    }
}

# Game state storage
chunks = {}
players = {}

# Noise generation functions (simplified for brevity)
seed = config['worldGenSeed']

def int_hash(n):
    n = (n << 13) ^ n
    return (n * (n * n * 15731 + 789221) + 1376312589) & 0x7fffffff

def noise(x, z):
    ix = math.floor(x)
    iz = math.floor(z)
    fx = x - ix
    fz = z - iz
    u = fx * fx * (3.0 - 2.0 * fx)
    v = fz * fz * (3.0 - 2.0 * fz)
    h1 = int_hash(iz + seed)
    h2 = int_hash(iz + 1 + seed)
    r = int_hash(ix + h1)
    s = int_hash(ix + 1 + h1)
    t = int_hash(ix + h2)
    q = int_hash(ix + 1 + h2)
    r = (r / 0x7fffffff) * 2 - 1
    s = (s / 0x7fffffff) * 2 - 1
    t = (t / 0x7fffffff) * 2 - 1
    q = (q / 0x7fffffff) * 2 - 1
    return r + (s - r) * u + (t - r) * v + (q - s - t + r) * u * v

def fBm(x, z, octaves=6, lacunarity=2.0, gain=0.5):
    total = 0
    frequency = 1
    amplitude = 1
    maxValue = 0
    for i in range(octaves):
        total += amplitude * noise(x * frequency, z * frequency)
        maxValue += amplitude
        frequency *= lacunarity
        amplitude *= gain
    return total / maxValue

def noise3D(x, y, z):
    ix = math.floor(x)
    iy = math.floor(y)
    iz = math.floor(z)
    fx = x - ix
    fy = y - iy
    fz = z - iz
    u = fx * fx * (3.0 - 2.0 * fx)
    v = fy * fy * (3.0 - 2.0 * fy)
    w = fz * fz * (3.0 - 2.0 * fz)
    h000 = int_hash(ix + int_hash(iy + int_hash(iz + seed)))
    h100 = int_hash(ix + 1 + int_hash(iy + int_hash(iz + seed)))
    h010 = int_hash(ix + int_hash(iy + 1 + int_hash(iz + seed)))
    h110 = int_hash(ix + 1 + int_hash(iy + 1 + int_hash(iz + seed)))
    h001 = int_hash(ix + int_hash(iy + int_hash(iz + 1 + seed)))
    h101 = int_hash(ix + 1 + int_hash(iy + int_hash(iz + 1 + seed)))
    h011 = int_hash(ix + int_hash(iy + 1 + int_hash(iz + 1 + seed)))
    h111 = int_hash(ix + 1 + int_hash(iy + 1 + int_hash(iz + 1 + seed)))
    h000 = (h000 / 0x7fffffff) * 2 - 1
    h100 = (h100 / 0x7fffffff) * 2 - 1
    h010 = (h010 / 0x7fffffff) * 2 - 1
    h110 = (h110 / 0x7fffffff) * 2 - 1
    h001 = (h001 / 0x7fffffff) * 2 - 1
    h101 = (h101 / 0x7fffffff) * 2 - 1
    h011 = (h011 / 0x7fffffff) * 2 - 1
    h111 = (h111 / 0x7fffffff) * 2 - 1
    a = h000 + (h100 - h000) * u
    b = h010 + (h110 - h010) * u
    c = h001 + (h101 - h001) * u
    d = h011 + (h111 - h011) * u
    e = a + (b - a) * v
    f = c + (d - c) * v
    return e + (f - e) * w

def fBm3D(x, y, z, octaves=4, lacunarity=2.0, gain=0.5):
    total = 0
    frequency = 1
    amplitude = 1
    maxValue = 0
    for i in range(octaves):
        total += amplitude * noise3D(x * frequency, y * frequency, z * frequency)
        maxValue += amplitude
        frequency *= lacunarity
        amplitude *= gain
    return total / maxValue

# Terrain generation constants
biomeScale = 0.005
terrainScale = 0.05
caveScale = 0.1
seaLevel = 10
snowLevel = 20

def generateChunk(chunkX, chunkZ):
    chunk = []
    for x in range(config['chunkSize']):
        chunk.append([])
        worldX = chunkX * config['chunkSize'] + x
        for z in range(config['chunkSize']):
            chunk[x].append([])
            worldZ = chunkZ * config['chunkSize'] + z
            biomeNoise = fBm(worldX * biomeScale, worldZ * biomeScale, 4)
            if biomeNoise < -0.3:
                biome = 'desert'
                heightMultiplier = 0.5
                surfaceBlock = config['blockTypes']['sand']['id']
                subsurfaceBlock = config['blockTypes']['sand']['id']
            elif biomeNoise > 0.3:
                biome = 'mountain'
                heightMultiplier = 1.5
                surfaceBlock = config['blockTypes']['stone']['id']
                subsurfaceBlock = config['blockTypes']['stone']['id']
            else:
                biome = 'forest'
                heightMultiplier = 1.0
                surfaceBlock = config['blockTypes']['grass']['id']
                subsurfaceBlock = config['blockTypes']['dirt']['id']
            terrainNoise = fBm(worldX * terrainScale, worldZ * terrainScale, 6)
            baseHeight = (terrainNoise + 1) * 12 + 4
            finalHeight = math.floor(baseHeight * heightMultiplier)
            finalHeight = max(0, min(config['worldHeight'] - 1, finalHeight))
            for y in range(config['worldHeight']):
                blockId = config['blockTypes']['air']['id']
                if y < finalHeight:
                    if y < finalHeight - 3:
                        blockId = config['blockTypes']['stone']['id']
                    elif y < finalHeight:
                        blockId = subsurfaceBlock
                    caveNoise = fBm3D(worldX * caveScale, y * caveScale, worldZ * caveScale, 4)
                    if caveNoise > 0.5 and y < finalHeight - 1:
                        blockId = config['blockTypes']['air']['id']
                    if y < finalHeight - 5 and random.random() < 0.001:
                        blockId = config['blockTypes']['quantum']['id']
                elif y < seaLevel:
                    blockId = config['blockTypes']['water']['id']
                chunk[x][z].append(blockId)
            if finalHeight < config['worldHeight']:
                chunk[x][z][finalHeight] = surfaceBlock
                if biome == 'mountain' and finalHeight >= snowLevel:
                    chunk[x][z][finalHeight] = config['blockTypes']['stone']['id']
                if biome == 'forest' and random.random() < 0.015 and finalHeight < config['worldHeight'] - 5:
                    treeHeight = 3 + math.floor(random.random() * 3)
                    for ty in range(finalHeight + 1, finalHeight + treeHeight):
                        chunk[x][z][ty] = config['blockTypes']['stone']['id']
                    if finalHeight + treeHeight < config['worldHeight']:
                        chunk[x][z][finalHeight + treeHeight] = config['blockTypes']['dirt']['id']
    print(f"Generated chunk {chunkX}_{chunkZ}")
    return chunk

def getChunk(chunkX, chunkZ):
    key = f"{chunkX}_{chunkZ}"
    if key not in chunks:
        chunks[key] = generateChunk(chunkX, chunkZ)
    return chunks[key]

def getBlockAt(x, y, z):
    chunkX = math.floor(x / config['chunkSize'])
    chunkZ = math.floor(z / config['chunkSize'])
    localX = ((x % config['chunkSize']) + config['chunkSize']) % config['chunkSize']
    localZ = ((z % config['chunkSize']) + config['chunkSize']) % config['chunkSize']
    chunk = getChunk(chunkX, chunkZ)
    if 0 <= y < config['worldHeight']:
        return chunk[localX][localZ][y] if chunk[localX][localZ] else config['blockTypes']['air']['id']
    return config['blockTypes']['air']['id']

def findSafeStartingPosition():
    centerX = math.floor(config['worldWidth'] / 2)
    centerZ = math.floor(config['worldDepth'] / 2)
    for y in range(config['worldHeight'] - 1, -1, -1):
        block = getBlockAt(centerX, y, centerZ)
        if block != config['blockTypes']['air']['id'] and block != config['blockTypes']['water']['id']:
            spawnY = y + 1
            print(f"Spawning player at {centerX + 0.5}, {spawnY}, {centerZ + 0.5}")
            return {'x': centerX + 0.5, 'y': spawnY, 'z': centerZ + 0.5}
    print('No safe spawn found, using fallback')
    return {'x': 32.5, 'y': 11, 'z': 32.5}

# Serve static files
@app.route('/')
def serve_index():
    return send_from_directory('../client', 'index.html')

@app.route('/<path:path>')
def serve_client(path):
    return send_from_directory('../client', path)

@app.route('/shared/<path:path>')
def serve_shared(path):
    return send_from_directory('../shared', path)

@socketio.on('connect')
def handle_connect(auth=None):
    playerId = request.sid
    initialChunkX = math.floor(config['worldWidth'] / 2 / config['chunkSize'])
    initialChunkZ = math.floor(config['worldDepth'] / 2 / config['chunkSize'])
    for dx in range(-1, 2):
        for dz in range(-1, 2):
            getChunk(initialChunkX + dx, initialChunkZ + dz)
    startPosition = findSafeStartingPosition()
    players[playerId] = {'position': startPosition}
    # Send existing players to the new player
    other_players = {pid: {'position': p['position']} for pid, p in players.items() if pid != playerId}
    emit('welcome', {
        'playerId': playerId,
        'startPosition': startPosition,
        'chunkData': {
            f"{initialChunkX - 1}_{initialChunkZ - 1}": chunks[f"{initialChunkX - 1}_{initialChunkZ - 1}"],
            f"{initialChunkX - 1}_{initialChunkZ}": chunks[f"{initialChunkX - 1}_{initialChunkZ}"],
            f"{initialChunkX - 1}_{initialChunkZ + 1}": chunks[f"{initialChunkX - 1}_{initialChunkZ + 1}"],
            f"{initialChunkX}_{initialChunkZ - 1}": chunks[f"{initialChunkX}_{initialChunkZ - 1}"],
            f"{initialChunkX}_{initialChunkZ}": chunks[f"{initialChunkX}_{initialChunkZ}"],
            f"{initialChunkX}_{initialChunkZ + 1}": chunks[f"{initialChunkX}_{initialChunkZ + 1}"],
            f"{initialChunkX + 1}_{initialChunkZ - 1}": chunks[f"{initialChunkX + 1}_{initialChunkZ - 1}"],
            f"{initialChunkX + 1}_{initialChunkZ}": chunks[f"{initialChunkX + 1}_{initialChunkZ}"],
            f"{initialChunkX + 1}_{initialChunkZ + 1}": chunks[f"{initialChunkX + 1}_{initialChunkZ + 1}"]
        },
        'otherPlayers': other_players
    })
    # Notify existing players of the new player
    socketio.emit('playerJoined', {'playerId': playerId, 'position': startPosition}, skip_sid=playerId)
    print(f"Player {playerId} connected at {startPosition['x']}, {startPosition['y']}, {startPosition['z']}")

@socketio.on('requestChunk')
def handle_requestChunk(data):
    chunkX = data['chunkX']
    chunkZ = data['chunkZ']
    chunk = getChunk(chunkX, chunkZ)
    emit('chunk', {'chunkX': chunkX, 'chunkZ': chunkZ, 'data': chunk})

@socketio.on('move')
def handle_move(data):
    playerId = request.sid
    if playerId in players:
        players[playerId]['position'] = data['position']
        socketio.emit('playerMoved', {
            'playerId': playerId,
            'position': data['position'],
            'facing': data['facing']
        }, skip_sid=playerId)

@socketio.on('disconnect')
def handle_disconnect():
    playerId = request.sid
    if playerId in players:
        del players[playerId]
        print(f"Player {playerId} disconnected")
        socketio.emit('playerLeft', playerId)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=3000)