// shared/config.js
const config = {
  chunkSize: 16,
  worldHeight: 48,
  worldWidth: 64,
  worldDepth: 64,
  renderDistance: 5,
  gravity: 9.81,
  jumpForce: 5,
  moveSpeed: 5,
  mouseSensitivity: 0.002,
  breakSpeed: 1.5,
  reachDistance: 5,
  maxInventorySlots: 9,
  worldGenSeed: 12345,
  expandWorldDistance: 16,
  forceDenseTerrain: true,
  defaultViewMode: 'third-person',
  dayNightCycle: true,
  cycleDuration: 120,
  enableWeatherEffects: false,
  blockTypes: {
    air: { id: 0, name: 'Air', emoji: '🌫️', color: 0x000000, transparent: true, walkable: true, className: '' },
    dirt: { id: 1, name: 'Dirt', emoji: '🟤', color: 0x8B4513, transparent: false, walkable: false, breakTime: 0.5, className: 'block-dirt' },
    stone: { id: 2, name: 'Stone', emoji: '⚪', color: 0x888888, transparent: false, walkable: false, breakTime: 1.0, className: 'block-stone' },
    glass: { id: 3, name: 'Glass', emoji: '💎', color: 0x88CCFF, transparent: true, opacity: 0.5, walkable: false, breakTime: 0.3, className: 'block-glass' },
    quantum: { id: 4, name: 'Quantum Block', emoji: '🔮', color: 0xAA00FF, transparent: false, walkable: false, glow: true, breakTime: 2.0, className: 'block-quantum' },
    teleport: { id: 5, name: 'Teleport Block', emoji: '✨', color: 0x00FFAA, transparent: true, opacity: 0.7, walkable: false, special: 'teleport', breakTime: 1.5, className: 'block-teleport' },
    grass: { id: 6, name: 'Grass', emoji: '🌱', color: 0x4CAF50, transparent: false, walkable: false, breakTime: 0.5, className: 'block-grass' },
    sand: { id: 7, name: 'Sand', emoji: '🏝️', color: 0xF9E076, transparent: false, walkable: false, breakTime: 0.4, className: 'block-sand' },
    water: { id: 8, name: 'Water', emoji: '💧', color: 0x3498DB, transparent: true, opacity: 0.7, walkable: true, special: 'liquid', breakTime: null, className: 'block-water' }
  }
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = config;
}

if (typeof window !== 'undefined') {
  window.config = config;
}