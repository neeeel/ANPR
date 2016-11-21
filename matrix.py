import tkinter
import mainwindow

class MatrixDisplay():
    def __init__(self,parentFrame,maxWidth,maxHeight,clickable=False):
        self.clickable = clickable
        self.clicked_callback_function = None
        self.maxWidth = maxWidth
        self.maxHeight = maxHeight
        self.parentFrame = parentFrame
        width = parentFrame.winfo_width()
        height = parentFrame.winfo_height()
        self.vbar = tkinter.Scrollbar(parentFrame, orient=tkinter.VERTICAL)
        self.hbar = tkinter.Scrollbar(parentFrame, orient=tkinter.HORIZONTAL)
        self.vbar.bind("<Button-1>", self.scroll_matrix_screen)
        self.hbar.bind("<Button-1>", self.scroll_matrix_screen)
        self.mainCanvas = tkinter.Canvas(parentFrame, bg="mint cream", width=width, height=height, scrollregion=(0, 0, width, height))
        self.mainCanvas.bind("<Button-1>", self.main_canvas_clicked)

        self.verticalLabelsCanvas = tkinter.Canvas(parentFrame, bg="white", width=50, height=height, scrollregion=(0, 0, width, height),yscrollcommand=self.vbar.set)
        self.horizontalLabelsCanvas = tkinter.Canvas(parentFrame, bg="white", width=width, height=30, scrollregion=(0, 0, width, height),xscrollcommand=self.hbar.set)
        self.horizontalLabelsCanvas.grid(row=0, column=1, columnspan=1, sticky="w")
        self.verticalLabelsCanvas.grid(row=1, column=0, sticky="n")
        self.mainCanvas.grid(row=1, column=1, sticky="nw")
        self.vbar.grid(row=1, column=2, rowspan=1, sticky="NS")
        self.hbar.grid(row=2, column=1, columnspan=1, sticky="EW")

    def draw(self,verticalLabels,horizontalLabels,data,fontsize=8):
        self.verticalLabels = verticalLabels
        self.horizontalLabels = horizontalLabels
        self.mainCanvas.delete(tkinter.ALL)
        self.verticalLabelsCanvas.delete(tkinter.ALL)
        self.horizontalLabelsCanvas.delete(tkinter.ALL)
        self.columnWidth = 50
        self.rowHeight = 30
        #fontsize = 8
        noOfCols = len(horizontalLabels)
        noOfRows = len(verticalLabels)
        x, y = 0, 0
        scrollBarWidth = 30
        labelfont =  tkinter.font.Font(family="helvetica", size=8)
        f = tkinter.font.Font(family="helvetica", size=fontsize)
        root = self.parentFrame.winfo_toplevel()
        print(root.winfo_screenheight())
        canvasHeight = (noOfRows * self.rowHeight) + 2
        canvasWidth = (noOfCols * self.columnWidth) + 2
        displayWidth = self.maxWidth
        displayHeight = self.maxHeight
        if displayWidth > canvasWidth + self.columnWidth + scrollBarWidth :
            displayWidth = canvasWidth + (self.columnWidth) + scrollBarWidth
        if displayHeight > canvasHeight + (self.rowHeight) + scrollBarWidth :
            displayHeight = canvasHeight + (self.rowHeight) + scrollBarWidth

        print("setting display to ", displayWidth, displayHeight)
        print("canvas settings are", canvasWidth, canvasHeight)

        ###
        ### draw lines and text for rows on grid
        ###
        for mov in verticalLabels:
            self.mainCanvas.create_line(x, y, x + ((noOfCols ) * self.columnWidth), y)
            y = y + self.rowHeight / 2
            self.verticalLabelsCanvas.create_text(x + self.columnWidth / 2, y, text=mov, font=labelfont)
            y = y + self.rowHeight / 2
            self.mainCanvas.create_line(x, y, x + ((noOfCols) * self.columnWidth), y)


        ###
        ### draw lines and text for columns on grid
        ###
        x, y = 0, 0

        # x += columnWidth
        # y += rowHeight + 10
        for mov in horizontalLabels:
            self.mainCanvas.create_line(x, y, x, y + ((noOfRows) * self.rowHeight))
            x = x + self.columnWidth / 2
            self.horizontalLabelsCanvas.create_text(x, y + self.rowHeight / 2, text=mov, font=labelfont)
            x = x + self.columnWidth / 2
            self.mainCanvas.create_line(x, y, x, y + ((noOfRows) * self.rowHeight))

        ###
        ### display data
        ###

        dataFont = tkinter.font.Font(family="verdana", size=fontsize)
        totalFont = tkinter.font.Font(family="verdana", size=fontsize)
        x, y = 0, 0
        for key, data in data.items():
            # print(key,data)
            i, o = key
            displayedValue = data
            try:
                row = verticalLabels.index(i) + 1
            except ValueError as e:
                print("error in ", key, data)
                continue
            try:
                column = horizontalLabels.index(o) + 1
            except ValueError as e:
                print("error in ", key, data)
                continue
            self.mainCanvas.create_text((x + (self.columnWidth * column) - self.columnWidth / 2),(y + (self.rowHeight * row) - self.rowHeight / 2),text=displayedValue, font=dataFont)

        parent = self.mainCanvas.winfo_parent()
        parent = self.parentFrame.nametowidget(parent)
        self.verticalLabelsCanvas.configure(width=self.columnWidth, height=displayHeight - self.rowHeight - scrollBarWidth,scrollregion=(0, 0, canvasWidth, canvasHeight))
        self.horizontalLabelsCanvas.configure(height=self.rowHeight, width=displayWidth - self.columnWidth - scrollBarWidth,scrollregion=(0, 0, canvasWidth, canvasHeight))
        self.mainCanvas.configure(width=displayWidth - self.columnWidth - scrollBarWidth,height=displayHeight - self.rowHeight - scrollBarWidth,scrollregion=(0, 0, canvasWidth, canvasHeight))
        parent.configure(width=displayWidth, height=displayHeight)

    def scroll_matrix_screen(self, event):
        print(event)
        print(event.widget.cget("orient"), event.x, event.y)

        if event.widget.cget("orient") == "vertical":
            top, bottom = (event.widget.get())
            thumbsize = bottom - top
            f = event.widget.fraction(event.x, event.y)
            if f < top:
                f = f - (thumbsize / 2)
            self.mainCanvas.yview_moveto(f)
            self.verticalLabelsCanvas.yview_moveto(f)
            return "break"
        else:
            left, right = (event.widget.get())
            thumbsize = right - left
            f = event.widget.fraction(event.x, event.y)
            if f < left:
                f = f - (thumbsize / 2)
            self.mainCanvas.xview_moveto(f)
            self.horizontalLabelsCanvas.xview_moveto(f)
            return "break"

    def set_matrix_clicked_callback_function(self,fun):
        self.clicked_callback_function = fun

    def main_canvas_clicked(self, event):
        x, y = event.x, event.y
        print("clicked at", x, y)
        if self.clicked_callback_function is None:
            return
        top, bottom = self.mainCanvas.yview()
        left, right = self.mainCanvas.xview()
        print(left,right,top,bottom)
        noOfCols = len(self.horizontalLabels)
        noOfRows = len(self.verticalLabels)
        x_offset = left * (self.columnWidth) * noOfCols
        y_offset = top * (self.rowHeight) * noOfRows
        # print("offset are", x_offset, y_offset)
        # x_offset, y_offset = x_offset - (10 + columnWidth), y_offset - (20 + rowHeight)
        # print("offset are", x_offset, y_offset)
        if x > noOfCols * self.columnWidth or y > noOfRows * self.rowHeight:
            print("outside matrix")
            return
        x, y = int((x + x_offset) / self.columnWidth) + 1, int((y + y_offset) / self.rowHeight) + 1
        self.clicked_callback_function(y,x)


#win = tkinter.Tk()
data = {(1,2):100,(2,3):50,(4,6):10,(4,7):12,(4,8):22,(5,2):12,(1,3):45,("total",2):56,("total","total"):56}
v = []
h= []
for i in range(20):
    data[(i,i)] = 10
    v.append(i)
    h.append(i)

#frame = tkinter.Frame(win,width = 800,height=800)
#frame.grid(row=0,column=0)
#frame.grid_propagate(False)
#matrix = MatrixDisplay(frame,800,800)
#matrix.draw(v,h,data)
#win.mainloop()