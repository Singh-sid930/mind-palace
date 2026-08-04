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
    floor: 0x7a5836, wall: 0xa8834a, trim: 0x4e3618, accent: 0xe0a94e,
    glow: 0xffc46b, fog: 0x2c1e0c, light: 0xffd28a,
  },
  crimson: {
    floor: 0x6e3535, wall: 0x9a4a4a, trim: 0x3e1c1c, accent: 0xe0a860,
    glow: 0xff9a7a, fog: 0x2a1010, light: 0xffc0aa,
  },
  sapphire: {
    floor: 0x44598a, wall: 0x6480b4, trim: 0x2c3d63, accent: 0xb6c2d6,
    glow: 0x9ac4ff, fog: 0x16223c, light: 0xd2e0ff,
  },
  violet: {
    floor: 0x4a3570, wall: 0x6e569e, trim: 0x2c1f47, accent: 0xd8c27a,
    glow: 0xd2a8ff, fog: 0x1d1330, light: 0xe4d2ff,
  },
  obsidian: {
    floor: 0x43454f, wall: 0x585a66, trim: 0x282a32, accent: 0xb0b0a6,
    glow: 0xa8fff2, fog: 0x16171d, light: 0xdcebee,
  },
  silver: {
    floor: 0x3a3f47, wall: 0x60656f, trim: 0x22252b, accent: 0xc4ceda,
    glow: 0xd0e0f0, fog: 0x16191f, light: 0xe8f0f8,
  },
  bronze: {
    floor: 0x4a3d28, wall: 0x796244, trim: 0x2c2214, accent: 0xc9a24e,
    glow: 0xe8c26a, fog: 0x1e180e, light: 0xf0d692,
  },
  verdigris: {
    floor: 0x2e4a47, wall: 0x467a72, trim: 0x1c2f2c, accent: 0xd8b25a,
    glow: 0x7ff2d8, fog: 0x10201d, light: 0xcfeee4,
  },
  cobalt: {
    floor: 0x1e3550, wall: 0x2f5580, trim: 0x142338, accent: 0x9fd8e8,
    glow: 0x5fd8ff, fog: 0x0b1626, light: 0xc2e8ff,
  },
  ember: {
    floor: 0x4a2c22, wall: 0x7a4632, trim: 0x2a1810, accent: 0xd9a05a,
    glow: 0xff8a4a, fog: 0x1e0f08, light: 0xffc296,
  },
};

export function palette(name) {
  return PALETTES[name] || PALETTES.parchment;
}

export function hexCss(hex) {
  return '#' + hex.toString(16).padStart(6, '0');
}
