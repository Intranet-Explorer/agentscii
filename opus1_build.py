#!/usr/bin/env python3
"""AQUEDUCT -- opus1. Two-tier aqueduct striding a fogged river gorge.

Build sequence per STYLE.md: backdrop block-in -> one light source (the
low sun, top-left) -> stone volumes as slabs -> cut the arches back to
the backdrop -> gradient passes over the flat fields -> foreground
canyon walls -> small-scale detail (figures, birds) -> frame/title.
Rerunnable: this script is the piece's source of truth.
"""
import pathlib

import canvas_tools as ct

W = '/Users/octo/agentscii/workspace'
S = 'opus1'

SKY, MIST, RIVER = 4, 6, 12
STONE, STONE_LO, STONE_HI = 7, 8, 15
ROCK, ROCK_LO, ROCK_HI = 8, 0, 8    # canyon wall: silhouette, no rim
BASE, BASE_LO, BASE_HI = 8, 8, 7    # lower tier: weathered, low contrast
LIGHT = 'top-left'

MIST_Y, RIVER_Y, ART_Y = 52, 78, 92      # pixel-space horizons

DECK_Y, UP_TOP, UP_SPRING, UP_BOT = 26, 34, 40, 50
UP_PITCH, UP_PIER_W, UP_R = 12, 4, 4
UP_CENTERS = [10 + UP_PITCH * k for k in range(6)]

LO_TOP, LO_SPRING, LO_BOT, LO_R = 52, 62, 84, 7
LO_CENTERS = [16, 40, 64]
LO_PIERS = [(0, 9), (23, 10), (47, 10), (71, 9)]


def build():
    pathlib.Path(W, 'canvases', S + '.json').unlink(missing_ok=True)
    ct.new_canvas(W, S, 80, 50, bg=0)

    # --- 1. backdrop block-in (flat fields, not volumes) ---
    ct.fill_px(W, S, 0, 0, 80, MIST_Y, SKY)
    ct.fill_px(W, S, 0, MIST_Y, 80, RIVER_Y - MIST_Y, MIST)
    ct.fill_px(W, S, 0, RIVER_Y, 80, ART_Y - RIVER_Y, RIVER)

    # --- 2. the light source itself ---
    ct.sphere_px(W, S, 14, 13, 8, 11, 11, 10, shadow_color=3, hi_color=15)

    # --- 3. stone volumes, one shared light ---
    ct.slab_px(W, S, 0, DECK_Y, 80, 3, STONE, LIGHT, STONE_LO, STONE_HI, 'left', 2)
    ct.slab_px(W, S, 1, DECK_Y + 3, 78, 5, STONE, LIGHT, STONE_LO, STONE_HI, 'left', 3)
    ct.slab_px(W, S, 0, UP_TOP, 80, UP_BOT - UP_TOP, STONE, LIGHT, STONE_LO, STONE_HI)
    for cx in UP_CENTERS:                       # piers between the small arches
        ct.slab_px(W, S, cx - UP_R - UP_PIER_W, UP_TOP, UP_PIER_W, UP_BOT - UP_TOP,
                   STONE, LIGHT, STONE_LO, STONE_HI, 'left', 1)
    ct.slab_px(W, S, 0, UP_BOT, 80, LO_TOP - UP_BOT, STONE, LIGHT, STONE_LO, STONE_HI)
    ct.slab_px(W, S, 0, LO_TOP, 80, LO_BOT - LO_TOP, BASE, LIGHT, BASE_LO, BASE_HI)
    for x, w in LO_PIERS:
        ct.slab_px(W, S, x, LO_TOP, w, LO_BOT - LO_TOP,
                   BASE, LIGHT, BASE_LO, BASE_HI, 'left', 3)

    # --- 4. cut the arches back to the backdrop ---
    for cx in UP_CENTERS:
        ct.circle_px(W, S, cx, UP_SPRING, UP_R + 1, STONE_HI)
        ct.fill_px(W, S, cx - UP_R - 1, UP_SPRING, UP_R * 2 + 2, UP_BOT - UP_SPRING, STONE_HI)
        ct.circle_px(W, S, cx, UP_SPRING, UP_R, SKY)
        ct.fill_px(W, S, cx - UP_R, UP_SPRING, UP_R * 2, UP_BOT - UP_SPRING, SKY)
    for cx in LO_CENTERS:
        ct.circle_px(W, S, cx, LO_SPRING, LO_R + 2, STONE_HI)
        ct.fill_px(W, S, cx - LO_R - 2, LO_SPRING, LO_R * 2 + 4, LO_BOT - LO_SPRING, STONE_HI)
        ct.circle_px(W, S, cx, LO_SPRING, LO_R, MIST)
        ct.fill_px(W, S, cx - LO_R, LO_SPRING, LO_R * 2, RIVER_Y - LO_SPRING, MIST)
        ct.fill_px(W, S, cx - LO_R, RIVER_Y, LO_R * 2, LO_BOT - RIVER_Y, RIVER)
        ct.fill_px(W, S, cx - LO_R, 72, LO_R * 2, 2, 0)

    # --- 5. directional detail: masonry courses on the piers ---
    for x, w in LO_PIERS:
        for cy in range(LO_TOP + 5, LO_BOT, 6):
            ct.fill_px(W, S, x, cy, w, 1, 0)

    # --- 6. gradient passes over the flat fields (arch holes included) ---
    ct.shade(W, S, SKY, 0, LIGHT, region={'type': 'color', 'color': SKY})
    ct.shade(W, S, MIST, 4, LIGHT, region={'type': 'color', 'color': MIST})
    for x, w in LO_PIERS:
        ct.fill_px(W, S, x, LO_BOT, w, ART_Y - LO_BOT, 0)
    for cx in LO_CENTERS:
        ct.fill_px(W, S, cx - LO_R, LO_BOT, LO_R * 2, 4, MIST)
    for gy, gx, gw in [(80, 17, 6), (82, 14, 9), (84, 18, 5), (86, 14, 8), (88, 17, 5), (90, 15, 3)]:
        ct.fill_px(W, S, gx, gy, gw, 1, 15 if gy % 4 == 0 else 14)
    ct.shade(W, S, RIVER, 4, 'top', region={'type': 'color', 'color': RIVER})
    ct.strand_shade(W, S, {'type': 'rect', 'x0': 0, 'y0': 2, 'x1': 80, 'y1': 11},
                    [1, 0], [12, 4, 4], n_strands=6, length=3, seed=7)
    ct.strand_shade(W, S, {'type': 'rect', 'x0': 0, 'y0': 41, 'x1': 80, 'y1': 46},
                    [1, 0], [14, 12, 4], n_strands=26, length=7, seed=3)

    # --- 7. foreground canyon walls, drawn last so they occlude ---
    ct.slab_px(W, S, 0, 58, 12, ART_Y - 58, ROCK, LIGHT, ROCK_LO, ROCK_HI, 'left', 4)
    ct.slab_px(W, S, 0, 68, 8, ART_Y - 68, ROCK, LIGHT, ROCK_LO, ROCK_HI, 'left', 3)
    ct.slab_px(W, S, 68, 60, 12, ART_Y - 60, ROCK, LIGHT, ROCK_LO, ROCK_HI, 'left', 4)
    ct.slab_px(W, S, 73, 72, 7, ART_Y - 72, ROCK, LIGHT, ROCK_LO, ROCK_HI, 'left', 3)
    for cx, cy, r in [(15, 89, 4), (24, 90, 3), (61, 89, 3), (54, 90, 2)]:
        ct.sphere_px(W, S, cx, cy, r, ROCK, cx - r, cy - r, shadow_color=0, hi_color=7)

    # --- 8. small scale: figures on the deck, birds ---
    for fx in (33, 36):
        ct.capsule_px(W, S, fx, 21, fx, 25, 1, 0, LIGHT, shadow_color=0)
    ct.slab_px(W, S, 45, 22, 4, 4, 0, LIGHT, 0, 8)          # cart
    for bx, by in [(58, 12), (62, 16), (66, 9), (28, 7)]:   # flat marks, not volumes
        ct.fill_px(W, S, bx, by, 1, 1, 0)
        ct.fill_px(W, S, bx + 1, by - 1, 2, 1, 0)
        ct.fill_px(W, S, bx + 3, by, 1, 1, 0)

    # --- 9. frame + title ---
    ct.fill_px(W, S, 0, 0, 80, 2, ROCK)
    ct.fill_px(W, S, 0, ART_Y - 2, 80, 2, ROCK)
    ct.fill_px(W, S, 0, 0, 2, ART_Y, ROCK)
    ct.fill_px(W, S, 78, 0, 2, ART_Y, ROCK)
    ct.fill_px(W, S, 0, ART_Y, 80, 100 - ART_Y, 0)
    ct.text(W, S, 4, 47, 'A Q U E D U C T', 11, 0)
    ct.text(W, S, 58, 47, 'the long water', 8, 0)

    print(ct.metrics(W, S))
    print(ct.save_ans(W, S, 'scratch/_opus1.ans', title='AQUEDUCT', handles='opus'))


if __name__ == '__main__':
    build()
