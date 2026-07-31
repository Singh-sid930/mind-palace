// Speech-bubble conversation with the companion. Talks to serve.py's
// /api/companion/chat endpoint, which proxies the local Ollama service.
// Long answers arrive as a short bubble + a link to a saved scroll.

export class CompanionChat {
  constructor({ getLocation, onThinking }) {
    this.getLocation = getLocation;
    this.onThinking = onThinking || (() => {});
    this.history = [];
    this.busy = false;
    this.healthChecked = false;
    this.offline = false;     // true when hosted with no companion backend (e.g. GitHub Pages)
    this.gateCtx = null;      // set by main when near a gated passage
    this._primedFor = null;   // which gate the Gatekeeper has already greeted

    this.panel = document.getElementById('chat-panel');
    this.log = document.getElementById('chat-log');
    this.input = document.getElementById('chat-input');

    this.input.addEventListener('keydown', (e) => {
      e.stopPropagation();
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.send();
      }
      if (e.key === 'Escape') this.close();
    });
  }

  get isOpen() { return this.panel.style.display === 'block'; }

  open() {
    this.panel.style.display = 'block';
    this.input.placeholder = this.offline ? '(the sage is silent here)'
      : this.gateCtx ? 'answer the Gatekeeper…' : 'ask Gemma…';
    if (!this.offline) setTimeout(() => this.input.focus(), 0);
    // No companion backend (a static host): explain once, gently, in-world.
    if (this.offline) {
      if (!this.healthChecked) {
        this.healthChecked = true;
        this._bubble('gemma',
          'The Whispering Sage keeps to the home palace — her voice does not ' +
          'carry to this realm. Wander freely; every chamber is still yours to read.');
      }
      if (this.gateCtx && this._primedFor !== this.gateCtx.dest) {
        this._primedFor = this.gateCtx.dest;
        this._bubble('gate',
          `✦ A Gatekeeper bars the way to “${this.gateCtx.dest}.” It is wordless ` +
          'in this realm — press E to pass.');
      }
      return;
    }
    if (!this.healthChecked) {
      this.healthChecked = true;
      this._checkHealth();
    }
    // If the keeper opened the chat at a gated passage, the Gatekeeper greets
    // and poses its first question (once per gate approached).
    if (this.gateCtx && this._primedFor !== this.gateCtx.dest) {
      this._primedFor = this.gateCtx.dest;
      this._startGate();
    }
  }

  setOffline(v) { this.offline = v; }

  setGate(ctx) {
    // ctx: { dest, persona, prereqs:[{name,summary}] } or null.
    this.gateCtx = ctx;
    if (!ctx) this._primedFor = null;
    if (this.isOpen) this.input.placeholder = ctx ? 'answer the Gatekeeper…' : 'ask Gemma…';
  }

  _startGate() {
    this._bubble('gate', `✦ A Gatekeeper bars the way to “${this.gateCtx.dest}.” It will test you — answer, or press E to pass regardless.`);
    // Prime the model to greet and ask its first question (not shown as "you").
    this.send('(I approach your gate, seeking passage. Test my readiness.)', { silent: true });
  }

  close() {
    this.panel.style.display = 'none';
    this.input.blur();
  }

  toggle() {
    if (this.isOpen) this.close(); else this.open();
    return this.isOpen;
  }

  async _checkHealth() {
    try {
      const res = await fetch('/api/companion/health').then((r) => r.json());
      if (!res.ok) {
        this._bubble('gemma',
          '(Gemma seems to be asleep — the Ollama service is not answering. ' +
          'Is it running on this machine?)');
      } else if (!res.model_present) {
        this._bubble('gemma',
          `(Gemma stirs, but her voice is missing — model “${res.model}” ` +
          'is not available in Ollama.)');
      } else if (this.history.length === 0 && !this.gateCtx) {
        this._bubble('gemma',
          'Hello, keeper. Ask me anything about what you see — press T anytime.');
      }
    } catch {
      this._bubble('gemma', '(The palace server is not answering.)');
    }
  }

  _bubble(who, text, scrollUrl = null) {
    const div = document.createElement('div');
    div.className = `bubble ${who}`;
    div.textContent = text;
    if (scrollUrl) {
      const a = document.createElement('a');
      a.href = scrollUrl;
      a.target = '_blank';
      a.textContent = '📜 read the full scroll';
      a.className = 'scroll-link';
      div.appendChild(document.createElement('br'));
      div.appendChild(a);
    }
    this.log.appendChild(div);
    this.log.scrollTop = this.log.scrollHeight;
    return div;
  }

  async send(overrideText = null, opts = {}) {
    const message = overrideText != null ? overrideText : this.input.value.trim();
    if (!message || this.busy) return;
    if (overrideText == null) this.input.value = '';
    if (this.offline) {
      if (!opts.silent) this._bubble('you', message);
      this._bubble('gemma', '(no answer comes — the sage is silent in this realm)');
      return;
    }
    const who = this.gateCtx ? 'gate' : 'gemma';
    if (!opts.silent) this._bubble('you', message);
    const pending = this._bubble(who, '…');
    pending.classList.add('pending');

    this.busy = true;
    this.onThinking(true);
    try {
      const res = await fetch('/api/companion/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          history: this.history.slice(-12),
          location: this.getLocation(),
          gate: this.gateCtx || null,
        }),
      });
      const data = await res.json();
      pending.remove();
      if (data.error) {
        this._bubble(who, `(Something went wrong: ${data.error})`);
      } else {
        this._bubble(who, data.bubble, data.scroll_url);
        this.history.push({ role: 'user', content: message });
        this.history.push({ role: 'assistant', content: data.bubble });
      }
    } catch (e) {
      pending.remove();
      this._bubble(who, `(The connection to the palace server failed: ${e.message})`);
    } finally {
      this.busy = false;
      this.onThinking(false);
    }
  }
}
