// Canvas-to-texture text rendering. No font assets: we draw onto 2D canvases
// and use them as textures, so every sign/plaque/portrait is procedural.

import * as THREE from 'three';
import { hexCss } from './palettes.js';

const SERIF = 'Georgia, "Times New Roman", serif';

function makeCanvas(w, h) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  return c;
}

function wrapText(ctx, text, maxWidth) {
  const out = [];
  for (const para of text.split('\n')) {
    let line = '';
    for (const word of para.split(' ')) {
      const probe = line ? line + ' ' + word : word;
      if (ctx.measureText(probe).width > maxWidth && line) {
        out.push(line);
        line = word;
      } else {
        line = probe;
      }
    }
    out.push(line);
  }
  return out;
}

// A framed parchment panel with a title and (optionally truncated) body text.
export function textPanelTexture({ title, body = '', w = 1024, h = 768, pal,
                                   titleSize = 64, bodySize = 38 }) {
  const c = makeCanvas(w, h);
  const ctx = c.getContext('2d');

  // Parchment ground with subtle vignette.
  ctx.fillStyle = '#e9dfc6';
  ctx.fillRect(0, 0, w, h);
  const vg = ctx.createRadialGradient(w / 2, h / 2, h / 3, w / 2, h / 2, h);
  vg.addColorStop(0, 'rgba(0,0,0,0)');
  vg.addColorStop(1, 'rgba(60,40,10,0.35)');
  ctx.fillStyle = vg;
  ctx.fillRect(0, 0, w, h);

  // Border in the palette's trim color.
  ctx.strokeStyle = hexCss(pal.trim);
  ctx.lineWidth = 14;
  ctx.strokeRect(22, 22, w - 44, h - 44);
  ctx.lineWidth = 4;
  ctx.strokeRect(40, 40, w - 80, h - 80);

  // Title.
  ctx.fillStyle = '#2a2118';
  ctx.font = `bold ${titleSize}px ${SERIF}`;
  ctx.textAlign = 'center';
  const titleLines = wrapText(ctx, title, w - 160);
  let y = 90 + titleSize;
  for (const line of titleLines.slice(0, 2)) {
    ctx.fillText(line, w / 2, y);
    y += titleSize * 1.15;
  }

  // Rule under title.
  ctx.strokeStyle = hexCss(pal.accent);
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(w * 0.2, y - titleSize * 0.55);
  ctx.lineTo(w * 0.8, y - titleSize * 0.55);
  ctx.stroke();

  // Body.
  if (body) {
    ctx.font = `${bodySize}px ${SERIF}`;
    ctx.textAlign = 'left';
    ctx.fillStyle = '#33291c';
    const lines = wrapText(ctx, body, w - 200);
    let by = y + bodySize * 0.8;
    const maxY = h - 80;
    for (const line of lines) {
      if (by > maxY - bodySize) {
        ctx.fillText('…', 100, by);
        break;
      }
      ctx.fillText(line, 100, by);
      by += bodySize * 1.32;
    }
  }

  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  return tex;
}

// A stylized portrait: hooded silhouette under an arch, with name plate.
export function portraitTexture({ name, subtitle = '', pal, w = 768, h = 1024 }) {
  const c = makeCanvas(w, h);
  const ctx = c.getContext('2d');

  // Dark oil-painting background.
  const bg = ctx.createLinearGradient(0, 0, 0, h);
  bg.addColorStop(0, '#1d1812');
  bg.addColorStop(1, '#0d0a07');
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, w, h);

  // Arched glow behind the figure.
  const glow = ctx.createRadialGradient(w / 2, h * 0.42, 40, w / 2, h * 0.42, w * 0.55);
  glow.addColorStop(0, 'rgba(255, 214, 140, 0.5)');
  glow.addColorStop(1, 'rgba(255, 214, 140, 0)');
  ctx.fillStyle = glow;
  ctx.fillRect(0, 0, w, h);

  // Robed silhouette: hood, shoulders, suggestion of a face in shadow.
  ctx.fillStyle = '#241c12';
  ctx.beginPath();
  ctx.moveTo(w * 0.5, h * 0.16);
  ctx.bezierCurveTo(w * 0.30, h * 0.20, w * 0.26, h * 0.42, w * 0.30, h * 0.52);
  ctx.bezierCurveTo(w * 0.18, h * 0.62, w * 0.14, h * 0.80, w * 0.16, h * 0.92);
  ctx.lineTo(w * 0.84, h * 0.92);
  ctx.bezierCurveTo(w * 0.86, h * 0.80, w * 0.82, h * 0.62, w * 0.70, h * 0.52);
  ctx.bezierCurveTo(w * 0.74, h * 0.42, w * 0.70, h * 0.20, w * 0.5, h * 0.16);
  ctx.fill();

  // Face shadow oval with two faint eye glints.
  ctx.fillStyle = '#0a0805';
  ctx.beginPath();
  ctx.ellipse(w * 0.5, h * 0.33, w * 0.115, h * 0.085, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = 'rgba(255, 226, 170, 0.9)';
  for (const dx of [-0.045, 0.045]) {
    ctx.beginPath();
    ctx.arc(w * (0.5 + dx), h * 0.335, 4.5, 0, Math.PI * 2);
    ctx.fill();
  }

  // Name plate.
  ctx.fillStyle = hexCss(pal.trim);
  ctx.fillRect(w * 0.12, h * 0.93, w * 0.76, h * 0.055);
  ctx.fillStyle = '#e9dfc6';
  ctx.textAlign = 'center';
  ctx.font = `bold ${Math.floor(w * 0.052)}px ${SERIF}`;
  ctx.fillText(name, w / 2, h * 0.966, w * 0.7);

  if (subtitle) {
    ctx.fillStyle = 'rgba(233, 223, 198, 0.75)';
    ctx.font = `italic ${Math.floor(w * 0.034)}px ${SERIF}`;
    ctx.fillText(subtitle, w / 2, h * 0.915, w * 0.7);
  }

  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

// A mystical "diagram sigil" panel for in-world display (the real Mermaid
// diagram renders in the focus overlay; in-world we show an evocative card).
export function diagramTexture({ title, pal, w = 1024, h = 768 }) {
  const c = makeCanvas(w, h);
  const ctx = c.getContext('2d');

  ctx.fillStyle = '#141a22';
  ctx.fillRect(0, 0, w, h);

  // Constellation-style node scatter derived from the title (deterministic).
  let seed = 0;
  for (const ch of title) seed = (seed * 31 + ch.charCodeAt(0)) >>> 0;
  const rand = () => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 0xffffffff;
  };
  const nodes = [];
  const n = 7 + Math.floor(rand() * 4);
  for (let i = 0; i < n; i++) {
    nodes.push({ x: 120 + rand() * (w - 240), y: 120 + rand() * (h - 300) });
  }
  ctx.strokeStyle = 'rgba(154, 196, 255, 0.45)';
  ctx.lineWidth = 2;
  for (let i = 0; i < n; i++) {
    const j = (i + 1 + Math.floor(rand() * (n - 2))) % n;
    ctx.beginPath();
    ctx.moveTo(nodes[i].x, nodes[i].y);
    ctx.lineTo(nodes[j].x, nodes[j].y);
    ctx.stroke();
  }
  for (const node of nodes) {
    ctx.fillStyle = '#cfe4ff';
    ctx.beginPath();
    ctx.arc(node.x, node.y, 7, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = 'rgba(154,196,255,0.25)';
    ctx.beginPath();
    ctx.arc(node.x, node.y, 16, 0, Math.PI * 2);
    ctx.fill();
  }

  // Title band.
  ctx.fillStyle = 'rgba(10, 14, 20, 0.85)';
  ctx.fillRect(0, h - 130, w, 130);
  ctx.strokeStyle = hexCss(pal.accent);
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(60, h - 130);
  ctx.lineTo(w - 60, h - 130);
  ctx.stroke();
  ctx.fillStyle = '#dbe7f5';
  ctx.textAlign = 'center';
  ctx.font = `bold 52px ${SERIF}`;
  ctx.fillText(title, w / 2, h - 55, w - 160);
  ctx.fillStyle = 'rgba(219,231,245,0.6)';
  ctx.font = `italic 30px ${SERIF}`;
  ctx.fillText('— study closely to unfold the diagram —', w / 2, h - 18, w - 160);

  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

// Floating room-name banner texture.
export function bannerTexture({ text, pal, w = 1024, h = 256 }) {
  const c = makeCanvas(w, h);
  const ctx = c.getContext('2d');
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = hexCss(pal.trim);
  ctx.globalAlpha = 0.92;
  ctx.fillRect(0, 0, w, h);
  ctx.globalAlpha = 1;
  ctx.strokeStyle = hexCss(pal.accent);
  ctx.lineWidth = 10;
  ctx.strokeRect(12, 12, w - 24, h - 24);
  ctx.fillStyle = '#efe6cf';
  ctx.textAlign = 'center';
  ctx.font = `bold 96px ${SERIF}`;
  ctx.fillText(text, w / 2, h / 2 + 34, w - 100);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}
