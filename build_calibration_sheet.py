#!/usr/bin/env python3
"""Build Tyler's blind calibration sheet.

20 pieces, mixed order: 10 the subject gate overturned (override_reject) and
10 it passed (accept). Each card shows only the render and the INTENDED
subject -- the gate's verdict, the curator's critique and the piece's own
notes are kept in manifest.json, which the page never reads.

Everything lands under workspace/, which .gitignore excludes wholesale, so
none of it can reach a repo.

Run: python3 build_calibration_sheet.py
"""
import base64
import glob
import json
import os
import random
import sqlite3
import sys

sys.path.insert(0, os.path.expanduser("~/agentscii"))
import harness  # noqa: E402

ROOT = os.path.expanduser("~/agentscii")
WS = os.path.join(ROOT, "workspace")
# Outside workspace/: the seats browse workspace/ and have cat'd .md files
# there wholesale. Tyler's answers must not be readable by the agents they
# judge.
OUT = os.path.expanduser("~/agentscii-private/calibration/sheet")
N_PER_SIDE = 10
SEED = 20261001        # fixed so a rebuild keeps the same sheet


def locate(dest_path):
    """A piece's current file. Accepts get moved from unpacked/ into packNN/."""
    direct = os.path.join(WS, dest_path)
    if os.path.exists(direct):
        return direct
    hits = glob.glob(os.path.join(WS, "gallery", "pack*", os.path.basename(dest_path)))
    return hits[0] if hits else None


def pool(conn, action, limit):
    """Distinct pieces for one verdict, newest first.

    Deduped by slug first so the sheet isn't ten versions of one subject; if
    that leaves us short (only 9 override_reject slugs carry an intended
    title), a second pass admits a different VERSION of an already-used slug
    rather than shipping an unbalanced sheet.
    """
    rows = conn.execute(
        "SELECT shift_id, path, dest_path FROM curation_events "
        "WHERE action=? AND dest_path IS NOT NULL ORDER BY id DESC", (action,)
    ).fetchall()
    out, seen_slug, seen_file = [], set(), set()

    def consider(shift_id, dest, allow_dup_slug):
        base = os.path.basename(dest)
        slug = harness.core_slug(os.path.splitext(base)[0])
        if base in seen_file or (slug in seen_slug and not allow_dup_slug):
            return False
        f = locate(dest)
        if not f:
            return False
        title = harness._extract_intended_title(f) or ""
        if not title.strip():
            return False      # no intended subject -> nothing to judge against
        b64, _note = harness.render_ans_to_png_b64(f, offset=0, max_rows=4000)
        if not b64:
            return False
        seen_slug.add(slug)
        seen_file.add(base)
        out.append({"slug": slug, "file": os.path.relpath(f, ROOT),
                    "intended": title.strip(), "verdict": action,
                    "shift_id": shift_id, "png_b64": b64})
        return True

    for allow_dup in (False, True):
        for shift_id, _src, dest in rows:
            if len(out) >= limit:
                break
            consider(shift_id, dest, allow_dup)
        if len(out) >= limit:
            break
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    conn = sqlite3.connect(os.path.join(ROOT, "state.db"))
    rejects = pool(conn, "override_reject", N_PER_SIDE)
    accepts = pool(conn, "accept", N_PER_SIDE)
    print(f"  override_reject: {len(rejects)}   accept: {len(accepts)}")
    if len(rejects) < N_PER_SIDE or len(accepts) < N_PER_SIDE:
        print("  WARNING: short of 10 on one side -- sheet will be unbalanced")

    items = rejects + accepts
    random.Random(SEED).shuffle(items)
    for i, it in enumerate(items, 1):
        it["id"] = i

    # Hidden side: verdicts, never read by the page.
    with open(os.path.join(OUT, "manifest.json"), "w") as f:
        json.dump([{k: v for k, v in it.items() if k != "png_b64"} for it in items],
                  f, indent=2)

    # Visible side: id, intended subject, image. No verdict, no slug, no path.
    cards = [{"id": it["id"], "intended": it["intended"], "img": it["png_b64"]}
             for it in items]
    html = TEMPLATE.replace("__CARDS__", json.dumps(cards))
    page = os.path.join(OUT, "index.html")
    with open(page, "w") as f:
        f.write(html)
    print(f"  wrote {page} ({os.path.getsize(page)//1024} KB, {len(cards)} pieces)")
    print(f"  hidden verdicts in {os.path.join(OUT, 'manifest.json')}")


TEMPLATE = r"""<!doctype html>
<meta charset="utf-8">
<title>AGENTSCII calibration</title>
<style>
  :root { color-scheme: dark; }
  body { background:#0b0b0d; color:#d8d8dc; font:14px/1.5 -apple-system,BlinkMacSystemFont,sans-serif;
         margin:0; padding:32px 24px 120px; }
  h1 { font-size:18px; font-weight:600; margin:0 0 4px; }
  .sub { color:#8a8a92; margin:0 0 28px; }
  .card { border:1px solid #26262c; border-radius:10px; margin:0 0 22px; overflow:hidden; background:#101014; }
  .head { display:flex; align-items:baseline; gap:12px; padding:12px 16px; border-bottom:1px solid #26262c; }
  .n { color:#6a6a72; font-variant-numeric:tabular-nums; }
  .subj { font-weight:600; }
  .subj span { color:#8a8a92; font-weight:400; }
  .imgwrap { background:#000; padding:14px; overflow:auto; }
  img { display:block; image-rendering:pixelated; max-width:100%; }
  .row { display:flex; gap:10px; align-items:center; padding:12px 16px; flex-wrap:wrap; }
  button { font:inherit; padding:7px 15px; border-radius:7px; border:1px solid #33333c;
           background:#1a1a20; color:#d8d8dc; cursor:pointer; }
  button:hover { border-color:#4a4a56; }
  button.on-yes { background:#16432a; border-color:#2e7d4f; color:#b6f0cb; }
  button.on-no  { background:#4a1d1d; border-color:#8a3434; color:#f3bcbc; }
  input[type=text] { flex:1; min-width:220px; font:inherit; padding:7px 10px; border-radius:7px;
                     border:1px solid #33333c; background:#141418; color:#d8d8dc; }
  .bar { position:fixed; left:0; right:0; bottom:0; background:#141418; border-top:1px solid #26262c;
         padding:12px 24px; display:flex; gap:16px; align-items:center; }
  .bar b { font-variant-numeric:tabular-nums; }
  .save { background:#1e3a5f; border-color:#2f5d94; color:#cfe3ff; }
  .note { color:#8a8a92; }
</style>
<h1>Calibration — does the piece read as its intended subject?</h1>
<p class="sub">20 pieces, mixed order. Judge the render on its own; the intended subject is
the only context. Gate and curator verdicts are hidden. Answers download as
<code>calibration_tyler.json</code> — keep it out of <code>workspace/</code>
(the agents browse there); <code>~/agentscii-private/calibration/</code>.</p>
<div id="cards"></div>
<div class="bar">
  <span>answered <b id="count">0</b>/<b id="total">0</b></span>
  <button class="save" onclick="save()">Download answers</button>
  <span class="note" id="status">autosaved in this browser as you go</span>
</div>
<script>
const CARDS = __CARDS__;
const KEY = 'agentscii_calibration_v1';
let answers = JSON.parse(localStorage.getItem(KEY) || '{}');

function render() {
  const root = document.getElementById('cards');
  root.innerHTML = '';
  for (const c of CARDS) {
    const a = answers[c.id] || {};
    const el = document.createElement('div');
    el.className = 'card';
    el.innerHTML = `
      <div class="head"><span class="n">${c.id}/${CARDS.length}</span>
        <span class="subj">intended: <span>${c.intended.replace(/</g,'&lt;')}</span></span></div>
      <div class="imgwrap"><img src="data:image/png;base64,${c.img}" alt=""></div>
      <div class="row">
        <button class="${a.reads === true ? 'on-yes' : ''}" data-id="${c.id}" data-v="1">reads as subject</button>
        <button class="${a.reads === false ? 'on-no' : ''}" data-id="${c.id}" data-v="0">doesn't</button>
        <input type="text" placeholder="note (optional)" data-note="${c.id}" value="${(a.note||'').replace(/"/g,'&quot;')}">
      </div>`;
    root.appendChild(el);
  }
  document.getElementById('total').textContent = CARDS.length;
  document.getElementById('count').textContent =
    Object.values(answers).filter(a => a.reads === true || a.reads === false).length;
}
document.addEventListener('click', e => {
  const b = e.target.closest('button[data-id]'); if (!b) return;
  const id = b.dataset.id;
  answers[id] = Object.assign({}, answers[id], {reads: b.dataset.v === '1'});
  localStorage.setItem(KEY, JSON.stringify(answers));
  render();
});
document.addEventListener('input', e => {
  const t = e.target.closest('input[data-note]'); if (!t) return;
  const id = t.dataset.note;
  answers[id] = Object.assign({}, answers[id], {note: t.value});
  localStorage.setItem(KEY, JSON.stringify(answers));
});
function save() {
  const out = CARDS.map(c => ({
    id: c.id, intended: c.intended,
    reads_as_subject: answers[c.id] ? answers[c.id].reads : null,
    note: (answers[c.id] && answers[c.id].note) || ''
  }));
  const blob = new Blob([JSON.stringify(out, null, 2)], {type: 'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'calibration_tyler.json';
  a.click();
  document.getElementById('status').textContent = 'downloaded — move it into workspace/';
}
render();
</script>
"""

if __name__ == "__main__":
    main()
