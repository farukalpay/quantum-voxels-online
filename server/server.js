const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const path = require('path');

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

const config = require('../shared/config'); // Load shared configuration

// Serve static files
app.use(express.static(path.join(__dirname, '../client')));
app.use('/shared', express.static(path.join(__dirname, '../shared')));

// Game state storage
const chunks = {};
const players = {};

// Noise generation functions
const seed = config.worldGenSeed;

// Hash function for pseudo-random noise
function hash(n) {
  n = (n + seed) ^ seed;
  n = (n << 13) ^ n;
  return (1.0 - ((n * (n * n * 15731 + 789221) + 1376312589) & 0x7fffffff) / 1073741824.0);
}

// 2D Perlin noise for terrain height
function noise(x, z) {
  const ix = Math.floor(x);
  const iz = Math.floor(z);
  const fx = x - ix;
  const fz = z - iz;
  const u = fx * fx * (3.0 - 2.0 * fx); // Smoothstep
  const v = fz * fz * (3.0 - 2.0 * fz);
  const r = hash(ix + hash(iz));
  const s = hash(ix + 1 + hash(iz));
  const t = hash(ix + hash(iz + 1));
  const q = hash(ix + 1 + hash(iz + 1));
  return r + (s - r) * u + (t - r) * v + (q - s - t + r) * u * v;
}

// Fractional Brownian Motion (fBm) for 2D terrain
function fBm(x, z, octaves = 6, lacunarity = 2.0, gain = 0.5) {
  let total = 0;
  let frequency = 1;
  let amplitude = 1;
  let maxValue = 0;
  for (let i = 0; i < octaves; i++) {
    total += amplitude * noise(x * frequency, z * frequency);
    maxValue += amplitude;
    frequency *= lacunarity;
    amplitude *= gain;
  }
  return total / maxValue; // Normalized to [-1, 1]
}

// 3D noise for caves and underground features
function noise3D(x, y, z) {
  const ix = Math.floor(x);
  const iy = Math.floor(y);
  const iz = Math.floor(z);
  const fx = x - ix;
  const fy = y - iy;
  const fz = z - iz;
  const u = fx * fx * (3.0 - 2.0 * fx);
  const v = fy * fy * (3.0 - 2.0 * fy);
  const w = fz * fz * (3.0 - 2.0 * fz);
  const h000 = hash(ix + hash(iy + hash(iz)));
  const h100 = hash(ix + 1 + hash(iy + hash(iz)));
  const h010 = hash(ix + hash(iy + 1 + hash(iz)));
  const h110 = hash(ix + 1 + hash(iy + 1 + hash(iz)));
  const h001 = hash(ix + hash(iy + hash(iz + 1)));
  const h101 = hash(ix + 1 + hash(iy + hash(iz + 1)));
  const h011 = hash(ix + hash(iy + 1 + hash(iz + 1)));
  const h111 = hash(ix + 1 + hash(iy + 1 + hash(iz + 1)));
  const a = h000 + (h100 - h000) * u;
  const b = h010 + (h110 - h010) * u;
  const c = h001 + (h101 - h001) * u;
  const d = h011 + (h111 - h011) * u;
  const e = a + (b - a) * v;
  const f = c + (d - c) * v;
  return e + (f - e) * w;
}

// 3D fBm for cave systems
function fBm3D(x, y, z, octaves = 4, lacunarity = 2.0, gain = 0.5) {
  let total = 0;
  let frequency = 1;
  let amplitude = 1;
  let maxValue = 0;
  for (let i = 0; i < octaves; i++) {
    total += amplitude * noise3D(x * frequency, y * frequency, z * frequency);
    maxValue += amplitude;
    frequency *= lacunarity;
    amplitude *= gain;
  }
  return total / maxValue;
}

// Terrain generation constants
const biomeScale = 0.005;  // Large scale for biome variation
const terrainScale = 0.05; // Detailed terrain features
const caveScale = 0.1;     // Scale for cave generation
const seaLevel = 10;       // Height of sea level
const snowLevel = 20;      // Elevation for snow in mountains

// Generate a chunk with improved terrain
function generateChunk(chunkX, chunkZ) {
  const chunk = [];
  for (let x = 0; x < config.chunkSize; x++) {
    chunk[x] = [];
    const worldX = chunkX * config.chunkSize + x;
    for (let z = 0; z < config.chunkSize; z++) {
      chunk[x][z] = [];
      const worldZ = chunkZ * config.chunkSize + z;

      // Determine biome
      const biomeX = worldX * biomeScale;
      const biomeZ = worldZ * biomeScale;
      const biomeNoise = fBm(biomeX, biomeZ, 4);
      let biome, heightMultiplier, surfaceBlock, subsurfaceBlock;
      if (biomeNoise < -0.3) {
        biome = 'desert';
        heightMultiplier = 0.5; // Flatter terrain
        surfaceBlock = config.blockTypes.sand.id;
        subsurfaceBlock = config.blockTypes.sand.id;
      } else if (biomeNoise > 0.3) {
        biome = 'mountain';
        heightMultiplier = 1.5; // Taller peaks
        surfaceBlock = config.blockTypes.stone.id;
        subsurfaceBlock = config.blockTypes.stone.id;
      } else {
        biome = 'forest';
        heightMultiplier = 1.0; // Moderate hills
        surfaceBlock = config.blockTypes.grass.id;
        subsurfaceBlock = config.blockTypes.dirt.id;
      }

      // Calculate terrain height
      const terrainX = worldX * terrainScale;
      const terrainZ = worldZ * terrainScale;
      const terrainNoise = fBm(terrainX, terrainZ, 6);
      const baseHeight = (terrainNoise + 1) * 12 + 4; // Range: 4 to 28
      let finalHeight = Math.floor(baseHeight * heightMultiplier);
      finalHeight = Math.max(0, Math.min(config.worldHeight - 1, finalHeight));

      // Fill the chunk vertically
      for (let y = 0; y < config.worldHeight; y++) {
        let blockId = config.blockTypes.air.id;
        if (y < finalHeight) {
          if (y < finalHeight - 3) {
            blockId = config.blockTypes.stone.id;
          } else if (y < finalHeight) {
            blockId = subsurfaceBlock;
          }
          // Carve caves
          const caveX = worldX * caveScale;
          const caveY = y * caveScale;
          const caveZ = worldZ * caveScale;
          const caveNoise = fBm3D(caveX, caveY, caveZ, 4);
          if (caveNoise > 0.5 && y < finalHeight - 1) {
            blockId = config.blockTypes.air.id;
          }
          // Add rare quantum deposits
          if (y < finalHeight - 5 && Math.random() < 0.001) {
            blockId = config.blockTypes.quantum.id;
          }
        } else if (y < seaLevel) {
          blockId = config.blockTypes.water.id;
        }
        chunk[x][z][y] = blockId;
      }

      // Place surface blocks and features
      if (finalHeight < config.worldHeight) {
        chunk[x][z][finalHeight] = surfaceBlock;
        if (biome === 'mountain' && finalHeight >= snowLevel) {
          chunk[x][z][finalHeight] = config.blockTypes.snow.id;
        }
        // Add trees in forest biome
        if (biome === 'forest' && Math.random() < 0.015 && finalHeight < config.worldHeight - 5) {
          const treeHeight = 3 + Math.floor(Math.random() * 3); // 3-5 blocks tall
          for (let ty = finalHeight + 1; ty < finalHeight + treeHeight; ty++) {
            chunk[x][z][ty] = config.blockTypes.stone.id; // Trunk
          }
          // Simple foliage (single block on top)
          if (finalHeight + treeHeight < config.worldHeight) {
            chunk[x][z][finalHeight + treeHeight] = config.blockTypes.dirt.id;
          }
        }
      }
    }
  }
  console.log(`Generated chunk ${chunkX}_${chunkZ}`);
  return chunk;
}

// Retrieve or generate a chunk
function getChunk(chunkX, chunkZ) {
  const key = `${chunkX}_${chunkZ}`;
  if (!chunks[key]) {
    chunks[key] = generateChunk(chunkX, chunkZ);
  }
  return chunks[key];
}

// Get block at world coordinates
function getBlockAt(x, y, z) {
  const chunkX = Math.floor(x / config.chunkSize);
  const chunkZ = Math.floor(z / config.chunkSize);
  const localX = ((x % config.chunkSize) + config.chunkSize) % config.chunkSize;
  const localZ = ((z % config.chunkSize) + config.chunkSize) % config.chunkSize;
  const chunk = getChunk(chunkX, chunkZ);
  if (y >= 0 && y < config.worldHeight) {
    return chunk[localX][localZ][y] || config.blockTypes.air.id;
  }
  return config.blockTypes.air.id;
}

// Find a safe spawn point
function findSafeStartingPosition() {
  const centerX = Math.floor(config.worldWidth / 2);
  const centerZ = Math.floor(config.worldDepth / 2);
  for (let y = config.worldHeight - 1; y >= 0; y--) {
    const block = getBlockAt(centerX, y, centerZ);
    if (block !== config.blockTypes.air.id && block !== config.blockTypes.water.id) {
      const spawnY = y + 1;
      console.log(`Spawning player at ${centerX + 0.5}, ${spawnY}, ${centerZ + 0.5}`);
      return { x: centerX + 0.5, y: spawnY, z: centerZ + 0.5 };
    }
  }
  console.log('No safe spawn found, using fallback');
  return { x: 32.5, y: 11, z: 32.5 };
}

// Socket.IO connection handling
io.on('connection', (socket) => {
  const playerId = socket.id;
  const initialChunkX = Math.floor(config.worldWidth / 2 / config.chunkSize);
  const initialChunkZ = Math.floor(config.worldDepth / 2 / config.chunkSize);

  // Pre-generate nearby chunks
  for (let dx = -1; dx <= 1; dx++) {
    for (let dz = -1; dz <= 1; dz++) {
      getChunk(initialChunkX + dx, initialChunkZ + dz);
    }
  }

  const startPosition = findSafeStartingPosition();
  players[playerId] = { position: startPosition };

  // Send initial data to the player
  socket.emit('welcome', {
    playerId,
    startPosition,
    chunkData: {
      [`${initialChunkX - 1}_${initialChunkZ - 1}`]: chunks[`${initialChunkX - 1}_${initialChunkZ - 1}`],
      [`${initialChunkX - 1}_${initialChunkZ}`]: chunks[`${initialChunkX - 1}_${initialChunkZ}`],
      [`${initialChunkX - 1}_${initialChunkZ + 1}`]: chunks[`${initialChunkX - 1}_${initialChunkZ + 1}`],
      [`${initialChunkX}_${initialChunkZ - 1}`]: chunks[`${initialChunkX}_${initialChunkZ - 1}`],
      [`${initialChunkX}_${initialChunkZ}`]: chunks[`${initialChunkX}_${initialChunkZ}`],
      [`${initialChunkX}_${initialChunkZ + 1}`]: chunks[`${initialChunkX}_${initialChunkZ + 1}`],
      [`${initialChunkX + 1}_${initialChunkZ - 1}`]: chunks[`${initialChunkX + 1}_${initialChunkZ - 1}`],
      [`${initialChunkX + 1}_${initialChunkZ}`]: chunks[`${initialChunkX + 1}_${initialChunkZ}`],
      [`${initialChunkX + 1}_${initialChunkZ + 1}`]: chunks[`${initialChunkX + 1}_${initialChunkZ + 1}`]
    }
  });

  console.log(`Player ${playerId} connected at ${startPosition.x}, ${startPosition.y}, ${startPosition.z}`);

  // Handle chunk requests
  socket.on('requestChunk', ({ chunkX, chunkZ }) => {
    const chunk = getChunk(chunkX, chunkZ);
    socket.emit('chunk', { chunkX, chunkZ, data: chunk });
  });

  // Handle player movement
  socket.on('move', (data) => {
    if (players[playerId]) {
      players[playerId].position = data.position;
      socket.broadcast.emit('playerMoved', {
        playerId,
        position: data.position,
        facing: data.facing
      });
    }
  });

  // Handle disconnection
  socket.on('disconnect', () => {
    delete players[playerId];
    console.log(`Player ${playerId} disconnected`);
    io.emit('playerLeft', playerId);
  });
});

// Start the server
server.listen(3000, () => {
  console.log('Server running on port 3000');
});