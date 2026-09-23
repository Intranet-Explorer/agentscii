import sys, os, math
sys.path.insert(0, os.getcwd())
import figure_common as fc
W,H = 80,52
LX,LY = 30.0,14.0
def L(x,y): return fc.light_field(x,y,LX,LY,lmax=30.0,ambient=0.16)
cv = fc.new_canvas(H,W)
r = fc.standing_figure(cv, 40.0, 34.0, L, height=34, stance="contrapposto", base_fg=11, hot_fg=15, iris_fg=96, one_eye=True)
print("ret:", r)
out=[]
out.append(fc.c(13)+"\u2554"*W)
fc.render(cv,out)
out.append(fc.c(13)+"\u2557"*W)
import canvas as C
C.write_ans("/tmp/_sf_test.ans", out, title="SF TEST", handles="raze")
print("ok")
