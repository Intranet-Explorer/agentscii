#!/usr/bin/env python3
"""AQUEDUCT -- opus1. Two-tier aqueduct striding a fogged river gorge.

Build sequence per STYLE.md: block-in -> one light source (top-left,
the low sun) -> cut arches -> background gradient passes -> foreground
cliffs -> small-scale detail (figures, birds) -> frame/title.
"""
import canvas_tools as ct

W = '/Users/octo/agentscii/workspace'
S = 'opus1'

SKY, MIST, RIVER = 4, 7, 12
STONE, STONE_LO, STONE_HI = 3, 8, 11
ROCK, ROCK_LO, ROCK_HI = 8, 0, 7
LIGHT = 'top-left'

SKY_Y, MIST_Y, RIVER_Y, ART_Y = 50, 78, 90, 90   # pixel-space horizons

UP_PITCH, UP_PIER_W = 12, 4        # upper arcade
UP_TOP, UP_BOT, UP_SPRING, UP_R = 36, 48, 44, 4
LO_TOP, LO_BOT, LO_SPRING, LO_R = 51, 86, 64, 9  # lower arcade
LO_CENTERS = [16, 40, 64]
LO_PIERS = [1, 25, 49, 73]


def build():
    ct.new_canvas(W, S, 80, 50, bg=0)

    # --- 1. backdrop block-in (flat: these are fields, not volumes) ---
    ct.fill_px(W, S, 0, 0, 80, SKY_Y, SKY)
    ct.fill_px(W, S, 0, SKY_Y, 80, MIST_Y - SKY_Y, MIST)
    ct.fill_px(W, S, 0, MIST_Y, 80, ART_Y - MIST_Y, RIVER)

    # --- 2. the light source itself, upper left ---
    ct.sphere_px(W, S, 15, 14, 7, 11, 12, 11, shadow_color=3)

    # --- 3. aqueduct block-in (volumes -> slabs, one shared light) ---
    # parapet + water channel
    ct.slab_px(W, S, 0, 26, 80, 4, STONE, LIGHT, STONE_LO, 15, 'left', 2)
    ct.slab_px(W, S, 1, 30, 78, 6, STONE, LIGHT, STONE_LO, STONE_HI, 'left', 3)
    # upper arcade: spandrel band, then every pier as its own lit box
    ct.slab_px(W, S, 0, UP_TOP, 80, UP_BOT - UP_TOP, STONE, LIGHT, STONE_LO, STONE_HI)
    for k in range(7):
        ct.slab_px(W, S, 2 + UP_PITCH * k, UP_TOP, UP_PIER_W, UP_BOT - UP_TOP,
                   STONE, LIGHT, STONE_LO, STONE_HI, 'left', 1)
    # impost band
    ct.slab_px(W, S, 0, UP_BOT, 80, LO_TOP - UP_BOT, STONE, LIGHT, STONE_LO, 15, 'left', 2)
    # lower arcade
    ct.slab_px(W, S, 0, LO_TOP, 80, LO_BOT - LO_TOP, STONE, LIGHT, STONE_LO, STONE_HI)
    for x in LO_PIERS:
        ct.slab_px(W, S, x, LO_TOP, 6, LO_BOT - LO_TOP,
                   STONE, LIGHT, STONE_LO, STONE_HI, 'left', 2)

    # --- 4. cut the arches back to the backdrop ---
    for k in range(6):
        cx = 6 + UP_PITCH * k + UP_PIER_W // 2 + 2
        ct.circle_px(W, S, cx, UP_SPRING, UP_R, SKY)
        ct.fill_px(W, S, cx - UP_R, UP_SPRING, UP_R * 2, UP_BOT - UP_SPRING, SKY)
    for cx in LO_CENTERS:
        ct.circle_px(W, S, cx, LO_SPRING, LO_R, MIST)
        ct.fill_px(W, S, cx - LO_R, LO_SPRING, LO_R * 2, MIST_Y - LO_SPRING, MIST)
        ct.fill_px(W, S, cx - LO_R, MIST_Y, LO_R * 2, LO_BOT - MIST_Y, RIVER)
        # far shore seen through the arch
        ct.slab_px(W, S, cx - LO_R, 66, LO_R * 2, 5, ROCK, LIGHT, ROCK_LO, ROCK)

    # --- 5. gradient passes over the flat fields (incl. the arch holes) ---
    ct.shade(W, S, SKY, 0, LIGHT, region={'type': 'color', 'color': SKY})
    ct.shade(W, S, MIST, 8, 'top', region={'type': 'color', 'color': MIST})
    ct.strand_shade(W, S, {'type': 'rect', 'x0': 0, 'y0': 2, 'x1': 80, 'y1': 11},
                    [1, 0], [12, 4, 15], n_strands=34, length=9, seed=7)
    ct.strand_shade(W, S, {'type': 'rect', 'x0': 0, 'y0': 39, 'x1': 80, 'y1': 45},
                    [1, 0], [14, 12, 4], n_strands=30, length=7, seed=3)

    # --- 6. foreground canyon walls, drawn last so they occlude ---
    ct.slab_px(W, S, 0, 58, 11, ART_Y - 58, ROCK, LIGHT, ROCK_LO, ROCK_HI, 'left', 3)
    ct.slab_px(W, S, 0, 70, 7, ART_Y - 70, ROCK, LIGHT, ROCK_LO, ROCK_HI, 'left', 2)
    ct.slab_px(W, S, 69, 62, 11, ART_Y - 62, ROCK, LIGHT, ROCK_LO, ROCK_HI, 'left', 3)
    ct.slab_px(W, S, 73, 74, 7, ART_Y - 74, ROCK, LIGHT, ROCK_LO, ROCK_HI, 'left', 2)
    for cx, cy, r in [(13, 88, 4), (22, 89, 3), (63, 88, 3), (55, 89, 2)]:
        ct.sphere_px(W, S, cx, cy, r, ROCK, cx - r, cy - r, shadow_color=0)

    # --- 7. small scale: figures on the deck, birds ---
    for fx in (33, 36, 52):
        ct.capsule_px(W, S, fx, 21, fx, 25, 1, 0, LIGHT, shadow_color=0)
    ct.slab_px(W, S, 44, 22, 4, 4, 0, LIGHT, 0, 8)          # cart
    for bx, by in [(58, 12), (62, 15), (66, 10), (26, 8)]:
        ct.capsule_px(W, S, bx, by, bx + 2, by - 1, 0, 0, LIGHT, shadow_color=0)
        ct.capsule_px(W, S, bx + 2, by - 1, bx + 4, by, 0, 0, LIGHT, shadow_color=0)

    # --- 8. frame + title ---
    ct.fill_px(W, S, 0, 0, 80, 2, ROCK)
    ct.fill_px(W, S, 0, ART_Y - 2, 80, 2, ROCK)
    ct.fill_px(W, S, 0, 0, 2, ART_Y, ROCK)
    ct.fill_px(W, S, 78, 0, 2, ART_Y, ROCK)
    ct.fill_px(W, S, 0, ART_Y, 80, 100 - ART_Y, 0)
    ct.text(W, S, 4, 46, 'A Q U E D U C T', 11, 0)
    ct.text(W, S, 55, 46, 'ninety arches', 8, 0)

    print(ct.metrics(W, S))
    print(ct.save_ans(W, S, 'scratch/_opus1.ans', title='AQUEDUCT', handles='opus'))


if __name__ == '__main__':
    build()
