#!/usr/bin/env python3
"""Manual publication review for pieces waiting in workspace/pending/.

Same shape as the calibration sheet, but titles are SHOWN (this is the
publish decision, not a blind test) and there are three answers per piece:
reads as subject, well made, publish. Answers land in
workspace/reviews/<date>.json.

  python3 review_sheet.py                         # build the sheet
  python3 review_sheet.py --apply F               # publish + tell the agents
  python3 review_sheet.py --apply F --no-deliver  # publish, HOLD the verdicts
  python3 review_sheet.py --deliver-baseline      # release the held batch

--no-deliver is for batch 1, the no-feedback baseline: it publishes and
records the verdicts in ~/agentscii-private/baseline_reviews.md -- outside
the repo and outside agent-browsable workspace/ -- without messaging the
agents and without touching REVIEWS.md, which the seat prompts point at.

Approved pieces land in gallery/unpacked/, which release_pack already reads,
so packing and syncing are unchanged.
"""
import datetime
import glob
import json
import os
import shutil
import sqlite3
import sys
import time

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


def _yn(v):
    return "yes" if v is True else ("no" if v is False else "—")


REVIEWS_MD = os.path.join(ROOT, "workspace", "REVIEWS.md")

# Held batch lives OUTSIDE the repo and outside workspace/, because workspace/
# is agent-browsable: the seats have run `ls workspace/` 339 times and three
# shifts cat'd a workspace .md wholesale. workspace/reviews/baseline.md would
# sit one `cat` away from the agents it is meant to be hidden from.
PRIVATE = os.path.expanduser("~/agentscii-private")
BASELINE_MD = os.path.join(PRIVATE, "baseline_reviews.md")

REVIEWS_HEAD = ("# Operator reviews\n\nTyler's own verdicts on finished pieces "
                "-- the only judgement that decides publishing. Newest first.\n")
BASELINE_HEAD = (
    "# HELD baseline reviews -- NOT delivered to the agents\n\n"
    "Batch 1 is the no-feedback baseline: the agents work under the new seat "
    "prompts but have not seen a single verdict. Delivering these would "
    "destroy the before/after. Release with:\n"
    "    python3 review_sheet.py --deliver-baseline\n"
    "which messages both seats and moves these entries into REVIEWS.md.\n")

BATCH_MARK = " -- BASELINE (not delivered)"
HOLD_NOTE = "held, not delivered"


def _batch_body(answers):
    """One markdown block for a reviewed batch. Blank rows are skipped."""
    lines = []
    for a in answers:
        if a.get("reads") is None and a.get("good") is None and a.get("publish") is None:
            continue                                   # never looked at
        slug = harness.core_slug(os.path.splitext(a["file"])[0])
        note = (a.get("note") or "").strip()
        lines.append(f"- {slug}: reads as subject {_yn(a.get('reads'))}, "
                     f"well made {_yn(a.get('good'))}, "
                     f"publish {_yn(a.get('publish'))}"
                     + (f'\n  operator note, verbatim: "{note}"' if note else ""))
    return "\n".join(lines), len(lines)


def _msg(body):
    """The agent-facing wrapper. Same text for a live batch and a released
    baseline, so the agents cannot tell held verdicts from fresh ones."""
    return ("OPERATOR REVIEW -- these are Tyler's own verdicts on your work, "
            "the only judgement that decides publishing.\n\n" + body +
            "\n\nThese are his words, not a model's. The blind subject check "
            "is off: it did not track his eye (7/20 blind, 9/20 told the "
            "title). Note that 'reads as subject' and 'well made' are "
            "SEPARATE questions -- a piece can read and still be weak.\n\n"
            "You may draw lessons from this. Do NOT edit METHOD.md or "
            "STYLE.md off a single review; a rule needs a pattern across "
            "several batches. See workspace/REVIEWS.md for the full history.")


def _send(body):
    conn = sqlite3.connect(os.path.join(ROOT, "state.db"))
    try:
        for seat in ("artist", "curator"):
            conn.execute("INSERT INTO human_messages (to_agent, text, timestamp, delivered) "
                         "VALUES (?,?,?,0)", (seat, _msg(body), time.time()))
        conn.commit()
    finally:
        conn.close()


def _prepend(path, default_head, section):
    """Newest batch first, under the file's standing header."""
    old = open(path).read() if os.path.exists(path) else default_head
    head, _, rest = old.partition("\n\n")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(f"{head}\n\n{section}\n\n{rest.lstrip()}")


def _deliver(answers, hold=False):
    """Feed a reviewed batch back to both agents, or hold it as baseline.

    hold=True writes to workspace/reviews/baseline.md and sends NOTHING: the
    agents must not see batch 1, or the before/after has no before.
    """
    body, n = _batch_body(answers)
    if not n:
        return 0
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    if hold:
        _prepend(BASELINE_MD, BASELINE_HEAD, f"## {stamp}{BATCH_MARK}\n\n{body}")
        print(f"  {n} verdicts {HOLD_NOTE} -> {BASELINE_MD}")
        print("  agents were NOT messaged; release with --deliver-baseline")
        return n
    _send(body)
    _prepend(REVIEWS_MD, REVIEWS_HEAD, f"## {stamp}\n\n{body}")
    print(f"  delivered {n} verdicts to both seats, appended to {REVIEWS_MD}")
    return n


def deliver_baseline():
    """Release the held batch: message both seats, move it into REVIEWS.md.

    Moves the rendered text wholesale rather than re-deriving it from the
    answer files, so what the agents receive is byte-identical to what was
    held and nothing can be dropped in a re-parse.
    """
    if not os.path.exists(BASELINE_MD):
        print(f"  nothing held: {BASELINE_MD} does not exist")
        return 0
    text = open(BASELINE_MD).read()
    i = text.find("\n## ")
    held = text[i:].strip() if i >= 0 else ""
    if not held:
        # A header with no batches is not a successful delivery. (standing rule)
        print(f"  BASELINE_HELD_NOTHING_TO_DELIVER: {BASELINE_MD} has no batches")
        return 0
    held = held.replace(BATCH_MARK, "")        # it is a normal batch once sent
    n = sum(1 for ln in held.splitlines() if ln.startswith("- "))
    _send(held)
    _prepend(REVIEWS_MD, REVIEWS_HEAD, held)
    os.remove(BASELINE_MD)
    print(f"  released the held baseline to both seats, moved into {REVIEWS_MD}")
    print(f"  {BASELINE_MD} removed; batches 2+ now deliver live")
    return n


def apply(answers_file, no_deliver=False):
    """Publish approved pieces, then feed every verdict back to the agents.

    no_deliver holds the verdicts as baseline instead of sending them.
    """
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
    _deliver(answers, hold=no_deliver)
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
    if len(sys.argv) > 1 and sys.argv[1] == "--deliver-baseline":
        deliver_baseline()
    elif len(sys.argv) > 2 and sys.argv[1] == "--apply":
        apply(sys.argv[2], no_deliver="--no-deliver" in sys.argv[3:])
    else:
        build()
