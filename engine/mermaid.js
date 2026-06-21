// Shared Mermaid loader + a rasterizer that turns a diagram spec into a
// high-resolution Three.js texture, so the same diagram can render both in the
// flat focus overlay (hud.js) and on a large floating panel in world space
// (diagrampanel.js). Mermaid is lazy-loaded from a CDN; offline, callers fall
// back to plain text.

import * as THREE from 'three';

let mermaidPromise = null;

export function loadMermaid() {
  if (!mermaidPromise) {
    mermaidPromise = import('https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs')
      .then((m) => {
        // htmlLabels:false keeps labels as native SVG <text> (no <foreignObject>),
        // so the SVG can be rasterized to a canvas texture without tainting it.
        m.default.initialize({
          startOnLoad: false, theme: 'dark', darkMode: true,
          htmlLabels: false, flowchart: { htmlLabels: false },
        });
        return m.default;
      })
      .catch(() => null);
  }
  return mermaidPromise;
}

// Render a Mermaid spec to an offscreen canvas texture on a dark backing.
// Returns { texture, w, h } (pixel size) or null if Mermaid/rasterization fails.
export async function renderDiagramTexture(spec) {
  const mermaid = await loadMermaid();
  if (!mermaid) return null;

  let svg;
  try {
    ({ svg } = await mermaid.render('dia3d-' + Date.now(), spec));
  } catch {
    return null;
  }

  // Force an explicit pixel size from the viewBox so the SVG rasterizes at a
  // known, crisp resolution rather than its CSS max-width.
  const doc = new DOMParser().parseFromString(svg, 'image/svg+xml');
  const root = doc.documentElement;
  let vw = 1024, vh = 768;
  const vb = root.getAttribute('viewBox');
  if (vb) {
    const p = vb.split(/[ ,]+/).map(Number);
    if (p.length === 4 && p[2] > 0 && p[3] > 0) { vw = p[2]; vh = p[3]; }
  }
  const W = 2048;
  const H = Math.max(256, Math.round(W * vh / vw));
  root.setAttribute('width', String(W));
  root.setAttribute('height', String(H));
  root.removeAttribute('style');
  const fixed = new XMLSerializer().serializeToString(root);

  const url = URL.createObjectURL(new Blob([fixed], { type: 'image/svg+xml;charset=utf-8' }));
  try {
    const img = new Image();
    await new Promise((res, rej) => { img.onload = () => res(); img.onerror = rej; img.src = url; });
    const canvas = document.createElement('canvas');
    canvas.width = W; canvas.height = H;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#10151d';
    ctx.fillRect(0, 0, W, H);
    const pad = Math.round(W * 0.03);
    ctx.drawImage(img, pad, pad, W - 2 * pad, H - 2 * pad);
    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.anisotropy = 8;
    return { texture, w: W, h: H };
  } catch {
    return null;
  } finally {
    URL.revokeObjectURL(url);
  }
}
