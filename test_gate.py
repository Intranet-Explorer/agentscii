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


def test_catalog_rebuilds_and_location_wins():
    """CATALOG.md regenerates from real directories, and where a piece
    IS beats the last status its subject row recorded (_beast sits in
    gallery/ but its subject row still reads 'rejected')."""
    import harness as h
    n = h._rebuild_catalog()
    assert n > 50, f"catalog suspiciously small: {n}"
    txt = (h.WORKSPACE / 'CATALOG.md').read_text()
    assert '| `_beast` |' in txt
    beast = [l for l in txt.splitlines() if l.startswith('| `_beast` |')][0]
    assert 'shipped' in beast, beast


def test_metrics_line_has_both_denominators():
    """Whole-canvas and subject-only differ by 5x on real pieces
    (_wasteland.v1: 26.1% vs 5.2%). Every metric line must label both,
    or the two sides of a report read as contradicting each other."""
    import harness as h
    m = h._compute_piece_metrics('workspace/gallery/pack53/_orb.v59.ans')
    line = h._fmt_metrics(m)
    assert 'subject-only' in line and 'whole-canvas' in line, line
    assert line.count('subject-only') == 2, 'both metrics need both denominators'


def test_find_patches_required_before_submit():
    import harness as h
    import inspect
    src = inspect.getsource(h.run_tool)
    assert "tool_name='find_patches'" in src
    assert 'call find_patches at' in src


def test_find_patches_returns_distinct_sources():
    """Overlapping windows from one file scored near-identically, so a
    3-result set came back with the same patch 2-3 times. n results must
    mean n distinct references."""
    import sys
    sys.path.insert(0, 'corpus')
    from find_patches_clip import find_patches_clip
    hits = find_patches_clip('shaded sphere warm light', n=3,
                             index_dir='corpus/clip_index')
    paths = [h['parent_path'] for h in hits]
    assert len(paths) == len(set(paths)), f'duplicate sources: {paths}'


def test_blind_render_redacts_overlaid_title():
    """A title drawn OVER a dither field measures only 0.31
    letter-density and slipped through, so Opus's first 'blind' subject
    read quoted 'THE KEEPER // AGENTSCII' off the canvas. Letter RUNS
    catch a word regardless of what it sits on."""
    import harness as h
    rows = [[(c, 7, 0) for c in "\u2592" * 17 + "THE KEEPER // AGENTSCII" + "\u2591" * 20]]
    visible = [ch for ch, fg, bg in rows[0] if ch != " "]
    letters = sum(1 for ch in visible if ch.isascii() and ch.isalpha())
    assert letters / len(visible) < 0.5, "fixture must defeat the density rule"
    run = best = 0
    for ch, fg, bg in rows[0]:
        if ch.isascii() and (ch.isalpha() or ch in "/-.,!'"):
            run += 1; best = max(best, run)
        else:
            run = 0
    assert best >= 6, "run rule must catch it"


def test_artist_cap_raised():
    import harness as h
    assert h.MAX_TOOL_CALLS_BY_ROLE["artist"] == 100


def test_intended_title_found_for_all_real_pieces():
    """A subject check that can't compare against intent can only
    describe, not verify. CROSSING returned None because its title sits
    in a framed row, not the first three lines."""
    import harness as h
    cases = {
        'workspace/rejected/_opus3.ans': 'CROSSING',
        'workspace/references/study/_opus_AQUEDUCT.ans': 'AQUEDUCT',
        'workspace/references/study/_opus_PROSPECTOR.ans': 'PROSPECTOR',
    }
    for p, want in cases.items():
        got = h._extract_intended_title(p)
        assert got == want, f'{p}: got {got!r} want {want!r}'
    assert h._extract_intended_title(
        'workspace/rejected/_opus3.ans', title='OVERRIDE') == 'OVERRIDE'


def test_landscape_terms_dont_trip_anatomy_guard():
    """The blind-claim guard catches a critique claiming ANATOMY the
    render lacks. 'mountain silhouettes' is a landscape term, and a
    blind check correctly reporting 'flat geometric shapes, no
    constructed subject' for a scene is AGREEMENT, not contradiction.
    CROSSING was blocked 8 times by that false positive."""
    import inspect, harness as h
    src = inspect.getsource(h.curate_piece_opus_gated) + inspect.getsource(h.run_tool)
    assert '_LANDSCAPE_OK' in src
    assert 'anatomy_claimed' in src


def test_autosave_groups_with_its_piece():
    """The cap-handoff autosave must not become a phantom piece. It
    wrote scratch/_<slug>.autosave.ans for canvas <slug>, and the
    dashboard grouped that as its own entry -- and since autosaves are
    the newest file, every one outranked the real piece it came from.
    The operator and I spent a round looking at two different files."""
    import inspect, harness as h
    src = inspect.getsource(h.run_shift)
    assert 'scratch/{_slug}.autosave.ans' in src, 'extra underscore is back'
    assert 'scratch/_{_slug}.autosave.ans' not in src


def test_gates_shared_by_both_paths():
    """opus_duo.py drew four rounds with zero find_patches calls because
    it bypassed submit_piece entirely. One shared gate function now."""
    import harness as h
    ok, rep = h.check_piece_gates('workspace/scratch/duo1.ans', retrieval_queries=None)
    assert not ok and 'RETRIEVAL' in rep
    ok2, rep2 = h.check_piece_gates('workspace/scratch/duo1.ans',
                                    retrieval_queries=['shaded knuckles'])
    assert ok2 and 'glyph-carried' in rep2


def test_house_tier_is_structured_field_not_keyword_scan():
    """Two-tier gate. The house verdict must be parsed from a HOUSE:
    line, never matched out of prose -- three false positives already
    came from keyword scans over critique text."""
    import inspect, harness as h
    src = inspect.getsource(h.opus_curate_review)
    assert 'HOUSE: PASS or HOUSE: FAIL' in src
    assert 'startswith("HOUSE:")' in src
    ship = inspect.getsource(h.curate_piece_opus_gated)
    assert "house_verdict" in ship and "GALLERY_UNPACKED" in ship
