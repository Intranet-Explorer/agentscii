# duo3 session archive

One file per session, written at session end. `duo3.sN.ans` is the canvas
as it stood when session N finished; the `.colour-only.png` /
`.glyphs-only.png` pair is that session's self-check.

## duo3.s6.ans is NOT the session-6 brief's output

Session 6 ran TWICE, and the file here is from the wrong one.

The first launch was killed by the agent harness, but killing the python
wrapper does not kill the `claude` child it spawned -- the child
reparented to init and kept working for another 62 minutes. A relaunch
under launchd ran at the same time. Two artists, one canvas.

  - relaunch (17:13-17:18, $1.28 reported) got the full session-6 brief:
    burning-side front, the dissolution constraint, both straight walls.
    Its output was OVERWRITTEN and is lost.
  - orphan (17:07-18:09, cost never reported) ran on the standard
    continuity prompt with NO operator brief -- confirmed by reading the
    prompt out of ~/.claude/projects: 'SESSION 6.' absent, 'structureless
    wash' absent. It won the last write at 18:08.

So duo3.s6.ans = the orphan's work, titled "What the Fire Left". It did
the contour work from its own prior NEXT line, because that NEXT is in
the standard continuity prompt. It never saw the dissolution constraint
or the two-straight-walls instruction.

Kept deliberately (operator decision) and reviewed as the real session-6
result, with the provenance recorded rather than smoothed over.

Guard added after this: opus_session.py takes a per-slug lockfile and
refuses to start while another session holds the canvas, and refuses an
empty brief outright.
