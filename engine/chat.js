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
    setTimeout(() => this.input.focus(), 0);
    if (!this.healthChecked) {
      this.healthChecked = true;
      this._checkHealth();
    }
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
      } else if (this.history.length === 0) {
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

  async send() {
    const message = this.input.value.trim();
    if (!message || this.busy) return;
    this.input.value = '';
    this._bubble('you', message);
    const pending = this._bubble('gemma', '…');
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
        }),
      });
      const data = await res.json();
      pending.remove();
      if (data.error) {
        this._bubble('gemma', `(Something went wrong: ${data.error})`);
      } else {
        this._bubble('gemma', data.bubble, data.scroll_url);
        this.history.push({ role: 'user', content: message });
        this.history.push({ role: 'assistant', content: data.bubble });
      }
    } catch (e) {
      pending.remove();
      this._bubble('gemma', `(The connection to the palace server failed: ${e.message})`);
    } finally {
      this.busy = false;
      this.onThinking(false);
    }
  }
}
