// Shared engine vocabulary: the one material helper and the fixed colors that
// several modules must agree on. Room-specific colors live in palettes.js;
// these are the palace-wide constants (furniture wood, passage glows).

import * as THREE from 'three';

export const lam = (color, extra = {}) => new THREE.MeshLambertMaterial({ color, ...extra });

// Furniture / structure tones (props, signposts).
export const WOOD = 0x4a3320;
export const DARKWOOD = 0x33220f;
export const STONE = 0x8b8678;
export const METAL = 0xb08428;

// Passage identity colors. Vertical stairs wear a fixed COOL sapphire so they
// pop against any room palette; lateral archways wear warm GOLD so a sideways
// crossing reads differently from an up/down one. Props and signboards share
// these — change them here and every portal + sign changes together.
export const STAIR_GLOW = 0x6ea8ff;   // sapphire glow
export const STAIR_EDGE = 0xcfe6ff;   // pale-blue tread/arch edges
export const STAIR_SIGN_TRIM = 0x14233a;
export const ARCH_GOLD = 0xffcf6b;
export const ARCH_SIGN_TRIM = 0x3a2a10;
