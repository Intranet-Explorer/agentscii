"""Gate regression checks. Run: python3 test_gate.py

Guards the 2026-09-22 findings:
  - a large solid region is legal when a dither ramp bridges it to
    another brightness (the old rule blocked every region over 40 cells,
    which is what pushed pieces toward wall-to-wall static)
  - box-drawing glyphs are frame, never subject
  - _run_claude_p reports the REAL failure, never a blanket "timed out"
"""
import sys
sys.path.insert(0, '.')
import harness


def test_house_bar_passes():
    assert harness._flat_region_check(
        'workspace/gallery/pack53/_orb.v59.ans') is None


def test_accepted_gallery_piece_passes():
    assert harness._flat_region_check(
        'workspace/gallery/unpacked/_beast.v7.ans') is None


def test_box_chars_cover_cp437():
    # the old hand-typed set missed these 18; '╡' blocked _cyclops
    box = {chr(cp) for cp in range(0x2500, 0x2580)}
    for ch in '╡╞╟╢╤╧╥╨╪╫╕╖╘╙╛╜╒╓':
        assert ch in box, ch


def test_claude_p_reports_real_reason():
    # never a bare None, and never a false "timed out" for a spawn failure
    r = harness._run_claude_p(['/nonexistent/binary'], timeout=5, retries=0)
    assert r is not None
    assert r.returncode != 0
    assert 'spawn failed' in r.stderr
    assert 'timed out' not in r.stderr


def test_errored_reviews_dont_burn_budget():
    import inspect
    src = inspect.getsource(harness.opus_curate_review)
    assert 'opus_verdict IS NOT NULL' in src


if __name__ == '__main__':
    fails = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith('test_'):
            continue
        try:
            fn()
            print(f'  PASS {name}')
        except Exception as e:
            fails += 1
            print(f'  FAIL {name}: {type(e).__name__}: {e}')
    print('FAILED' if fails else 'all gate checks pass')
    sys.exit(1 if fails else 0)


def test_flat_forms_pack_halfblocks():
    """slab/capsule must produce real ▀ interiors, not flat fills with
    noise. Regression guard for the 5.1% -> 20.5% band-width fix."""
    import canvas_tools as ct
    W = 'workspace'
    for slug in ('_tchk_slab', '_tchk_cap'):
        p = __import__('pathlib').Path(W) / 'canvases' / f'{slug}.json'
        p.unlink(missing_ok=True)
    ct.new_canvas(W, '_tchk_slab', 80, 50, bg=0)
    ct.slab_px(W, '_tchk_slab', 22, 6, 36, 88, 12,
               shadow_color=4, hi_color=14, side='left', side_w=13)
    m = ct.metrics(W, '_tchk_slab')
    assert m['half_block_pct'] > 12, f"slab half_block too low: {m}"

    ct.new_canvas(W, '_tchk_cap', 80, 50, bg=0)
    ct.capsule_px(W, '_tchk_cap', 26, 18, 54, 76, 9, 12, shadow_color=4)
    m = ct.metrics(W, '_tchk_cap')
    assert m['half_block_pct'] > 8, f"capsule half_block too low: {m}"


def test_disconnected_masses_is_soft_only():
    """Honest name and honest scope: counts spatially disconnected
    masses, NOT forms (a 5-form composite where everything touches
    scores 1). Soft signal only -- must never gate or tripwire."""
    import harness as h
    import inspect
    v59 = h._compute_piece_metrics('workspace/gallery/pack53/_orb.v59.ans')
    assert 'disconnected_masses' in v59
    assert 'subject_regions' not in v59
    src = inspect.getsource(h._check_regression_tripwire)
    # check the QUERY, not the docstring that explains the exclusion
    sql = src.split('"""')[2] if src.count('"""') >= 2 else src
    assert 'disconnected_masses' not in sql


def test_scratch_hygiene_moves_not_deletes():
    """Closing a subject archives its scratch files. Must MOVE, never
    delete, and must leave the shared helper modules alone."""
    import harness as h
    from pathlib import Path
    probe = h.SCRATCH / '_tchk_hygiene.v1.ans'
    probe.write_text('probe\n')
    keeper = h.SCRATCH / 'canvas.py'
    assert keeper.exists(), 'helper module missing before test'
    moved = h._archive_subject_scratch('_tchk_hygiene')
    dest = h.WORKSPACE / 'archive' / 'scratch-2026-09' / '_tchk_hygiene.v1.ans'
    try:
        assert '_tchk_hygiene.v1.ans' in moved, moved
        assert dest.exists(), 'file was not moved into archive'
        assert not probe.exists(), 'file left behind in scratch'
        assert keeper.exists(), 'helper module was archived -- must stay'
    finally:
        dest.unlink(missing_ok=True)
