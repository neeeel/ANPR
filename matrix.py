import tkinter
import mainwindow
import datetime
from tkinter import messagebox

class MatrixDisplay(tkinter.Frame):
    def __init__(self,parentFrame,maxWidth,maxHeight,project,clickable=False,mainCanvasClickable=False):
        self.clickable = clickable
        self.project = project
        self.clicked_callback_function = None
        self.maxWidth = maxWidth
        self.maxHeight = maxHeight
        self.parentFrame = parentFrame
        self._entry_popup = None
        width = self.maxWidth#parentFrame.winfo_width()
        height =self.maxHeight# parentFrame.winfo_height()
        self.vbar = tkinter.Scrollbar(parentFrame, orient=tkinter.VERTICAL)
        self.hbar = tkinter.Scrollbar(parentFrame, orient=tkinter.HORIZONTAL)
        self.vbar.bind("<Button-1>", self.scroll_matrix_screen)
        self.hbar.bind("<Button-1>", self.scroll_matrix_screen)
        self.mainCanvas = tkinter.Canvas(parentFrame, bg="mint cream", width=width, height=height, scrollregion=(0, 0, width, height))
        self.mainCanvas.bind("<Button-1>", self.main_canvas_clicked)
        self.mainCanvasClickable = mainCanvasClickable
        self.verticalLabelsCanvas = tkinter.Canvas(parentFrame, bg="white", width=50, height=height, scrollregion=(0, 0, width, height),yscrollcommand=self.vbar.set)
        self.verticalLabelsCanvas.bind("<Button-1>",self.vertical_canvas_clicked)
        self.horizontalLabelsCanvas = tkinter.Canvas(parentFrame, bg="white", width=width, height=30, scrollregion=(0, 0, width, height),xscrollcommand=self.hbar.set)
        self.horizontalLabelsCanvas.bind("<Button-1>", self.horizontal_canvas_clicked)
        self.horizontalLabelsCanvas.grid(row=0, column=1, columnspan=1, sticky="w")
        self.verticalLabelsCanvas.grid(row=1, column=0, sticky="n")

        self.mainCanvas.grid(row=1, column=1, sticky="nw")
        self.vbar.grid(row=1, column=2, rowspan=1, sticky="NS")
        self.hbar.grid(row=2, column=1, columnspan=1, sticky="EW")
        self.vbar.grid_remove()
        self.hbar.grid_remove()


    def mouse_over(self,event,canvas):
        x, y = event.x, event.y
        #print("clicked at", x, y)
        # if self.clicked_callback_function is None:
        # return
        top, bottom = self.mainCanvas.yview()
        left, right = self.mainCanvas.xview()
        #print(left, right, top, bottom)
        if canvas == "v":
            noOfRows = len(self.verticalLabels)
            y_offset = top * (self.rowHeight) * noOfRows
            try:
                mov = self.verticalLabels[int((y + y_offset) / self.rowHeight)]
            except Exception as e:
                return
        else:
            noOfCols = len(self.horizontalLabels)
            x_offset = left * (self.columnWidth) * noOfCols
            mov = int((x + x_offset) / self.columnWidth)
            try:
                mov = self.horizontalLabels[int((x + x_offset) / self.columnWidth)]
            except Exception as e:
                return

        if self.clicked_callback_function is not None:
            self.clicked_callback_function(mov)



    def clear(self):
        self.mainCanvas.delete(tkinter.ALL)
        self.mainCanvas.update()
        #self.verticalLabelsCanvas.delete(tkinter.ALL)
        #self.horizontalLabelsCanvas.delete(tkinter.ALL)

    def draw(self,data,index=0,fontsize=10,totals=False):
        verticalLabels = list(self.project.allMov)
        horizontalLabels = list(self.project.allMov)
        if totals:
            verticalLabels.append("Total")
            horizontalLabels.append("Total")
        self.verticalLabelsCanvas.bind("<Motion>", lambda e: self.mouse_over(e, "v"))
        self.horizontalLabelsCanvas.bind("<Motion>", lambda e: self.mouse_over(e, "h"))
        self.vbar.grid()
        self.hbar.grid()
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


        mvmntColours = ["","sky blue","orange red","orange"]

        ###
        ### draw lines and text for rows on grid
        ###
        for mov in verticalLabels:
            colour = "white"
            dir = self.project.get_direction(mov)
            #print("dir of",mov,"is",dir)
            colour = mvmntColours[["In","Out","Both"].index(dir) + 1]
            self.mainCanvas.create_line(x, y, x + ((noOfCols ) * self.columnWidth), y)
            self.verticalLabelsCanvas.create_rectangle(x, y, x + self.columnWidth, y + self.rowHeight, fill=colour)
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
            colour = "white"
            dir = self.project.get_direction(mov)
            colour = mvmntColours[["In", "Out", "Both"].index(dir) + 1]
            self.mainCanvas.create_line(x, y, x, y + ((noOfRows) * self.rowHeight))
            self.horizontalLabelsCanvas.create_rectangle(x, y, x + self.columnWidth, y + self.rowHeight, fill=colour)
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
            #print(key,data)
            i, o = key
            if type(data) == list:
                displayedValue = data[index]
            else:
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
            if key[0] != "total" and key[1] != "total":
                self.mainCanvas.create_text((x + (self.columnWidth * column) - self.columnWidth / 2),(y + (self.rowHeight * row) - self.rowHeight / 2), text=displayedValue,font=dataFont)
            if key[0] == "Total" or key[1]=="Total":
                self.mainCanvas.create_text((x + (self.columnWidth * column) - self.columnWidth / 2),(y + (self.rowHeight * row) - self.rowHeight / 2), text=displayedValue,font=dataFont,fill="light blue")
            if key[0] == "Total" and key[1]=="Total":
                self.mainCanvas.create_text((x + (self.columnWidth * column) - self.columnWidth / 2),(y + (self.rowHeight * row) - self.rowHeight / 2), text=displayedValue,font=dataFont,fill = "dark blue")


        parent = self.mainCanvas.winfo_parent()
        parent = self.parentFrame.nametowidget(parent)
        self.verticalLabelsCanvas.configure(width=self.columnWidth, height=displayHeight - self.rowHeight - scrollBarWidth,scrollregion=(0, 0, canvasWidth, canvasHeight))
        self.horizontalLabelsCanvas.configure(height=self.rowHeight, width=displayWidth - self.columnWidth - scrollBarWidth,scrollregion=(0, 0, canvasWidth, canvasHeight))
        self.mainCanvas.configure(width=displayWidth - self.columnWidth - scrollBarWidth,height=displayHeight - self.rowHeight - scrollBarWidth,scrollregion=(0, 0, canvasWidth, canvasHeight))
        parent.configure(width=displayWidth, height=displayHeight)


    def scroll_matrix_screen(self, event):
        print(event)
        print(event.widget.cget("orient"), event.x, event.y)
        self.popup_destroy()
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


    def set_matrix_clicked_callback_function(self,fun,mainCanvasClickable=False):
        self.clicked_callback_function = fun
        self.mainCanvasClickable = mainCanvasClickable


    def main_canvas_clicked(self, event):
        x, y = event.x, event.y
        print("clicked at", x, y)
        if not self.mainCanvasClickable:
            return
        top, bottom = self.mainCanvas.yview()
        left, right = self.mainCanvas.xview()
        print(left,right,top,bottom)
        noOfCols = len(self.horizontalLabels)
        noOfRows = len(self.verticalLabels)
        x_offset = left * (self.columnWidth) * noOfCols
        y_offset = top * (self.rowHeight) * noOfRows
        print("offset are", x_offset, y_offset)
        # x_offset, y_offset = x_offset - (10 + columnWidth), y_offset - (20 + rowHeight)
        # print("offset are", x_offset, y_offset)
        if x > noOfCols * self.columnWidth or y > noOfRows * self.rowHeight:
            print("outside matrix")
            return
        x, y = int((x + x_offset) / self.columnWidth), int((y + y_offset) / self.rowHeight)
        print("x,y is ",x,y)
        print("labels are",self.verticalLabels[y-1],self.horizontalLabels[x-1])
        if self._entry_popup:
            self._entry_popup.destroy()
        self._entry_popup = tkinter.Entry(self.mainCanvas, exportselection=True, borderwidth=2,relief=tkinter.GROOVE)
        self._entry_popup.place(x=x*(self.columnWidth) - x_offset + 3, y=y*(self.rowHeight) - y_offset + 3, width=self.columnWidth, height=self.rowHeight)
        self._entry_popup.bind("<Escape>", lambda event: self.popup_destroy())
        self._entry_popup.bind("<FocusOut>", lambda event: self.popup_destroy())
        self._entry_popup.bind("<Return>", lambda event: self.edit_duration_value(x+1,y+1))
        self._entry_popup.insert(0, "00:00")
        self._entry_popup.focus_force()

        #self.clicked_callback_function(self.verticalLabels[y-1],self.horizontalLabels[x-1])


    def popup_destroy(self):
        if self._entry_popup:
            self._entry_popup.destroy()
        self._entry_popup = None


    def edit_duration_value(self,outMov,inMov):
        print("editing",inMov,outMov)
        val = self._entry_popup.get()
        try:
            datetime.datetime.strptime(val,"%H:%M")
        except Exception as e:
            messagebox.showinfo(message="Incorrect time format",parent=self.mainCanvas)
            if self._entry_popup:
                self._entry_popup.delete(0,"end")
            return
        print("current value is",self.project.durations[inMov,outMov])
        self.project.durations[inMov,outMov] = val
        print("new value is", self.project.durations[inMov,outMov])
        self.project.save_durations()
        self._entry_popup.destroy()
        self.draw(self.project.get_durations())


    def vertical_canvas_clicked(self,event):
        if not self.clickable:
            return None
        x, y = event.x, event.y
        print("clicked at", x, y)
        #if self.clicked_callback_function is None:
            #return
        top, bottom = self.mainCanvas.yview()
        left, right = self.mainCanvas.xview()
        print(left, right, top, bottom)
        noOfRows = len(self.verticalLabels)
        y_offset = top * (self.rowHeight) * noOfRows
        print("clicked in row",int((y + y_offset) / self.rowHeight),"actual value in cell",self.verticalLabels[int((y + y_offset) / self.rowHeight)])
        if self.clicked_callback_function is not None:
            self.clicked_callback_function(self.verticalLabels[int((y + y_offset) / self.rowHeight)])


    def horizontal_canvas_clicked(self,event):
        if not self.clickable:
            return None
        x, y = event.x, event.y
        print("clicked at", x, y)
        #if self.clicked_callback_function is None:
            #return
        top, bottom = self.mainCanvas.yview()
        left, right = self.mainCanvas.xview()
        print(left, right, top, bottom)
        noOfCols = len(self.horizontalLabels)
        x_offset = left * (self.columnWidth) * noOfCols
        print("clicked in column",int((x + x_offset) / self.columnWidth),"actual value in cell",self.horizontalLabels[int((x + x_offset) / self.columnWidth)])
        if self.clicked_callback_function is not None:
            self.clicked_callback_function(self.horizontalLabels[int((x + x_offset) / self.columnWidth)])


    def enable_click(self):
        self.clickable = True


    def disable_click(self):
        self.clickable = False

