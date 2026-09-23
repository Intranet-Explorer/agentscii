import sys; sys.path.insert(0,"scratch")
import canvas as C
cv=C.Canvas(80,26,fill_ch=' ',fill_fg=7,fill_bg=0)
# label each row with the fg index, fill a bar so I can SEE its rendered hue
rows=[("idx3",3),("idx5",5),("idx1",1),("idx4",4),("idx6",6),("idx2",2),
      ("B3/11",11),("B5/13",13),("B1/9",9),("B4/12",12),("B6/14",14),("B2/10",10)]
for i,(name,idx) in enumerate(rows):
    y=i*2
    for x in range(8,78): cv.set(x,y,'█',idx,0)
    for x,ch in enumerate(name): cv.set(x,y,ch,15,0)
out=[]; cv.render(out); C.write_ans("scratch/_swatch3.ans",out,title="SWATCH",handles="raze")
