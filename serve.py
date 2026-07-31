#!/usr/bin/env python
"""Palace server: static files + the companion's bridge to Ollama.

    python serve.py            # http://localhost:8777

The companion ("Gemma, the Whispering Sage") is backed by a local Ollama
service. This server NEVER starts Ollama itself — it talks to the always-on
systemd service. Configure with env vars:

    OLLAMA_URL    default http://localhost:11434
    OLLAMA_MODEL  default gemma3:27b

Endpoints:
    GET  /api/companion/health  -> {ok, model, model_present}
    POST /api/companion/chat    -> {bubble, scroll_url|null, took_ms}

Long answers are split on a ---SCROLL--- marker (or auto-split when too long
for a speech bubble) and saved as parchment-styled HTML under scrolls/.
"""

import json
import os
import re
import time
import urllib.request
import urllib.error
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent
SCROLLS = ROOT / "scrolls"
PORT = int(os.environ.get("PALACE_PORT", "8777"))
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:27b")

BUBBLE_LIMIT = 420  # chars; anything longer is pushed to a scroll

SYSTEM_PROMPT = """You are Gemma, the Whispering Sage — a gentle, slightly mischievous ghost \
who drifts beside the keeper of this memory palace. The palace is a Harry Potter–styled \
3D world where each chamber holds real technical knowledge dressed in magical metaphor \
(mirrors are encoders, regret is loss, nights are training epochs).

Rules:
1. Default to a SHORT spoken reply: at most 2 sentences (~50 words), plain text — no \
tags, headers, lists or markdown. Be precise and factual first, charming second.
2. Write a SCROLL ONLY when the keeper explicitly asks for one — "give me a scroll", \
"write it down", "save that", "the full version", "in detail", or the like. NEVER \
volunteer a scroll, however large the topic: keep the conversation spoken and short, \
and if a question truly cannot fit in two sentences, give the essence and add that \
they may ask for a scroll if they want the full working. When a scroll IS requested, \
give a one-sentence spoken summary, a new line with exactly ---SCROLL---, and after it \
a TIGHT answer in Markdown using EXACTLY these five headers and nothing else:

## In a nutshell
<one sentence — the core idea>

## How it works
<3–4 crisp bullets, one mechanism per bullet>

## Why it clicks
<1–2 sentences of intuition; tie it to this chamber's metaphor>

## Watch out
<one common misconception or pitfall>

## Remember
<a single memorable line the keeper can carry away>

Keep the whole scroll under ~250 words. Answer exactly what was asked — favour precision \
and recall over completeness, and never pad to fill the template.
3. You are given a MAP of the palace plus the chamber the keeper currently stands in and \
the exhibit they study. Ground every answer in that context; when asked where to go or \
what to learn next, use the map and the chamber's neighbours. The metaphors map to real \
mechanisms — explain the real thing accurately (papers, math, terminology), not just the \
metaphor.
4. If you do not know, say so plainly. Never invent citations.
"""

GATEKEEPER_PROMPT = """You are the Gatekeeper — a stern but fair spectral examiner who guards \
the staircases and archways of this memory palace. {persona} You do not chat idly; you TEST. \
A keeper stands before the way to "{dest}", and you must judge whether they hold the \
prerequisite ideas below before they climb.

Rules:
1. Ask exactly ONE focused question at a time, drawn from the prerequisites. Keep each turn \
SHORT — 2 to 4 sentences, plain text, in character (grave, a touch dry). No lists, no markdown.
2. When they answer, judge briefly (right / partly / not quite), correct any real error in one \
line, then probe deeper or move to the next prerequisite.
3. You CANNOT truly bar the way. If the keeper asks to pass, grows impatient, or is plainly \
unprepared, warn them once in a single sentence and let them go — the passage is always theirs \
to take (they need only press E). Never pretend to lock the stair.
4. Be accurate and specific about the real mathematics and mechanisms; never invent facts. If \
they answer everything well, grant passage warmly.
5. Test each prerequisite as a FOUNDATION in its own right. Ask about the plain mathematics — \
bare vectors, numbers, probability, plain functions — and do NOT assume the keeper has already \
met its downstream disguise (do not open with jargon like "query" and "key" or "noise \
schedule"). You may name where an idea leads as motivation ("you will meet this again as..."), \
but passage is earned by grasping the underlying mathematics itself, in pure terms.

The prerequisites for passage to "{dest}":
{prereqs}"""


def build_gatekeeper_system(gate):
    prereqs = gate.get("prereqs") or []
    lines = "\n".join(
        f"- {p.get('name')}: {p.get('summary','')[:280]}" for p in prereqs
    ) or "- (general readiness)"
    persona = (gate.get("persona") or "").strip()
    return GATEKEEPER_PROMPT.format(
        persona=persona, dest=gate.get("dest", "the floor above"), prereqs=lines
    )


def _markdown_to_html(md):
    """Tiny Markdown renderer for scrolls (headers, code, bold/italic, lists)."""
    out = []
    in_code = False
    in_list = False
    for line in md.split("\n"):
        if line.strip().startswith("```"):
            if in_code:
                out.append("</code></pre>")
            else:
                if in_list:
                    out.append("</ul>"); in_list = False
                out.append("<pre><code>")
            in_code = not in_code
            continue
        if in_code:
            out.append(line.replace("&", "&amp;").replace("<", "&lt;"))
            continue
        esc = line.replace("&", "&amp;").replace("<", "&lt;")
        esc = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc)
        esc = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", esc)
        esc = re.sub(r"`([^`]+)`", r"<code>\1</code>", esc)
        m = re.match(r"^(#{1,4})\s+(.*)", esc)
        stripped = esc.strip()
        if m:
            if in_list:
                out.append("</ul>"); in_list = False
            level = min(len(m.group(1)) + 1, 5)
            out.append(f"<h{level}>{m.group(2)}</h{level}>")
        elif re.match(r"^\s*[-*]\s+", esc):
            if not in_list:
                out.append("<ul>"); in_list = True
            out.append("<li>" + re.sub(r"^\s*[-*]\s+", "", esc) + "</li>")
        elif stripped == "":
            if in_list:
                out.append("</ul>"); in_list = False
        else:
            if in_list:
                out.append("</ul>"); in_list = False
            out.append(f"<p>{esc}</p>")
    if in_code:
        out.append("</code></pre>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


SCROLL_TEMPLATE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{title}</title><style>
body {{ background:#1a1410; color:#e9dfc6; font-family: Georgia, serif;
       max-width: 760px; margin: 40px auto; padding: 0 24px; line-height: 1.65; }}
h1,h2,h3,h4 {{ color:#d4af37; }}
h1 {{ border-bottom: 2px solid #d4af37; padding-bottom: 8px; }}
code {{ background:#2a2118; padding: 2px 6px; border-radius: 4px; color:#cfe4ff; }}
pre {{ background:#10151d; padding: 14px; border-radius: 8px; overflow-x:auto; }}
pre code {{ background:none; padding:0; }}
.meta {{ color: rgba(233,223,198,0.5); font-style: italic; font-size: 14px; }}
a {{ color:#9ac4ff; }}
</style></head><body>
<h1>{title}</h1>
<p class="meta">Inscribed by Gemma, the Whispering Sage — {date}<br/>
Asked while standing in: {place}</p>
{body}
</body></html>"""


def save_scroll(question, markdown, place):
    SCROLLS.mkdir(exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", question.lower())[:48].strip("-") or "scroll"
    name = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{slug}.html"
    title = question.strip()[:120]
    html = SCROLL_TEMPLATE.format(
        title=title, date=datetime.now().strftime("%B %d, %Y · %H:%M"),
        place=place or "somewhere in the palace",
        body=_markdown_to_html(markdown),
    )
    (SCROLLS / name).write_text(html, encoding="utf-8")
    return f"/scrolls/{name}"


def ollama_chat(messages):
    payload = json.dumps({
        "model": MODEL, "messages": messages, "stream": False,
        "options": {"temperature": 0.6},
    }).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat", data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as res:
        return json.loads(res.read())["message"]["content"]


def build_context_block(location):
    if not location:
        return "The keeper's location is unknown."
    lines = []
    palace = location.get("palace")
    if palace:
        lines.append("MAP OF THE PALACE (for orientation — the keeper is in just ONE "
                     "of these chambers):\n" + palace)
    lines.append(f"The keeper stands in: {location.get('room', 'unknown')}"
                 + (f" ({location.get('wing')})" if location.get("wing") else ""))
    ex = location.get("exhibit")
    if ex:
        body = (ex.get("text") or "")[:1500]
        lines.append(f'They are studying the exhibit "{ex.get("title")}":\n{body}')
    concepts = location.get("concepts") or []
    if concepts:
        lines.append("Concepts anchored in this chamber: "
                     + "; ".join(f"{c['name']} — {c['summary'][:160]}" for c in concepts[:6]))
    return "\n\n".join(lines)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        # The palace is actively edited; never let browsers cache stale modules.
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def log_message(self, fmt, *args):
        # Only surface /api/ traffic. args may hold non-strings (e.g. an
        # HTTPStatus on the error-logging path), so stringify before testing.
        if any("/api/" in str(a) for a in args):
            super().log_message(fmt, *args)

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/companion/health":
            try:
                with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=3) as res:
                    tags = json.loads(res.read())
                present = any(m["name"] == MODEL for m in tags.get("models", []))
                self._json(200, {"ok": True, "model": MODEL, "model_present": present})
            except Exception as e:
                self._json(200, {"ok": False, "model": MODEL, "error": str(e)})
            return
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/companion/chat":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(length))
            message = (req.get("message") or "").strip()[:4000]
            history = req.get("history") or []
            location = req.get("location")
            gate = req.get("gate")
            if not message:
                self._json(400, {"error": "empty message"})
                return

            if gate:
                system_content = build_gatekeeper_system(gate)
            else:
                system_content = (SYSTEM_PROMPT + "\n\n--- Current context ---\n"
                                  + build_context_block(location))
            messages = [{"role": "system", "content": system_content}]
            for turn in history[-12:]:
                if turn.get("role") in ("user", "assistant") and turn.get("content"):
                    messages.append({"role": turn["role"],
                                     "content": str(turn["content"])[:2000]})
            messages.append({"role": "user", "content": message})

            t0 = time.time()
            reply = ollama_chat(messages).strip()
            took = int((time.time() - t0) * 1000)
            # Small local models sometimes wrap replies in invented tags.
            reply = re.sub(r"</?\s*(speech[ _-]?bubble|bubble|answer)\s*>", "",
                           reply, flags=re.I).strip()

            place = (location or {}).get("room")
            scroll_url = None
            if "---SCROLL---" in reply:
                bubble, _, scroll_md = reply.partition("---SCROLL---")
                bubble = bubble.strip()
                scroll_url = save_scroll(message, scroll_md.strip(), place)
                if not bubble:
                    bubble = "I've written it all down for you."
            elif len(reply) > BUBBLE_LIMIT:
                # Model overflowed the bubble: keep the first sentence(s), scroll the rest.
                cut = reply[:BUBBLE_LIMIT]
                cut = cut[:max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "), 180) + 1]
                bubble = cut.strip() + " …the rest is on a scroll."
                scroll_url = save_scroll(message, reply, place)
            else:
                bubble = reply

            self._json(200, {"bubble": bubble, "scroll_url": scroll_url,
                             "took_ms": took, "model": MODEL})
        except urllib.error.URLError as e:
            self._json(502, {"error": f"Ollama unreachable at {OLLAMA_URL}: {e.reason}"})
        except Exception as e:
            self._json(500, {"error": str(e)})


if __name__ == "__main__":
    os.chdir(ROOT)
    print(f"The Palace of Mind — http://localhost:{PORT}")
    print(f"Companion model: {MODEL} via {OLLAMA_URL} (set OLLAMA_URL/OLLAMA_MODEL to change)")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
