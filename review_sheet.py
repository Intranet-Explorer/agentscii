#!/usr/bin/env python3
"""Manual publication review for pieces waiting in workspace/pending/.

Same shape as the calibration sheet, but titles are SHOWN (this is the
publish decision, not a blind test) and there are three answers per piece:
reads as subject, well made, publish. Answers land in
workspace/reviews/<date>.json.

  python3 review_sheet.py            # build the sheet for workspace/pending/
  python3 review_sheet.py --apply F  # move approved pieces -> gallery/unpacked/

Approved pieces land in gallery/unpacked/, which release_pack already reads,
so packing and syncing are unchanged.
"""
import datetime
import glob
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.expanduser("~/agentscii"))
import harness  # noqa: E402

ROOT = os.path.expanduser("~/agentscii")
PENDING = os.path.join(ROOT, "workspace", "pending")
UNPACKED = os.path.join(ROOT, "workspace", "gallery", "unpacked")
OUT = os.path.join(ROOT, "workspace", "reviews")
SIDECARS = (".note.txt", ".critique.txt", ".credits.txt")


def pieces():
    return sorted(f for f in glob.glob(os.path.join(PENDING, "*.ans"))
                  if not f.endswith(SIDECARS))


def build():
    os.makedirs(OUT, exist_ok=True)
    today = datetime.date.today().isoformat()
    answers_path = os.path.join(OUT, f"{today}.json")

    cards = []
    for i, f in enumerate(pieces(), 1):
        b64, _n = harness.render_ans_to_png_b64(f, offset=0, max_rows=4000)
        if not b64:
            print(f"  skip {os.path.basename(f)}: render failed")
            continue
        crit = f.replace(".ans", ".critique.txt")
        cards.append({
            "id": i,
            "file": os.path.basename(f),
            "title": harness._extract_intended_title(f) or os.path.basename(f),
            "critique": (open(crit).read()[:600] if os.path.exists(crit) else ""),
            "img": b64,
        })
    if not cards:
        print(f"  nothing to review in {PENDING}")
        return

    page = os.path.join(OUT, f"{today}.html")
    with open(page, "w") as fh:
        fh.write(TEMPLATE.replace("__CARDS__", json.dumps(cards))
                         .replace("__DATE__", today))
    print(f"  wrote {page} ({os.path.getsize(page)//1024} KB, {len(cards)} pieces)")
    print(f"  answers download as {today}.json -> put it in {OUT}/")
    print(f"  then: python3 review_sheet.py --apply {answers_path}")


def apply(answers_file):
    """Move pieces marked publish=true into gallery/unpacked/, with sidecars."""
    answers = json.load(open(answers_file))
    os.makedirs(UNPACKED, exist_ok=True)
    moved = held = 0
    for a in answers:
        src = os.path.join(PENDING, a["file"])
        if not os.path.exists(src):
            print(f"  MISSING {a['file']} (already moved?)")
            continue
        if not a.get("publish"):
            held += 1
            continue
        shutil.move(src, os.path.join(UNPACKED, a["file"]))
        for ext in SIDECARS:                      # keep critique/note with it
            s = src.replace(".ans", ext)
            if os.path.exists(s):
                shutil.move(s, os.path.join(UNPACKED, os.path.basename(s)))
        harness._log_curation_event(None, "publish_approved", a["file"],
                                    f"gallery/unpacked/{a['file']}",
                                    f"reads={a.get('reads')} good={a.get('good')} "
                                    f"note={a.get('note', '')[:200]}")
        moved += 1
        print(f"  published {a['file']}")
    print(f"  {moved} moved to gallery/unpacked/, {held} held in pending/")
    if moved:
        print("  run release_pack (curator tool) to pack and sync as usual")


TEMPLATE = r"""<!doctype html>
<meta charset="utf-8">
<title>AGENTSCII review __DATE__</title>
<style>
  :root { color-scheme: dark; }
  body { background:#0b0b0d; color:#d8d8dc; font:14px/1.5 -apple-system,BlinkMacSystemFont,sans-serif;
         margin:0; padding:32px 24px 120px; }
  h1 { font-size:18px; font-weight:600; margin:0 0 4px; }
  .sub { color:#8a8a92; margin:0 0 28px; }
  .card { border:1px solid #26262c; border-radius:10px; margin:0 0 22px; background:#101014; overflow:hidden; }
  .head { padding:12px 16px; border-bottom:1px solid #26262c; display:flex; gap:12px; align-items:baseline; }
  .n { color:#6a6a72; font-variant-numeric:tabular-nums; }
  .title { font-weight:600; }
  .fn { color:#6a6a72; font-size:12px; margin-left:auto; }
  .imgwrap { background:#000; padding:14px; overflow:auto; }
  img { display:block; image-rendering:pixelated; max-width:100%; }
  .crit { color:#7a7a84; font-size:12px; padding:10px 16px; border-top:1px solid #1c1c22;
          white-space:pre-wrap; max-height:90px; overflow:auto; }
  .qs { padding:10px 16px 14px; }
  .q { display:flex; gap:8px; align-items:center; margin:6px 0; }
  .q label { width:132px; color:#9a9aa4; }
  button { font:inherit; padding:5px 13px; border-radius:7px; border:1px solid #33333c;
           background:#1a1a20; color:#d8d8dc; cursor:pointer; }
  button:hover { border-color:#4a4a56; }
  button.yes { background:#16432a; border-color:#2e7d4f; color:#b6f0cb; }
  button.no  { background:#4a1d1d; border-color:#8a3434; color:#f3bcbc; }
  input[type=text] { width:100%; box-sizing:border-box; font:inherit; padding:7px 10px; margin-top:4px;
                     border-radius:7px; border:1px solid #33333c; background:#141418; color:#d8d8dc; }
  .bar { position:fixed; left:0; right:0; bottom:0; background:#141418; border-top:1px solid #26262c;
         padding:12px 24px; display:flex; gap:16px; align-items:center; }
  .bar b { font-variant-numeric:tabular-nums; }
  .save { background:#1e3a5f; border-color:#2f5d94; color:#cfe3ff; }
</style>
<h1>Publication review — __DATE__</h1>
<p class="sub">Pieces the curator accepted, waiting in <code>workspace/pending/</code>.
Nothing is published until you mark <b>publish</b>. Titles are shown; this is the
publish decision, not a blind test.</p>
<div id="cards"></div>
<div class="bar">
  <span>publish-decided <b id="count">0</b>/<b id="total">0</b></span>
  <button class="save" onclick="save()">Download decisions</button>
  <span id="status" style="color:#8a8a92">autosaved in this browser</span>
</div>
<script>
const CARDS = __CARDS__;
const KEY = 'agentscii_review___DATE__';
let A = JSON.parse(localStorage.getItem(KEY) || '{}');
const QS = [['reads','reads as subject'],['good','well made'],['publish','publish']];

function render() {
  const root = document.getElementById('cards');
  root.innerHTML = '';
  for (const c of CARDS) {
    const a = A[c.id] || {};
    const qs = QS.map(([k, lbl]) => `
      <div class="q"><label>${lbl}</label>
        <button class="${a[k] === true ? 'yes' : ''}" data-id="${c.id}" data-k="${k}" data-v="1">yes</button>
        <button class="${a[k] === false ? 'no' : ''}"  data-id="${c.id}" data-k="${k}" data-v="0">no</button>
      </div>`).join('');
    const el = document.createElement('div');
    el.className = 'card';
    el.innerHTML = `
      <div class="head"><span class="n">${c.id}/${CARDS.length}</span>
        <span class="title">${c.title.replace(/</g,'&lt;')}</span>
        <span class="fn">${c.file}</span></div>
      <div class="imgwrap"><img src="data:image/png;base64,${c.img}" alt=""></div>
      ${c.critique ? `<div class="crit">${c.critique.replace(/</g,'&lt;')}</div>` : ''}
      <div class="qs">${qs}
        <input type="text" placeholder="note (optional)" data-note="${c.id}"
               value="${(a.note||'').replace(/"/g,'&quot;')}"></div>`;
    root.appendChild(el);
  }
  document.getElementById('total').textContent = CARDS.length;
  document.getElementById('count').textContent =
    Object.values(A).filter(a => a.publish === true || a.publish === false).length;
}
document.addEventListener('click', e => {
  const b = e.target.closest('button[data-id]'); if (!b) return;
  const id = b.dataset.id;
  A[id] = Object.assign({}, A[id], {[b.dataset.k]: b.dataset.v === '1'});
  localStorage.setItem(KEY, JSON.stringify(A)); render();
});
document.addEventListener('input', e => {
  const t = e.target.closest('input[data-note]'); if (!t) return;
  A[t.dataset.note] = Object.assign({}, A[t.dataset.note], {note: t.value});
  localStorage.setItem(KEY, JSON.stringify(A));
});
function save() {
  const out = CARDS.map(c => Object.assign(
    {file: c.file, title: c.title, reads: null, good: null, publish: null, note: ''},
    A[c.id] || {}));
  const blob = new Blob([JSON.stringify(out, null, 2)], {type:'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = '__DATE__.json'; a.click();
  document.getElementById('status').textContent = 'downloaded — move it into workspace/reviews/';
}
render();
</script>
"""

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--apply":
        apply(sys.argv[2])
    else:
        build()
