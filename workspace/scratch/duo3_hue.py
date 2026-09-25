"""duo3 session 4: take the violet out of the canvas that is already drawn.

duo3_tools and duo3_bg are both fixed at the source, so a fresh build
never makes a magenta cell again. This is for the live canvas, which I
am not rebuilding: session 2 learned the hard way that re-running a
respelling pass over an already-respelled canvas quantises the value
twice and flattens what it is respelling, and the model pass is the one
thing in this piece I will not run again by choice.

So: sweep, and recolour in place. Every magenta cell in the piece is a ░
over black, and ░ in dark red is the same ink at the same coverage, so
nothing about the drawing moves. Only the hue does.
"""
import sys
sys.path.insert(0, '/Users/octo/agentscii/workspace/scratch')
import duo3_tools as t

cells = [(x, y, ch, 1, 0)
         for y, row in enumerate(t.grid(0, 0, 80, 28))
         for x, (ch, fg, bg) in enumerate(row) if 5 in (fg, bg)]
t.paint(cells)

if __name__ == '__main__':
    left = sum(1 for row in t.grid(0, 0, 80, 28) for ch, fg, bg in row if 5 in (fg, bg))
    assert left == 0, left
    print('recoloured', len(cells), 'magenta cells -> dark red; 0 left')
