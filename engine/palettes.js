// Named palettes — the only colors the world is allowed to use.
// Each palette: floor, wall, trim (baseboard/lintels), accent (props/frames),
// glow (emissive details, portal light), fog, light (room point-light color).

export const PALETTES = {
  parchment: {
    floor: 0x8a7a5e, wall: 0xcfc2a5, trim: 0x6e5b3e, accent: 0x9c7b3f,
    glow: 0xffd98a, fog: 0x2a2118, light: 0xffd9a0,
  },
  emerald: {
    floor: 0x274233, wall: 0x3c5c49, trim: 0x1c2f24, accent: 0xb08428,
    glow: 0x9fe8b9, fog: 0x101f17, light: 0xcfe9c9,
  },
  amber: {
    floor: 0x5c4123, wall: 0x8a6a3c, trim: 0x3e2b15, accent: 0xc78f3a,
    glow: 0xffc46b, fog: 0x231708, light: 0xffc878,
  },
  crimson: {
    floor: 0x4a2020, wall: 0x6e3030, trim: 0x2e1212, accent: 0xb08428,
    glow: 0xff9a7a, fog: 0x1d0c0c, light: 0xffb09a,
  },
  sapphire: {
    floor: 0x1f2c4a, wall: 0x32456e, trim: 0x131c30, accent: 0x8c8b86,
    glow: 0x9ac4ff, fog: 0x0b1120, light: 0xa9c8ff,
  },
  violet: {
    floor: 0x32234a, wall: 0x4c3a6e, trim: 0x1e1430, accent: 0xb08428,
    glow: 0xd2a8ff, fog: 0x140d20, light: 0xd8baff,
  },
  obsidian: {
    floor: 0x1c1c20, wall: 0x2c2c32, trim: 0x101012, accent: 0x8c8b86,
    glow: 0xa8fff2, fog: 0x0a0a0c, light: 0xbfcfd0,
  },
};

export function palette(name) {
  return PALETTES[name] || PALETTES.parchment;
}

export function hexCss(hex) {
  return '#' + hex.toString(16).padStart(6, '0');
}
