
import tkinter
import tkinter.font as font

import tkinter.ttk as ttk
from tkinter import messagebox
import datetime
import openpyxl
import win32com.client
from PIL import Image,ImageDraw,ImageTk
from tkinter import filedialog
import threading
import os
import myDB
import pickle


class mainWindow(tkinter.Tk):

    def __init__(self):
        super(mainWindow, self).__init__()
        #win = tkinter.Toplevel(self)
        self.colourLabels = []
        self.entryValues = []
        self.revertButton = None
        self.siteLabel = None
        self.box1Value = 0
        self.box2Value = 0 ### to keep track of the combo boxes on the comparison display sheet
        self.selectedDuplicates = None
        self.getRouteAssignmentFsLsNonDirectionalFunction = None
        self.loadUnclassedFunction = None
        self.loadClassedFunction = None
        self.loadJobFunction = None
        self.getNonDirectionalCordonFunction = None
        self.reprocessDataFunction = None
        self.setDuplicatesFunction = None
        self.getCordonFunction = None
        self.getRouteAssignmentFsLsFunction = None
        self.displayWin = None
        self.currentSelected = [0,0]
        self.loadOVCountsFunction = None
        self.getUnclassedComparisonFunction = None
        self.displayStatus = "edited" ## stores whether to display base comparison data, or edited comparison data
        self.geometry("600x500")
        self.movementTabs = None
        self.displayedDataIndex = 0
        self.comparisonWindow = None
        self.summaryTree = None
        self.state("zoomed")
        self.numCams =0 ## this is so we can delete entryvalues from the list if the no of cameras gets updated on the survey set up window
        self.movementsFrame = None ### this frame goes in the parameters window, to display the site/movement data
        self.dataFrame = tkinter.Frame(self,width = 50,height  = 600,bg = "green")
        self.comparisonDataStructure = []
        self.configure(bg = "white")
        self.jobListBox = None
        self.currentJob = None
        self.uneditedDataList = None
        self.tempEditedDataStore  = []
        self.menubar = tkinter.Menu(self)
        menu = tkinter.Menu(self.menubar, tearoff=0)
        menu.add_command(label="Load TPs")
        menu.add_separator()
        menu.add_command(label="Export")
        self.menubar.add_cascade(label="File", menu=menu)
        self.config(menu=self.menubar)
        menu = tkinter.Menu(self.menubar, tearoff=0)
        menu.add_command(label="Journey Time Settings")
        # menu.add_separator()
        # menu.add_command(label = "Excel Settings",command = self.spawn_excel_window)
        self.menubar.add_cascade(label="Settings", menu=menu)

        self.menubar = tkinter.Menu(self)
        menu = tkinter.Menu(self.menubar, tearoff=0)
        menu.add_command(label="Load Settings", command=self.spawn_settings_window)
        menu.add_separator()
        menu.add_command(label="l")
        self.menubar.add_cascade(label="Settings", menu=menu)
        self.config(menu=self.menubar)
        self.load_settings()
        #self.spawn_cordon_screen()
        self.spawn_survey_setup_screen()
        #self.spawn_duplicates_window(None)

    def get_cordon_data(self):
        data = self.getCordonFunction(self.currentJob)
        self.draw_cordon_matrix(self.matrixCanvas,data)

    def spawn_cordon_screen(self):
        for child in self.winfo_children():
            child.destroy()

        frame = tkinter.Frame(self, bg="white")
        tkinter.Button(frame, text="In/Out Only", bg="white", height=3,width=12,
                       command=self.get_directional_cordon_data).grid(row=0, column=0, padx=10, pady=10)
        tkinter.Button(frame, text="Non Directional", bg="white", height=3,width=12,
                       command=self.get_nondirectional_cordon_data).grid(row=1, column=0, padx=10, pady=10)
        tkinter.Button(frame, text="Netest", bg="white", height=3, width=12,
                       command=self.get_directional_route_assignment_fs_ls_data).grid(row=2, column=0, padx=10, pady=10)
        tkinter.Button(frame, text="test 2", bg="white", height=3, width=12,
                       command=self.get_non_directional_route_assignment_fs_ls_data).grid(row=3, column=0, padx=10, pady=10)
        frame.grid(row=0,column=0, padx=20, pady=10,sticky="w")
        frame = tkinter.Frame(self, bg="white",relief=tkinter.GROOVE,borderwidth=3,width=800,height=800)
        frame.grid(row=0, column=1, padx=10, pady=10)
        self.matrixCanvas = tkinter.Canvas(frame,bg="white",width=800,height=800)
        self.matrixCanvas.grid(row=0,column=0)
        self.get_directional_cordon_data()

    def spawn_duration_matrix_screen(self):
        pass

    def get_non_directional_route_assignment_fs_ls_data(self):
        inMov = []
        outMov = []
        data = self.getRouteAssignmentFsLsNonDirectionalFunction(self.currentJob)
        for item in data[0]:
            i, o = item[0]
            if i not in inMov:
                inMov.append(i)
            if o not in outMov:
                outMov.append(o)
        inMov = sorted(inMov)
        outMov = sorted(outMov)
        self.draw_matrix(data, inMov, outMov)

    def get_directional_route_assignment_fs_ls_data(self):
        inMov = []
        outMov = []
        data = self.getRouteAssignmentFsLsFunction(self.currentJob)
        for site, details in self.currentJob["sites"].items():
            for mvmtNo, mvmt in details.items():
                if mvmt["dir"] == 1:
                    inMov.append(mvmt["newmovement"])
                if mvmt["dir"] == 2:
                    outMov.append(mvmt["newmovement"])
        inMov = sorted(inMov)
        outMov = sorted(outMov)
        self.draw_matrix(data, inMov, outMov)

    def get_nondirectional_cordon_data(self):
        inMov=[]
        outMov=[]
        data = self.getNonDirectionalCordonFunction(self.currentJob)
        for item in data[0]:
            i, o = item[0]
            if i not in inMov:
                inMov.append(i)
            if o not in outMov:
                outMov.append(o)
        inMov = sorted(inMov)
        outMov = sorted(outMov)
        self.draw_matrix(data,inMov,outMov)

    def get_directional_cordon_data(self):
        inMov = []
        outMov = []
        data = self.getCordonFunction(self.currentJob)
        for site, details in self.currentJob["sites"].items():
            for mvmtNo, mvmt in details.items():
                if mvmt["dir"] == 1:
                    inMov.append(mvmt["newmovement"])
                if mvmt["dir"] == 2:
                    outMov.append(mvmt["newmovement"])
        inMov = sorted(inMov)
        outMov = sorted(outMov)
        self.draw_matrix(data,inMov,outMov)

    def draw_matrix(self,data,inMov,outMov):
        ###
        ### data is in the form of a list [cell data,in Totals,out Totals]
        ### cell data is a list of lists, each item is of the form [(inmov,outmov),value]
        ### in Totals and out Totals are the final row and column totals to display in the matrix
        ###
        canvas = self.matrixCanvas
        maxColWidth = 50
        maxRowHeight = 30
        maxFontSize = 8
        columnWidth = 50
        rowHeight = 30
        fontsize = 8
        print("inmov is",inMov)
        noOfCols = len(outMov)
        noOfRows = len(inMov)
        if noOfCols >32 or noOfRows > 32:
            columnWidth =30
            rowHeight = 17
            fontsize=6
        x, y = 10, 10
        f = tkinter.font.Font(family="helvetica", size=fontsize)
        titleFont = tkinter.font.Font(family="helvetica", size=12, weight="bold")
        self.matrixCanvas.delete(tkinter.ALL)
        canvasHeight = noOfRows * rowHeight
        canvasWidth = noOfCols * columnWidth
        print("canvas specs are", self.matrixCanvas.winfo_width(), self.matrixCanvas.winfo_height())
        pad = (self.winfo_height() - (canvasHeight + (3 * (rowHeight + 10)))) / 2
        print("pad is", pad)
        parent = canvas.winfo_parent()
        parent = canvas.nametowidget(parent)
        # parent.grid_configure(pady=pad)
        canvas.configure(width=canvasWidth + (3 * (columnWidth + 10)), height=canvasHeight + (3 * (rowHeight + 10)))
        canvas.create_text(x, (canvasHeight + (3 * rowHeight) + 10) / 2, text="IN", font=titleFont)
        x += columnWidth
        y += rowHeight + 10
        ###
        ### draw lines and text for rows on grid
        ###
        for mov in inMov:
            canvas.create_line(x, y, x + ((noOfCols + 1) * columnWidth), y)
            y = y + rowHeight / 2
            canvas.create_text(x - columnWidth / 2, y, text=mov, font=f)
            y = y + rowHeight / 2
        canvas.create_line(x, y, x + ((noOfCols + 1) * columnWidth), y)
        y = y + rowHeight / 2
        canvas.create_text(x - columnWidth / 2, y, text="Total", font=f)
        y = y + rowHeight / 2
        canvas.create_line(x, y, x + ((noOfCols + 1) * columnWidth), y)

        ###
        ### draw lines and text for columns on grid
        ###
        x, y = 10, 10
        canvas.create_text((canvasWidth + (3 * columnWidth)) / 2, y, text="OUT", font=titleFont)
        x += columnWidth
        y += rowHeight + 10
        for mov in outMov:
            canvas.create_line(x, y, x, y + ((noOfRows + 1) * rowHeight))
            x = x + columnWidth / 2
            canvas.create_text(x, y - rowHeight / 2, text=mov, font=f)
            x = x + columnWidth / 2
        canvas.create_line(x, y, x, y + ((noOfRows + 1) * rowHeight))
        x = x + columnWidth / 2
        canvas.create_text(x, y - rowHeight / 2, text="Total", font=f)
        x = x + columnWidth / 2
        canvas.create_line(x, y, x, y + ((noOfRows + 1) * rowHeight))

        ###
        ### display data
        ###
        dataFont = tkinter.font.Font(family="verdana", size=fontsize)
        totalFont = tkinter.font.Font(family="verdana", size=fontsize)
        x, y = 10 + (2 * columnWidth), 10 + rowHeight + 10
        for item in data[0]:
            i, o = item[0]
            count = item[1]
            try:
                row = inMov.index(i) + 1
            except ValueError as e:
                print("error in ", item)
                continue
            try:
                column = outMov.index(o)
            except ValueError as e:
                print("error in ", item)
                continue
            canvas.create_text((x + (columnWidth * column) - columnWidth / 2), (y + (rowHeight * row) - rowHeight / 2),
                               text=count, font=dataFont)

        column, row = noOfCols, 1
        for value in data[1]:
            canvas.create_text((x + (columnWidth * column) - columnWidth / 2), (y + (rowHeight * row) - rowHeight / 2),
                               text=int(value), font=totalFont, fill="red")
            row += 1

        column, row = 0, noOfRows + 1
        for value in data[2]:
            canvas.create_text((x + (columnWidth * column) - columnWidth / 2), (y + (rowHeight * row) - rowHeight / 2),
                               text=int(value), font=totalFont, fill="red")
            column += 1
        column, row = noOfCols, noOfRows + 1
        canvas.create_text((x + (columnWidth * column) - columnWidth / 2), (y + (rowHeight * row) - rowHeight / 2),
                           text=int(sum(data[1])), font=totalFont, fill="blue")
        print("sum of data columns is", sum(data[1]), sum(data[2]))

    def spawn_survey_setup_screen(self):
        self.joblist = myDB.get_jobs()
        #print(type(self.joblist[1]["surveyDate"]))
        self.entryValues = []

        for child in self.winfo_children():
            child.destroy()
        self.menubar = tkinter.Menu(self)
        menu = tkinter.Menu(self.menubar, tearoff=0)
        menu.add_command(label="Load Settings", command=self.spawn_settings_window)
        menu.add_separator()
        menu.add_command(label="l")
        self.menubar.add_cascade(label="Settings", menu=menu)
        self.config(menu=self.menubar)
        frame = tkinter.Frame(self,  bg="white")
        f = tkinter.font.nametofont("TkDefaultFont").configure(size=14)
        treefont = tkinter.font
        tkinter.Button(frame, text="Create new ANPR \nProject", bg="white", height=3,
                       command=self.spawn_parameters_window).grid(row=0, column=0, padx=20, pady=20)
        tkinter.Button(frame, text="Edit ANPR \nProject", width=17, height=3, bg="white",command=self.edit_job).grid(row=0, column=1, padx=20,
                                                                                         pady=20)
        tkinter.Button(frame, text="Duplicate ANPR \nProject", width=17, height=3, bg="white").grid(row=0, column=2, padx=20,
                                                                                         pady=20)
        tkinter.Button(frame, text="Delete ANPR \nProject", width=17, height=3, bg="white",command=self.delete_job).grid(row=0, column=3, padx=20,
                                                                                         pady=20)
        frame.grid(row=0, column=0,pady=(100,0),padx=(120,0))
        frame = tkinter.Frame(self, bg="white")
        cols = ("Job No","Job Name","Survey Date","Survey Times","OV Template","OV Counts","Unclassed VRN","Classed VRN","Comparison","Completed","Created By","Created Date","Folder")

        self.tree = ttk.Treeview(frame,columns=tuple(range(len(cols))),show="headings",height = 30)
        self.tree.bind("<Double-Button-1>", self.load_job)
        self.tree.heading(0,text="WERW")
        self.tree.tag_configure("grn",foreground="dark blue")
        for i,col in enumerate(cols):
            self.tree.heading(i,text=col)
            self.tree.column(i,width  = 120,anchor=tkinter.CENTER)
        for i in range(2):
            self.tree.column(i,width=150)
        #tree.column(3)
            self.tree.grid(row=0,column=0)
            self.tree.tag_configure("tree",font="courier 8")
        for job in self.joblist:
            self.tree.insert("","end",values =job,tags=("tree","grn"))


        frame.grid(row=1, column=0,padx=(120,0))

    def spawn_parameters_window(self):

        for child in self.winfo_children():
            child.destroy()
        win = tkinter.Frame(self,width= 1500,height = 900,bg = "white")
        win.grid_propagate(False)
        win.grid(row=0,column=0)
        outerFrame = tkinter.Frame(win,bg = "white")

        ###
        ### set up the top left frame
        ###

        frame = tkinter.Frame(outerFrame,width=330,height = 150,bg = "white",relief=tkinter.GROOVE,borderwidth=2)
        frame.grid_propagate(False)
        tkinter.Label(frame, text="Job No", bg="white").grid(row=0, column=0, pady=10, padx=(40, 0))
        tkinter.Label(frame,text = "Job Name",bg = "white").grid(row=1,column = 0,pady = 10,padx=(40,0))
        tkinter.Label(frame, text="Date",bg = "white").grid(row=2, column=0, pady=10, sticky="w",padx=(40,0))
        self.entryValues.append(tkinter.StringVar())
        tkinter.Entry(frame, width=20, textvariable=self.entryValues[-1],bg = "white").grid(row=0, column=1, pady=10, padx=10)
        self.entryValues.append(tkinter.StringVar())
        tkinter.Entry(frame, width=20, textvariable=self.entryValues[-1],bg = "white").grid(row=1, column=1, pady=10, padx=10,
                                                                               sticky="w")

        vcmd = (self.register(self.validate_date),"%d","%s","%S")
        self.entryValues.append(tkinter.StringVar())
        e = tkinter.Entry(frame, width=20, textvariable=self.entryValues[-1], bg="white",validate="key",validatecommand=vcmd)
        e.grid(row=2, column=1, pady=10,padx=10, sticky="w")
        e.bind("<FocusOut>", self.validate_date_on_focus_out)



        frame.grid(row=0, column=0, sticky="nw", padx=(100, 10),pady= (70,0))




        ###
        ### set up mid left frame
        ###
        vcmd = (self.register(self.validate_numeric),"%d", "%s","%S")
        frame = tkinter.Frame(outerFrame,width=330,height=350,bg = "white",relief=tkinter.GROOVE,borderwidth=2)
        frame.grid_propagate(False)
        tkinter.Label(frame, text="From", bg="white").grid(row=0, column=1, pady=10, padx=5)
        tkinter.Label(frame, text="To", bg="white").grid(row=0, column=2, pady=10, padx=5)
        tkinter.Label(frame, text="Time Period 1",bg = "white").grid(row=1, column=0,pady = 10,padx = 5,sticky="e")
        tkinter.Label(frame, text="Time Period 2",bg = "white").grid(row=2, column=0,pady = 10,padx = 5,sticky="e")
        tkinter.Label(frame, text="Time Period 3",bg = "white").grid(row=3, column=0,pady = 10,padx = 5,sticky="e")
        tkinter.Label(frame, text="Time Period 4",bg = "white").grid(row=4, column=0,pady = 10,padx = 5,sticky="e")
        for i in range(1, 5):
            self.entryValues.append(tkinter.StringVar())
            e = tkinter.Entry(frame, width=10, textvariable=self.entryValues[-1], bg="white",validate="key",validatecommand=vcmd)
            e.grid(row=i, column=1, pady=10,padx=5)
            e.bind("<FocusOut>",self.validate_hhmm)
            self.entryValues.append(tkinter.StringVar())
            e = tkinter.Entry(frame, width=10, textvariable=self.entryValues[-1], bg="white",validate="key",validatecommand=vcmd)
            e.grid(row=i, column=2, pady=10,padx=5)
            e.bind("<FocusOut>", self.validate_hhmm)
        tkinter.Label(frame, text="Interval", bg="white").grid(row=5, column=0, pady=10, padx=10, sticky="e")
        self.entryValues.append(tkinter.StringVar())
        box = ttk.Combobox(frame, textvariable=self.entryValues[-1], width=15)
        box["values"] = ("5", "15", "30", "60")
        box.grid(row=5, column=1,columnspan = 3)
        frame.grid(row=1, column=0, padx=(100, 10), pady=20)

        ###
        ### set up lower left frame
        ###


        frame = tkinter.Frame(outerFrame, width=330,height =60, bg="white", relief=tkinter.GROOVE, borderwidth=2)
        frame.grid_propagate(False)
        tkinter.Label(frame, text="No of Cameras", bg="white").grid(row=0, column=0, pady=10, padx=10, sticky="e")
        self.entryValues.append(tkinter.StringVar())
        tkinter.Entry(frame, width=10, textvariable=self.entryValues[-1], bg="white").grid(row=0, column=1, pady=10,
                                                                                           padx=0, sticky="w")
        tkinter.Button(frame,text = "Update",height =1,command = self.update_movement_window).grid(row=0,column=2,padx=10)
        frame.grid(row=2,column=0,sticky="nw", padx=(100, 10))
        outerFrame.grid(row=0, column=0)

        ###
        ### set up classification frame
        ###
        outerFrame = tkinter.Frame(win, bg="white")
        frame = tkinter.Frame(outerFrame,bg = "white", width = 300,height = 520, relief=tkinter.GROOVE, borderwidth=2)
        frame.grid_propagate(False)
        tkinter.Label(frame, text="Classification",bg = "white").grid(row=0, column=0,columnspan = 3)
        tkinter.Label(frame, text="Overview",bg = "white").grid(row=1, column=0, pady=10, padx=10)
        tkinter.Label(frame, text="ANPR classes",bg = "white").grid(row=1, column=1, pady=10, padx=10)

        for i in range(10):
            self.entryValues.append(tkinter.StringVar())
            tkinter.Entry(frame, width=10, textvariable=self.entryValues[-1],bg = "white").grid(row=2 + i, column=0, pady=10, padx=10)
            self.entryValues.append(tkinter.StringVar())
            tkinter.Entry(frame, width=10, textvariable=self.entryValues[-1],bg = "white").grid(row=2+i, column=1, pady=10, padx=10)
        frame.grid(row=0,column =1,sticky="nw")


        ###
        ### frame with buttons
        ###

        frame = tkinter.Frame(outerFrame, bg="white", width=300, height=70)
        tkinter.Button(frame, text="Back", bg="white",command=self.spawn_survey_setup_screen).grid(row=0, column=0, padx=10,sticky="w")
        tkinter.Button(frame,text="Save",bg = "white",command=self.save_job).grid(row=0,column=1,padx = 10,sticky = "e")
        frame.grid(row=1,column=1,pady=30)
        outerFrame.grid(row=0, column=1,pady=(95,0))


        ###
        ### movements frame
        ###

        outerFrame = tkinter.Frame(win, bg="white", width=1000, height=880)
        outerFrame.grid_propagate(False)
        frame = tkinter.Frame(outerFrame, bg="white", width=1100, height=200)
        tkinter.Label(frame, text="On Site Movements", bg="white").grid(row=0, column=0,columnspan=3)
        tkinter.Label(frame, text="ANPR Movements", bg="white").grid(row=0, column=3,columnspan=3,padx = (200,0))
        tkinter.Label(frame, text="Site", bg="white").grid(row=1, column=0,padx = (10,0))
        tkinter.Label(frame, text="Cam", bg="white").grid(row=1, column=1,padx = (60,0))
        tkinter.Label(frame, text="Mvmt", bg="white").grid(row=1, column=2,padx = (60,0))
        tkinter.Label(frame, text="Movement", bg="white").grid(row=1, column=3,padx = (150,90))
        tkinter.Label(frame, text="Dir", bg="white").grid(row=1, column=4,padx = 0)
        tkinter.Label(frame, text="", bg="white").grid(row=1, column=5, padx=0)
        frame.grid(row=0, column=0)
        self.movementsFrame = tkinter.Frame(outerFrame,bg="white", width=800, height=888, relief=tkinter.GROOVE, borderwidth=3)
        self.movementsFrame.grid_propagate(False)
        self.movementsFrame.grid(row=1,column  = 0,columnspan = 6,padx =0,pady=0)
        outerFrame.grid(row=0, column=2, pady=(10, 0),padx=10)

    def edit_job(self):
        if self.tree.selection() == "":
            return
        jobname = self.tree.item(self.tree.selection()[0])
        print("selected job", jobname["values"])
        self.currentJob = myDB.load_job(jobname["values"][0], jobname["values"][1], jobname["values"][2])
        self.spawn_parameters_window()
        job = self.currentJob
        self.entryValues[0].set(job["jobno"])
        self.entryValues[1].set(job["jobname"])
        self.entryValues[2].set(datetime.datetime.strftime(job["surveydate"], "%d/%m/%y"))

        t =job["timeperiod1"]
        self.entryValues[3].set(t.split("-")[0])
        self.entryValues[4].set(t.split("-")[1])
        t = job["timeperiod2"]
        self.entryValues[5].set(t.split("-")[0])
        self.entryValues[6].set(t.split("-")[1])
        t = job["timeperiod3"]
        self.entryValues[7].set(t.split("-")[0])
        self.entryValues[8].set(t.split("-")[1])
        t = job["timeperiod4"]
        self.entryValues[9].set(t.split("-")[0])
        self.entryValues[10].set(t.split("-")[1])
        self.entryValues[12].set(job["noofcameras"])
        self.entryValues[11].set(job["interval"])
        classes = job["classification"].split(",")
        for index,e in enumerate(self.entryValues[13:33]):
            if index < len(classes):
                e.set(classes[index])

        print("no of sites is",job["sites"])
        self.update_movement_window()
        sites = job["sites"]
        print("sites are ",sites)
        print("no of entry values is",len(self.entryValues))
        if len(self.entryValues) > 33:
            print("no of entry values is", len(self.entryValues))
            count = 1
            for i in range(0, len(self.entryValues[33:]), 4):
                for siteNo,site in sites.items():
                    #print("site no",siteNo,"site",site)
                    for newmvNo,mvmt in site.items():
                        #print("newmvno",newmvNo,"oldmovements",mvmt)
                        for oldMv in mvmt["originalmovements"]:
                            if oldMv == count:
                                self.entryValues[33 + i].set(siteNo)
                                self.entryValues[33 + i + 2].set(newmvNo)
                                self.entryValues[33 + i + 3].set(mvmt["dir"])
                count += 1

    def spawn_duplicates_window(self):
        try:
            e = self.currentJob["duplicateValues"]
        except KeyError as e:
            messagebox.showinfo(message="No plates loaded, cant display duplicates")
            return
        for child in self.winfo_children():
            child.destroy()
        win = tkinter.Frame(self, width=1500, height=900, bg="white")
        win.grid_propagate(False)
        win.grid(row=0, column=0)
        f = tkinter.font.Font(family="helvetica", size=10)
        tkinter.Label(win,text = "Duration",font = f,bg = "Light blue").grid(row=0,column=0,padx=(400,0), pady=(100, 10))
        tkinter.Label(win, text="VRN Count",font = f,bg = "Light blue").grid(row=0, column=1, pady=(100, 10))
        tkinter.Label(win, text="Duration",font = f,bg = "Light blue").grid(row=0, column=2, padx=(400, 0), pady=(100, 10))
        tkinter.Label(win, text="VRN Count",font = f,bg = "Light blue").grid(row=0, column=3, pady=(100, 10))
        for i in range(31):
            colour = "white"
            if self.currentJob["selectedduplicates"] != -1:
                if self.currentJob["selectedduplicates"] == i:
                    colour = "red"
            l = tkinter.Label(win,text = datetime.timedelta(seconds = i),font = f,bg = colour)
            l.grid(row=i+1,column = 0, padx=(400, 0))
            l.bind("<Double-Button-1>",self.select_duplicate)
            tkinter.Label(win,text = self.currentJob["duplicateValues"][i],font = f,bg = "white").grid(row=i+1,column = 1)
            colour = "white"
            if self.currentJob["selectedduplicates"] != -1:
                if self.currentJob["selectedduplicates"] == i+31:
                    colour = "red"
            l = tkinter.Label(win, text=datetime.timedelta(seconds=i*15),font = f,bg= colour)
            l.grid(row=i + 1, column=2, padx=(400, 0))
            l.bind("<Double-Button-1>", self.select_duplicate)
            tkinter.Label(win, text=self.currentJob["duplicateValues"][i+31],font = f,bg = "white").grid(row=i+1, column=3)
        tkinter.Button(win,text = "Back",font = f,command = self.spawn_home_window).grid(row = 32,column = 4,padx=(400,0))

    def select_duplicate(self,event):
        index = 0
        print("widget is",event.widget,event.widget.cget("text"),event.widget.grid_info())
        text = event.widget.cget("text")
        info = event.widget.grid_info()
        if info["column"] == 2:
            index = 31
        index = index + info["row"] -1
        print("selected index is",index)
        self.currentJob["selectedduplicates"] = index
        myDB.update_duplicates(self.currentJob["id"],index)
        self.setDuplicatesFunction(index,self.currentJob)
        self.spawn_duplicates_window()

    def validate_comparison_entry(self,action,text,char):
        if action == "0":  ### action 0 is delete. We dont mind what they delete
            return True
        return char.isdigit()

    def validate_date(self,action,text,char):
        if action == "0":
            return True
        print("text is",text,"char is ",char)
        if len(text)== 8:
            return False
        if len(text) == 2 or len(text) == 5:
            return(char =="/")
        else:
            return char.isdigit()
        return False

    def validate_date_on_focus_out(self,event):
        ###
        ### validate that a correct date , in a correct format, has been entered
        text = event.widget.get()
        try:
            d = datetime.datetime.strptime(text,"%d/%m/%y")
        except Exception as e:
            messagebox.showinfo(message=text + " isnt a valid date, must be in format dd/mm/yy")
            event.widget.delete(0,tkinter.END)

    def validate_numeric(self,action,text,char):
        ###
        ### validate that only numbers, or a colon, can be entered in the cells for the project times on the project setup screen
        ###

        if action == "0": ### action 0 is delete. We dont mind what they delete
            return True
        if len(text) ==5:### dont allow any string greater than length 5
            return False
        if len(text) == 2: ### if 2 numbers have been entered, the next char must be a :
            return (char == ":" or char == ":00")
        if len(text)==1:
            if char == ":":
                pass
        return(char.isdigit() or char == ":00")

    def validate_hhmm(self,event):
        ###
        ### validate the user input for the project times on the project setup screen, when the input widget loses focus.
        ### if the user enters only 1 number, the rest is filled in. Eg they enter 4, the value of cell is 04:00
        ### similarly with 2 numbers, :00 is added to the end
        ###
        text = event.widget.get()
        if text.strip() == "":
            return
        if len(text) > 5:
            event.widget.delete(0, tkinter.END)
            messagebox.showinfo(message="not a valid time")
            return

        elif len(text) == 1:
            if not text.isdigit():
                event.widget.delete(0,tkinter.END)
                messagebox.showinfo(message="not a valid time")
                return
            event.widget.insert(0,0)
            event.widget.insert(tkinter.END, ":00")
        elif len(text) == 2:
            if not text.isdigit():
                event.widget.delete(0, tkinter.END)
                messagebox.showinfo(message="not a valid time")
                return
            event.widget.insert(tkinter.END,":00")
        elif len(text) == 3 and text[-1] == ":":
            if not text[:-1].isdigit():
                event.widget.delete(0, tkinter.END)
                messagebox.showinfo(message="not a valid time")
                return
            event.widget.delete(len(text)-1,tkinter.END)
            event.widget.insert(tkinter.END, ":00")
        elif ":" not in text:
            event.widget.delete(0, tkinter.END)
            messagebox.showinfo(message="not a valid time")
            return

        t = event.widget.get()
        hours = t.split(":")[0]
        mins = t.split(":")[1]
        if int(hours) > 23 or int(mins) > 60:
            event.widget.delete(0, tkinter.END)
            messagebox.showinfo(message="not a valid time")
            return
        if len(mins) == 1:
            event.widget.insert(tkinter.END,"0")
        if len(hours) == 1:
            event.widget.insert(0, "0")

    def save_job(self):
        ###
        ### save the job details entered in the form, to the main job database
        ###

        ###
        ### set up a dictionary containing all the details entered on the form
        job = {}

        job["jobno"] = self.entryValues[0].get()
        job["jobname"]=self.entryValues[1].get()
        job["surveyDate"]= self.entryValues[2].get()
        if self.entryValues[3].get()=="" or  self.entryValues[4].get() == "":
            messagebox.showinfo(message="You must enter at least one time period")
            return
        else:
            ### TODO: verify end time is after start time, verify that if one is filled, the other is filled

            job["timeperiod1"] = self.entryValues[3].get() + "-" + self.entryValues[4].get()
        job["timeperiod2"] = self.entryValues[5].get() + "-" + self.entryValues[6].get()
        job["timeperiod3"] = self.entryValues[7].get() + "-" + self.entryValues[8].get()
        job["timeperiod4"] = self.entryValues[9].get() + "-" + self.entryValues[10].get()
        job["noOfCameras"] =self.entryValues[12].get()
        job["interval"] = self.entryValues[11].get()
        cl = [str(x.get()) for x in self.entryValues[13:33] if x.get() != ""]
        print("classification is",cl)
        job["classification"] = ",".join(cl)

        ###
        ### do some basic checking to make sure that a value has been entered for each key in the dictionary
        ### prompt the user if they havent
        ###
        for key,value in job.items():
            print(key,value)
            if value =="":
                messagebox.showinfo(message="You must enter " + key)
                return

        ###
        ### set up the site data
        ###
        data = {}
        data["job"] = job
        data["sites"] = []
        if len(self.entryValues) >33: ### the site details start at entryValues[33]
            count = 1
            for i in range(0,len(self.entryValues[33:]),4):
                if self.entryValues[33 +i+2].get() != "":
                    if self.entryValues[33 + i+3].get()==0:
                        messagebox.showinfo(message="For site " + self.entryValues[33+i].get() + " movement " + str(count) + " you havent selected a direction")
                        return
                    l =[self.entryValues[33+i].get(),self.entryValues[33 +i+2].get(),count,self.entryValues[33 + i+3].get(),self.entryValues[33 +i+1].get()] # [Site no, new movement no, old movement no, dir,cam]
                    data["sites"].append(l)
                count+=1



        ###
        ### prompt the user to select the location for storing any files and data produced by the software
        ###

        dir = filedialog.askdirectory(title="Please select Project Location",initialdir="S:\\SCOTLAND DRIVE 2\\JOB FOLDERS\\")
        if dir == "":
            messagebox.showinfo(message="No Project Location selected, project not saved")
            return
        job["folder"] = dir
        myDB.save_Job(data)
        self.spawn_survey_setup_screen()

    def update_movement_window(self):
        ###
        ### when setting up a project, we need to enter the relations between site numbers, old movement numbers,
        ### new movement numbers, etc. The number of movements is 2 * the number of cameras in the project
        ### this function fills out the window with the required number of widgets
        ###

        ###
        ### delete any previous stored entryValues
        ###

        print("no of existing entryvalues is",len(self.entryValues))
        if self.numCams >0 and len(self.entryValues)>33:
            for i in range(self.numCams  * 8): ## 4 variables, 2 rows, for each cam
                del self.entryValues[-1]

        for child in self.movementsFrame.winfo_children():
            child.destroy()
        self.numCams = int(self.entryValues[12].get())
        count = int(self.entryValues[12].get()) * 2

        ###
        ### set up the label frame
        ###

        scrollframe = VerticalScrolledFrame(self.movementsFrame,bg="beige")
        for i in range(count):
            self.entryValues.append(tkinter.StringVar())
            tkinter.Entry(scrollframe.interior,textvariable=self.entryValues[-1],width = 5).grid(row=i,column = 0, padx=(25,0))
            self.entryValues.append(tkinter.StringVar())
            tkinter.Entry(scrollframe.interior, textvariable=self.entryValues[-1],width = 8).grid(row=i, column=1, padx=(60,0))
            self.entryValues.append(tkinter.StringVar())
            tkinter.Entry(scrollframe.interior, textvariable=self.entryValues[-1], width=5).grid(row=i, column=3,padx=(150,10))
            tkinter.Label(scrollframe.interior, text=str(i + 1),bg="white").grid(row=i, column=2, padx=(70,10))
            self.entryValues.append(tkinter.IntVar())
            tkinter.Radiobutton(scrollframe.interior,text = "In",variable=self.entryValues[-1],value=1,bg="white").grid(row=i,column = 4,padx=(50,0))
            tkinter.Radiobutton(scrollframe.interior, text="Out", variable=self.entryValues[-1],value=2,bg="white").grid(row=i, column=5)
            tkinter.Radiobutton(scrollframe.interior, text="both", variable=self.entryValues[-1],value=3,bg="white").grid(row=i, column=6,padx =(0,30))
        scrollframe.grid(row=1,column = 0,padx = 0,pady=0)

    def spawn_summary_window(self):
        ###
        ### the summary window displays a summary of all sites in the project, in a pop up window.
        ###

        win = tkinter.Toplevel(self)
        win.protocol("WM_DELETE_WINDOW",lambda: self.summary_window_closed(win))
        f = tkinter.font.Font(family="helvetica",size=18)
        win.state("zoomed")
        frame = tkinter.Frame(win)
        frame.grid(row=0,column=0)
        tkinter.Label(frame,text = "Summary",font=f).grid(row=0,column=0)
        cols = ("Movement", "Site", "OVCount", "VRN Count", "Av % Capture", "Min % Capture", "Max % Capture",
                "Time < 85%","Comments")
        self.summaryTree = ttk.Treeview(frame, columns=tuple(range(len(cols))), show="headings", height=40)
        for i, col in enumerate(cols):
            self.summaryTree.heading(i, text=col)
            self.summaryTree.column(i, width=20, anchor=tkinter.CENTER,stretch=tkinter.NO)
        self.summaryTree.column(i,width=500)
        self.summaryTree.grid(row=1,column=0,padx = 100,pady=30)
        self.summaryTree.bind("<Double-Button-1>",self.comment_clicked)
        self.summaryTree.bind("<Button-3>", self.movement_selected_via_summary)
        self.update_summary_screen()

    def movement_selected_via_summary(self,event):
        curItem = event.widget.identify_row(event.y)
        movement = self.summaryTree.item(curItem)["values"][0]
        movementList = self.movementBox.cget("values")
        self.movementBox.current(movementList.index("Movement " + str(movement)))
        self.movementBox.event_generate("<<ComboboxSelected>>", when="tail")

    def summary_window_closed(self,win):
        self.summaryTree = None
        win.destroy()

    def spawn_home_window(self):
        ###
        ### this window shows once the user has loaded a job. It allows the user to do various
        ### tasks related to the ANPR project
        ###

        for child in self.winfo_children():
            child.destroy()
        self.colourLabels = []
        self.summaryTree = None
        self.img = ImageTk.PhotoImage(Image.open("folder-icon.jpg").resize((30,30),Image.ANTIALIAS))

        frame = tkinter.Frame(self, bg="white")
        f = tkinter.font.nametofont("TkDefaultFont").configure(size=14)
        d = datetime.datetime.strftime(self.currentJob["surveydate"],"%d/%m/%y")
        tkinter.Label(frame, text=self.currentJob["jobno"] + " " + self.currentJob["jobname"]+ " " + d , bg="white",relief = tkinter.GROOVE,borderwidth = 2).grid(row=0, column=2,columnspan = 10,ipadx =30,pady = (10,30))
        tkinter.Button(frame,image=self.img).grid(row=0,column=14,padx=10,pady = (10,30))
        tkinter.Label(frame,text = "Overviews", bg="white",relief = tkinter.GROOVE,borderwidth = 2).grid(row=1,column = 0,ipadx =30)
        tkinter.Button(frame, text="Create Overview \nCount Template", width=17, bg="white", height=3,
                       command=self.export_OVTemplate).grid(row=2, column=0, padx=20, pady=20)
        tkinter.Button(frame, text="Load Overview \nCount Results", width=17, height=3, bg="white",command=self.load_OV_counts).grid(row=2, column=1, padx=20,
                                                                                             pady=20)
        tkinter.Label(frame, text="VRNs", bg="white",relief = tkinter.GROOVE,borderwidth = 2).grid(row=3, column=0,ipadx =30)
        tkinter.Button(frame, text="Load Unclassed\n VRNs", width=17, height=3, bg="white",command = self.load_unclassed_plates).grid(row=4, column=0,
                                                                                                    padx=20,pady=20)
        tkinter.Button(frame, text="Load Classed\n VRNs", width=17, height=3, bg="white",command=self.load_classes).grid(row=4, column=1,
                                                                                                 padx=20, pady=20)
        tkinter.Button(frame, text="Duplicate Removal", width=17, height=3, bg="white",command=self.spawn_duplicates_window).grid(row=4, column=2,padx=20,
                                                                                                        pady=20)
        tkinter.Label(frame, text="Comparison", bg="white",relief = tkinter.GROOVE,borderwidth = 2).grid(row=5, column=0,ipadx =30)
        tkinter.Button(frame, text="View Comparison", width=17, height=3, bg="white",command= self.get_comparison_data).grid(row=6, column=0,
                                                                                                 padx=20, pady=20)
        tkinter.Button(frame, text="Create Client\nComparison", width=17, height=3, bg="white").grid(row=6, column=1,
                                                                                               padx=20, pady=20)

        tkinter.Label(frame, text="Matching", bg="white",relief = tkinter.GROOVE,borderwidth = 2).grid(row=7, column=0,ipadx =30)
        tkinter.Button(frame, text="Open/Closed\nCordon", width=17, height=3, bg="white",command=self.spawn_cordon_screen).grid(row=8, column=0,
                                                                                           padx=20, pady=20)
        tkinter.Button(frame, text="First/Last Seen", width=17, height=3, bg="white").grid(row=8, column=1,
                                                                                                     padx=20, pady=20)
        tkinter.Button(frame, text="Route Assignment", width=17, height=3, bg="white").grid(row=8, column=2, padx=20,
                                                                                             pady=20)
        tkinter.Button(frame, text="Overtaking", width=17, height=3, bg="white").grid(row=8, column=2, padx=20,
                                                                                             pady=20)
        tkinter.Button(frame, text="Back", width=10, height=1, bg="white",command = self.spawn_survey_setup_screen).grid(row=9, column=0, padx=20,
                                                                                      pady=20)
        frame.grid(row=0, column=0, pady=(120, 0), padx=(320, 0))

    def comment_clicked(self,event):
        curItem = event.widget.identify_row(event.y)
        print(event.widget.identify_column(event.y))
        values = self.summaryTree.item(curItem)["values"]
        self.spawn_comment_window(values[-1])

    def spawn_comment_window(self,text):
        win = tkinter.Toplevel(self)
        win.protocol("WM_DELETE_WINDOW", lambda:self.destroy__window(win))
        txt = tkinter.Text(win)
        txt.grid(row=0,column=0)
        txt.focus_set()
        txt.insert("1.0",text)
        tkinter.Button(win,text="Save",command=lambda: self.save_comment(txt,win)).grid(row=1,column=0)

    def spawn_settings_window(self):
        f = tkinter.font.Font(family='Courier', size=9, weight='bold')
        win = tkinter.Toplevel(self)
        win.protocol("WM_DELETE_WINDOW", lambda: self.destroy__window(win))
        tkinter.Label(win,text = "Please Enter Your Name",font = f).grid(row=0,column = 0,padx=10,pady=10)
        e = tkinter.Entry(win,width = 20,font = f)
        e.grid( row=0,column=1,padx=10,pady=10)
        tkinter.Label(win,text="Please Select Database file",font = f).grid(row=1, column=0,padx=10,pady=10)
        l = tkinter.Label(win,text="None",font = f,width = 40)
        l.grid(row=1, column=1,padx=10,pady=10)
        name,file = self.load_settings()
        e.delete(0, tkinter.END)
        e.insert(0, name)
        l.configure(text=file)
        tkinter.Button(win,text = "Select",font = f,command=lambda:self.get_database_file_location(l)).grid(row=1,column=2,padx=10,pady=10)
        tkinter.Button(win, text="Save", font=f,command=lambda:self.save_settings(e,l,win)).grid(row=2, column=2,padx=10,pady=10)

    def save_settings(self,e,l,win):
        name = e.get()
        file = l.cget("text")
        print("name is",name,"file is",file)
        if (name == "") | (file == ""):
            messagebox.showinfo(message="You need to enter a name, and select a database location")
            return
        dir = os.getcwd()
        print("dir is",dir)
        f = open("settings.txt","w")
        f.write(name + "\n")
        f.write(file+ "\n")
        if self.selectedDuplicates is None:
            f.write("\n")
        else:
            f.write(str(self.selectedDuplicates) + "\n")
        self.destroy__window(win)

    def load_settings(self):
        f = open("settings.txt", "r")
        try:
            name = f.readline().rstrip()
            file = f.readline().rstrip()
            val = f.readline().rstrip()
            if val != "" :
                self.selectedDuplicates = int(val)
        except Exception as e:
            print(e)
            return ["",""]
        myDB.set_file(file)
        return([name,file])

    def get_database_file_location(self,label):
        ###
        ### prompt the user with a file navigation dialog, to select the location of the job database
        ### display the selected location in a label in the settings window
        ###
        file = filedialog.askopenfilename()
        if file == "":
            messagebox.showinfo(message="You need to select a database file")
            label.configure(text="")
            return
        label.configure(text=file)

    def save_comment(self,txt,win):
        ###
        ### get the comment entered by the user in the pop up text box, save it to the Db
        ### then destroy the pop up window
        ###
        contents = txt.get("1.0",tkinter.END).strip().rstrip("\n").replace("\n"," ")
        row = self.summaryTree.item(self.summaryTree.selection())
        values = row["values"]
        siteNo = values[1]
        move  = values[0]
        myDB.update_comment(self.currentJob["id"], siteNo,move,contents)
        values[-1]=contents
        index = self.summaryTree.index(self.summaryTree.selection())
        self.currentJob["comments"][index] = contents
        self.summaryTree.item(self.summaryTree.selection(),values=values)
        win.destroy()

    def destroy__window(self,win):
        win.destroy()

    def set_up_comparison_display(self):
        self.comparisonDataStructure = [] ### stores the widgets which display the data

        ###
        ### set up a list containing lists of vehicle classes, so we can set up the correct number of columns
        ### in each section
        ###

        classes = []
        seen = set()
        OVClasses = [x for i, x in enumerate(self.currentJob["classification"].split(",")) if
                     i % 2 == 0 and x not in seen and not seen.add(x)]
        classes.append(OVClasses)
        seen = set()
        ANPRClasses = [x for i, x in enumerate(self.currentJob["classification"].split(",")) if
                       i % 2 == 1 and x not in seen and not seen.add(x)]
        classes.append(ANPRClasses)
        classes.append(ANPRClasses)

        ###
        ### destroy any widgets in the window
        ###
        for child in self.winfo_children():
            if type(self.nametowidget(child))!= tkinter.Toplevel:
                child.destroy()


        win = tkinter.Frame(self, width=self.winfo_screenwidth(), height=self.winfo_screenheight(), bg="white", padx=20,
                            pady=20)
        win.columnconfigure(0,weight=1)
        f = tkinter.font.Font(family='Helvetica', size=10, weight='bold')
        appHighlightFont = font.Font(family='Helvetica', size=8)
        boldFont = font.Font(family='Helvetica', size=8, weight="bold")
        timeFont = tkinter.font.Font(family='Courier', size=9, weight='bold')
        frame = tkinter.Frame(win,bg ="white", width=self.winfo_screenwidth(), height=self.winfo_screenheight())
        frame.columnconfigure(0,weight = 1)
        tkinter.Label(frame,text="Comparison Type", bg="white",font = f).grid(row = 0,column = 0,padx=(20,10),pady=(10,10))
        box = ttk.Combobox(frame, width=20,font = f)
        box["values"] = ("Unclassed","Classed")
        box.bind("<<ComboboxSelected>>", self.boxChanged)
        box.current(self.box1Value)
        tkinter.Button(frame,text="Summary",command=self.spawn_summary_window,font = f).grid(row = 0,column = 2,padx = 20)
        self.revertButton = tkinter.Button(frame, text="Revert", font=f)
        self.revertButton.grid(row=0, column=3, padx=20,sticky="e")
        self.revertButton.bind("<Button-1>",self.revert)
        tkinter.Button(frame, text="Back", command=self.spawn_home_window, font=f).grid(row=0, column=4, padx=20)
        box.grid(row=0, column=1)

        tkinter.Label(frame, text="VRNs", bg="white",width = 14,anchor=tkinter.E,font = f).grid(row=1, column=0,padx=(20,10),pady=(10,10))
        box = ttk.Combobox(frame, width=20,font = f)
        box["values"] = ("Original VRNs", "Duplicates Removed")
        box.bind("<<ComboboxSelected>>", self.boxChanged)
        box.current(self.box2Value)
        box.grid(row=1, column=1)
        self.siteLabel = tkinter.Label(frame, text="Site 1", bg="white", width=14, anchor=tkinter.E, font=f)
        self.siteLabel.grid(row=1, column=2,padx=(50, 10),pady=(10, 10))


        tkinter.Label(frame, text="Select Mvmt", bg="white", width=14, anchor=tkinter.E, font=f).grid(row=1, column=4,
                                                                                                      padx=(20, 10),
                                                                                                      pady=(10, 10))
        ###
        ### get list of movements
        ###
        mvmts = []
        for site in self.dataList:
            [mvmts.append("Movement " + str(key)) for key, movement in sorted(site["movements"].items())]
        self.movementBox = ttk.Combobox(frame, width=15, font=f)
        self.movementBox["values"] = mvmts
        self.movementBox.grid(row=1, column=5)
        self.movementBox.current(0)
        self.movementBox.bind("<<ComboboxSelected>>", self.movementChanged)
        self.currentSelected[1] = int(mvmts[0].replace("Movement",""))
        tkinter.Button(frame,text="<",command=lambda :self.scroll_through_movements("left")).grid(row = 1,column = 7,padx = 10, pady=10)
        tkinter.Button(frame, text=">", command=lambda :self.scroll_through_movements("right")).grid(row=1, column=8, padx=10, pady=10)
        frame.grid(row=0,column=0,sticky = "w")
        win.grid(row=0, column=0)

        vcmd = (self.register(self.validate_edit), "%d", "%s", "%S")
        site = self.dataList[0]
        l = [movement for key, movement in sorted(site["movements"].items())]
        movement = l[0]
        displayedData = []
        displayedData.append(movement["data"][1])
        displayedData.append(movement["data"][2])
        displayedData.append(movement["data"][2]) ### we dont actually display this data, this is just used to build the structure of the 3rd section
        innerFrame = tkinter.Frame(win)
        scrollframe = VerticalScrolledFrame(innerFrame, bg="white")
        scrollframe.grid(row=0, column=0)
        frame = tkinter.Frame(scrollframe.interior, bg="beige", width=820)
        frame.grid(row=0, column=0)
        innerFrame.grid(row=1,column=0,padx =450,pady = (30,0))
        col = 0
        tkinter.Label(frame, text="OV Count", font=appHighlightFont, bg="beige").grid(row=1, column=col,
                                                                                      columnspan=len(
                                                                                          classes[0]) + 4,
                                                                                      padx=2, pady=20)

        tkinter.Label(frame, text="ANPR Count", font=appHighlightFont, bg="beige").grid(row=1,
                                                                                        column=col + len(
                                                                                            classes[0]) + len(
                                                                                            classes[1]),
                                                                                        columnspan=len(
                                                                                            classes[1]) + 4,
                                                                                        padx=2, pady=20)
        tkinter.Label(frame, text="Comparison", font=appHighlightFont, bg="beige").grid(row=1,
                                                                                        column=col + (2 * len(
                                                                                            classes[1])) + len(
                                                                                            classes[0]),
                                                                                        columnspan=len(
                                                                                            classes[1]) + 8,
                                                                                        padx=2, pady=20)

        if col != 0:
            ttk.Separator(frame, orient="vertical", style="sep.TSeparator").grid(row=0, column=col,
                                                                                 rowspan=1000,
                                                                                 padx=60, pady=4, sticky="ns")
            col += 1

        for i, d in enumerate(displayedData):
            print(i,"th block of data is",d)
            block = []
            first = True
            rowNo = 4
            for index, cl in enumerate(classes[i]):
                tkinter.Label(frame, text=cl, font=appHighlightFont, bg="beige").grid(row=2,
                                                                                      column=col + index + 2,
                                                                                      padx=2, pady=2)
            ttk.Separator(frame, orient="horizontal").grid(row=3, column=col, pady=4, columnspan=10,
                                                           sticky="ew")
            ttk.Separator(frame, orient="vertical").grid(row=3, column=col + 1, rowspan=1000, pady=4, padx=0,
                                                         sticky="ns")
            ttk.Separator(frame, orient="vertical").grid(row=3, column=col + 2 + len(classes[i]), rowspan=1000,
                                                         padx=0, pady=4, sticky="ns")
            tkinter.Label(frame, text="Total", font=appHighlightFont, bg="beige").grid(row=2,
                                                                                       column=col + 3 + len(
                                                                                           classes[i])
                                                                                       , padx=(2, 20), pady=2)

            for row in d:
                entryValueRow = []
                if row[0] == "1 Hr" :
                    ttk.Separator(frame, orient="horizontal").grid(row=rowNo, column=col, pady=4, columnspan=10,
                                                                   sticky="ew")
                    ttk.Separator(frame, orient="horizontal").grid(row=rowNo + 2, column=col, pady=4,
                                                                   columnspan=10, sticky="ew")
                    rowNo += 1
                    for j, item in enumerate(row):
                        if j == 0:
                            s = tkinter.StringVar()
                            lbl = tkinter.Label(frame, font=timeFont, fg="black",textvariable = s,
                                                bg="lemon chiffon")
                            lbl.grid(row=rowNo, column=col, padx=2, pady=2)
                            entryValueRow.append(s)
                            s.set(item)
                        elif j == len(row) - 1:
                            s = tkinter.StringVar()
                            lbl = tkinter.Label(frame, font=boldFont,textvariable = s,
                                                bg="beige")
                            lbl.grid(row=rowNo, column=col + j + 2, padx=(2, 20), pady=2)
                            entryValueRow.append(s)
                            s.set(int(item))
                            if i == 2:
                                self.colourLabels.append(lbl)
                        else:
                            s = tkinter.StringVar()
                            lbl = tkinter.Label(frame, font=boldFont,textvariable = s,
                                                bg="beige")
                            lbl.grid(row=rowNo, column=col + j + 1, padx=2, pady=2)
                            entryValueRow.append(s)
                            s.set(int(item))
                            if i == 2:
                                self.colourLabels.append(lbl)
                    rowNo += 2
                else:
                    for j, item in enumerate(row):
                        if j == 0:
                            s = tkinter.StringVar()
                            lbl = tkinter.Label(frame, font=timeFont, fg="black",textvariable = s,bg="lemon chiffon")
                            lbl.grid(row=rowNo, column=col, padx=2, pady=2)
                            s.set(item)
                            entryValueRow.append(s)
                        elif j == len(row) - 1:
                            s = tkinter.StringVar()
                            lbl = tkinter.Label(frame, font=boldFont,textvariable = s,bg="beige")
                            lbl.grid(row=rowNo, column=col + j + 2, padx=(2, 20), pady=2)
                            entryValueRow.append(s)
                            s.set(int(item))
                            if i == 2:
                                self.colourLabels.append(lbl)
                        else:
                            if i == 0:
                                s = tkinter.StringVar()
                                e = tkinter.Entry(frame, width=4, font=appHighlightFont, textvariable = s,
                                                  bg="beige", validate="key", validatecommand=vcmd)
                                e.grid(row=rowNo, column=col + j + 1, padx=2, pady=2)
                                s.set(int(item))
                                entryValueRow.append(s)
                                e.bind("<Return>", self.edit_cell)
                                e.bind("<Tab>", self.edit_cell)
                                e.bind("<FocusOut>",self.edit_cell)
                            else:
                                s = tkinter.StringVar()
                                lbl = tkinter.Label(frame, font=appHighlightFont,textvariable = s,bg="beige")
                                lbl.grid(row=rowNo, column=col + j + 1, padx=2, pady=2)
                                if i ==2 :
                                    self.colourLabels.append(lbl)
                                entryValueRow.append(s)
                                s.set(int(item))
                    rowNo += 1
                block.append(entryValueRow)
            self.comparisonDataStructure.append(block)
            self.update()
            self.update_idletasks()
            col += 4 + len(OVClasses)
        self.update_comparison_display()

    def scroll_through_movements(self,dir):
        ###
        ### using the "arrow" buttons on the comparison screen to move one by one through the
        ### movements , either up or down the movements
        ###
        index = self.movementBox.current()
        values = self.movementBox.cget("values")
        print("movements are",len(values),values)
        print("value is",self.movementBox.get())
        if dir=="left":
            if index >0:
                self.movementBox.current(index-1)
                self.movementBox.event_generate("<<ComboboxSelected>>",when="tail")
        else:
            if index<len(values)-1:
                self.movementBox.current(index + 1)
                print("after,value is", self.movementBox.get())
                self.movementBox.event_generate("<<ComboboxSelected>>", when="tail")

    def edit_cell(self,event):
        ###
        ### deals with when an entry box is edited, it updates the data in the data structure, and saves the data
        ### and then displays the updated data in the comparison display

        entry = event.widget

        ###
        ### find which widget triggered the event
        ###

        for r,row in enumerate(self.comparisonDataStructure[0]):
            for c, item in enumerate(row):
                if entry.cget("textvariable") == item._name:
                    for site in self.dataList:
                        for key, m in site["movements"].items():
                            if self.currentSelected[1] == key:
                                print("selected site is", site["siteNo"])
                                selectedSite = site
                    l = [movement for key, movement in sorted(selectedSite["movements"].items()) if
                         key == self.currentSelected[1]]
                    movement = l[0]
                    if entry.get().isdigit():
                        if movement["data"][1][r][c] != int(entry.get()):

                            ###
                            ### we found the widget, and its value has changed, update the stored data, update the display
                            ### and dump the data to file
                            ###
                            self.displayStatus = "edited"
                            self.revertButton.configure(text="Revert")
                            movement["data"][1][r][c] = int(entry.get())
                            self.update_comparison_display()
                            with open(self.currentJob["folder"] + '/comparisondata.pkl', 'wb') as handle:
                                pickle.dump(self.dataList, handle)
                    else:
                        entry.delete(0,tkinter.END)
                        entry.insert(0,movement["data"][1][r][c])

        try:
            if event.keycode == 13:
                event.widget.tk_focusNext().focus()
        except Exception as e:
            print(e)

    def update_comparison_display(self):
        ###
        ### update whats shown on the comparison screen depending on the selection, eg classed, unclassed etc
        ### and depending on what site and movement is selected
        ###

        for site in self.dataList:
            for key, m in site["movements"].items():
                if self.currentSelected[1] == key:
                    print("selected site is", site["siteNo"])
                    selectedSite = site
        l = [movement for key, movement in sorted(selectedSite["movements"].items()) if key == self.currentSelected[1]]
        movement = l[0]
        self.calculate_display()
        dataIndex = [(0,0),(1,0),(0,1),(1,1)].index((self.box1Value, self.box2Value)) + 2

        ###
        ### set up which data we are going to display
        ### data for each movement is in the form [OVdata,Edited OVdata,ANPRuc/orig,ANPRuc/dupremoved,ANPRc/orig,ANPRc/dupremoved]
        ### dataindex gives us the index of the ANPR data
        ###
        print("selected boxes",(self.box1Value, self.box2Value))
        print("site",selectedSite["siteNo"],"movement",self.currentSelected[1])
        for item in movement["data"]:
            print(item)
        displayedData=[movement["data"][1],movement["data"][dataIndex]]
        print("we are actually displaying index",dataIndex)
        print(displayedData)
        for index,block in enumerate(displayedData):
            vars = self.comparisonDataStructure[index]
            for i,row in enumerate(block):
                for j,item in enumerate(row[1:]):
                    vars[i][j+1].set(int(item))
                vars[i][0].set(row[0])
        self.update_summary_screen()

    def boxChanged(self,event):
        ###
        ### keep track of the combo box selections on the comparison display sheet
        ### box1Value tracks classed or unclassed
        ### box2Value tracks original or duplicate VRNs
        ###

        box = event.widget
        current = event.widget.current()
        text = box.get()
        if text in ["Unclassed" ,"Classed"]:
            if self.box1Value==current:
                return
            self.box1Value = current
        else:
            if self.box2Value == current:
                return
            self.box2Value = current
        print(self.box1Value,self.box2Value)
        self.update_comparison_display()

    def revert(self,event):
        ###
        ### the user can edit some of the data displayed on the comparison screen. They can also revert back to the
        ### original data. If the user reverts,we keep the edited data stored temporarily, which we can switch back
        ### in if requested. If the user reverts, and then edits the original data, the old edited data is discarded
        ### and the new edit becomes the stock edited data.
        ### self.displayStatus keeps track of which state we are in, "edited" or "base". "base" refers to displaying
        ### the base data

        print("disply status is",self.displayStatus)
        for site in self.dataList:
            for key, m in site["movements"].items():
                if self.currentSelected[1] == key:
                    print("selected site is", site["siteNo"])
                    selectedSite = site
        l = [movement for key, movement in sorted(selectedSite["movements"].items()) if key == self.currentSelected[1]]
        movement = l[0]
        print("selected movement is",movement)
        if self.displayStatus == "base":
            ### we are in reverted state, and user requested to go back to edited state
            self.displayStatus = "edited"
            event.widget.configure(text = "Revert")
            movement["data"][1] =self.tempEditedDataStore
            self.tempEditedDataStore= []
        else:
            self.displayStatus = "base"
            event.widget.configure(text="Load")
            self.tempEditedDataStore = list(movement["data"][1])
            movement["data"][1] = list(movement["data"][0])
        self.update_comparison_display()
        return "break"

    def validate_edit(self,action,text,char):
        #print("action is", action, type(action))
        print("char is",char,text)
        if action == "0":
            #print("yes")
            return True
        print("checking", char)
        return char.isdigit()

    def update_summary_screen(self):
        seen = set()
        ANPRClasses = [x for i, x in enumerate(self.currentJob["classification"].split(",")) if
                       i % 2 == 1 and x not in seen and not seen.add(x)]
        seen = set()
        OVClasses = [x for i, x in enumerate(self.currentJob["classification"].split(",")) if
                     i % 2 == 0 and x not in seen and not seen.add(x)]
        ANPRtoOVdict = {}  ### this will hold a dictionary of how we combine the OV classes into the ANPR classes
        for cl in ANPRClasses:
            # print("looing for ", cl)
            ANPRtoOVdict[cl] = []
            for item in [i for i, x in enumerate(self.currentJob["classification"].split(",")) if
                         x.lower() == cl.lower() and i % 2 == 1]:
                ANPRtoOVdict[cl].append(OVClasses.index(self.currentJob["classification"].split(",")[item - 1]))
        for site in self.dataList:
            #print("site is", site)
            l = [movement for key, movement in sorted(site["movements"].items())]
            for movement in l:
                movement["summary"] = {}
                movement["summary"]["OVTotal"] = 0
                movement["summary"]["ANPRTotal"] = 0
                movement["summary"]["AvgCapture"] = 0
                movement["summary"]["MinCapture"] = 1000
                movement["summary"]["MaxCapture"] = 0
                movement["summary"]["TimeLessThan"] = 0

                #print("site no", site["siteNo"], ",currently selected movement is", movement)


                OVdata = movement["data"][1]
                dataIndex = [(0,0),(1,0),(0,1),(1,1)].index((self.box1Value, self.box2Value)) + 2
                ANPRdata = movement["data"][dataIndex]

                for i, item in enumerate(OVdata):
                    #print("processing item", item)
                    if item[0] == "1 Hr":
                        movement["summary"]["OVTotal"] = movement["summary"]["OVTotal"] + int(item[-1])
                        #print("OVTotal is", movement["summary"]["OVTotal"])

                for row in ANPRdata:
                    if row[0] == "1 Hr":
                        movement["summary"]["ANPRTotal"] = movement["summary"]["ANPRTotal"] + row[-1]

                ###
                ### set up the comparison data for display
                ###

                compData = []
                for i, row in enumerate(OVdata):
                    compRowData = []
                    OVrow = row[1:]
                    ANPRrow = ANPRdata[i][1:]
                    timestamp = row[0]
                    for index, item in enumerate(ANPRrow[:-1]):
                        cl = ANPRClasses[index]
                        total = sum([OVrow[j] for j in ANPRtoOVdict[cl]])
                        if total == 0:
                            compRowData.append(0)
                        else:
                            compRowData.append(int(item * 100 / total))
                    if OVrow[-1] == 0:
                        compRowData.append(0)
                    else:
                        value = int(ANPRrow[-1] * 100 / OVrow[-1])
                        if timestamp != "1 Hr":
                            if value < movement["summary"]["MinCapture"]:
                                movement["summary"]["MinCapture"] = value
                            if value > movement["summary"]["MaxCapture"]:
                                movement["summary"]["MaxCapture"] = value
                            if value < 85:
                                movement["summary"]["TimeLessThan"] += 1
                        compRowData.append(value)
                    compRowData.insert(0, timestamp)
                    compData.append(compRowData)

                movement["summary"]["TimeLessThan"] = datetime.timedelta(
                    seconds=movement["summary"]["TimeLessThan"] * self.currentJob["interval"] * 60)
                if movement["summary"]["OVTotal"] != 0:
                    # print("ovtotal",site["summary"]["OVTotal"])
                    movement["summary"]["AvgCapture"] = int(
                        movement["summary"]["ANPRTotal"] * 100 / movement["summary"]["OVTotal"])
        if self.summaryTree is None:
            return
        if not self.summaryTree is None:
            for child in self.summaryTree.get_children():
                self.summaryTree.delete(child)
            self.summaryTree.tag_configure("tree", font="courier 10")
            #print("data list is", self.dataList)
            count = 0
            for site in self.dataList:
                #print("site is", site["siteNo"])
                keylist = [s for s in sorted(site["movements"])]
                #print("keylist is", keylist)
                for index, key in enumerate(keylist):
                    mvt = site["movements"][key]
                    item = []
                    item.append(key)
                    item.append(site["siteNo"])
                    summary = mvt["summary"]
                    item.append(summary["OVTotal"])
                    item.append(summary["ANPRTotal"])
                    item.append(str(summary["AvgCapture"]) + "%")
                    if summary["MinCapture"] ==1000:
                        item.append("0%")
                    else:
                        item.append(str(summary["MinCapture"]) + "%")
                    item.append(str(summary["MaxCapture"]) + "%")
                    item.append(summary["TimeLessThan"])
                    if self.currentJob["comments"][count] is None:
                        item.append("")
                    else:
                        item.append(self.currentJob["comments"][count])
                    count += 1
                    self.summaryTree.insert("", "end", values=item, tags=("tree",))
            for i in range(8):
                self.summaryTree.column(i, width=110, anchor=tkinter.CENTER, stretch=tkinter.NO)
            self.summaryTree.column(8, width=700, anchor=tkinter.CENTER, stretch=tkinter.NO)

    def calculate_display(self):

        ###
        ### this function re calculates the comparison display each time an entry box is edited and then
        ###  loses focus
        ###

        seen = set()
        ANPRClasses = [x for i, x in enumerate(self.currentJob["classification"].split(",")) if
                       i % 2 == 1 and x not in seen and not seen.add(x)]
        seen = set()
        OVClasses = [x for i, x in enumerate(self.currentJob["classification"].split(",")) if
                     i % 2 == 0 and x not in seen and not seen.add(x)]
        ANPRtoOVdict = {}  ### this will hold a dictionary of how we combine the OV classes into the ANPR classes
        for cl in ANPRClasses:
            # print("looing for ", cl)
            ANPRtoOVdict[cl] = []
            for item in [i for i, x in enumerate(self.currentJob["classification"].split(",")) if x.lower() == cl.lower() and i % 2 == 1]:
                ANPRtoOVdict[cl].append(OVClasses.index(self.currentJob["classification"].split(",")[item - 1]))

        rowList = []  ### holds the blocks of data that we want to sum by column


        for site in self.dataList:
            for key, m in site["movements"].items():
                if self.currentSelected[1] == key:
                    print("selected site is", site["siteNo"])
                    selectedSite = site
        l = [movement for key, movement in sorted(selectedSite["movements"].items()) if key == self.currentSelected[1]]
        movement = l[0]

        movement["summary"] = {}
        movement["summary"]["OVTotal"] = 0
        movement["summary"]["ANPRTotal"] = 0
        movement["summary"]["AvgCapture"] = 0
        movement["summary"]["MinCapture"] = 1000
        movement["summary"]["MaxCapture"] = 0
        movement["summary"]["TimeLessThan"] = 0

        #print("site no", site["siteNo"], ",currently selected movement is",movement)

        OVdata = list(movement["data"][1])
        dataIndex = [(0,0),(1,0),(0,1),(1,1)].index((self.box1Value,self.box2Value)) + 2
        ANPRdata = movement["data"][dataIndex]

        ###
        ### set up the OV data for display
        ###

        newList = []
        for i, item in enumerate(OVdata):
            #print("processing item", item)

            if item[0] == "1 Hr":
                rowList = [int(sum(r)) for r in zip(*rowList)]
                movement["summary"]["OVTotal"] = movement["summary"]["OVTotal"] + int(item[-1])
                rowList.insert(0, "1 Hr")
                newList.append(list(rowList))
                rowList = []
            else:
                item[-1] = (int(sum(item[1:-1])))
                rowList.append(list(item[1:]))
                newList.append(list(item))

        movement["data"][1] = list(newList)

        ###
        ### set up the ANPR data for display
        ###

        for row in ANPRdata:
            if row[0] == "1 Hr":
                movement["summary"]["ANPRTotal"] = movement["summary"]["ANPRTotal"] + row[-1]

        ###
        ### set up the comparison data for display
        ###

        compData = []
        for i, row in enumerate(OVdata):
            compRowData = []
            OVrow = row[1:]
            ANPRrow = ANPRdata[i][1:]
            timestamp = row[0]
            for index, item in enumerate(ANPRrow[:-1]):
                cl = ANPRClasses[index]
                total = int(sum([OVrow[j] for j in ANPRtoOVdict[cl]]))
                if total == 0:
                    compRowData.append(int(0))
                else:
                    compRowData.append(int(item * 100 / total))
            if OVrow[-1] == 0:
                compRowData.append(0)
            else:
                value = int(ANPRrow[-1] * 100 / OVrow[-1])
                if timestamp != "1 Hr":
                    if value < movement["summary"]["MinCapture"]:
                        movement["summary"]["MinCapture"] = value
                    if value > movement["summary"]["MaxCapture"]:
                        movement["summary"]["MaxCapture"] = value
                    if value < 85:
                        movement["summary"]["TimeLessThan"] += 1
                compRowData.append(value)
            compRowData = [str(item) + "%" for item in compRowData]
            compRowData.insert(0, timestamp)
            compData.append(compRowData)

        movement["summary"]["TimeLessThan"] = datetime.timedelta(
            seconds=movement["summary"]["TimeLessThan"] * self.currentJob["interval"] * 60)
        if movement["summary"]["OVTotal"] != 0:
            # print("ovtotal",site["summary"]["OVTotal"])
            movement["summary"]["AvgCapture"] = int(movement["summary"]["ANPRTotal"] * 100 / movement["summary"]["OVTotal"])

        vars = self.comparisonDataStructure[2]
        #print(vars)
        for i,row in enumerate(compData):
            #print("row is",row)
            v = vars[i]
            for j, item in enumerate(row):
                v[j].set(item)

        for label in self.colourLabels:
            val = label.cget("text")
            print("val is",val)
            if val =="":
                val = 0
            else:
                val = int(val.replace("%",""))
            label.configure(fg=get_colour(val))

    def movementChanged(self,event):


        if self.displayStatus == "base":
            ###
            ### if the user has reverted, then not edited anything, then changed movement, we need to
            ### deal with the reverted data, putting it back into the previously viewed movement
            ###
            for site in self.dataList:
                for key, m in site["movements"].items():
                    if self.currentSelected[1] == key:
                        print("selected site is", site["siteNo"])
                        selectedSite = site
            l = [movement for key, movement in sorted(selectedSite["movements"].items()) if key == self.currentSelected[1]]
            movement = l[0]
            movement["data"][1] = self.tempEditedDataStore
            self.tempEditedDataStore = []

        mvmnt = int(event.widget.get().replace("Movement", ""))
        for site in self.dataList:
            for key, m in site["movements"].items():
                if mvmnt == key:
                    print("selected site is", site["siteNo"])
                    selectedSite = site
        self.siteLabel.configure(text="Site " + str(selectedSite["siteNo"]))
        self.currentSelected[0] = selectedSite["siteNo"]
        self.currentSelected[1] = mvmnt
        self.displayStatus = "edited"
        self.revertButton.configure(text="Revert")

        self.update_comparison_display()
        self.update()
        self.update_idletasks()

    def load_job(self,event):
        jobname = self.tree.item(self.tree.selection()[0])
        self.currentJob = myDB.load_job(jobname["values"][0],jobname["values"][1],jobname["values"][2])
        title = self.currentJob["jobno"] + " " + self.currentJob["jobname"]
        self.wm_title(title)
        if not self.loadJobFunction(self.currentJob):
            return
        self.spawn_home_window()

    def delete_job(self):
        if self.tree.selection() == "":
            return
        jobname = self.tree.item(self.tree.selection()[0])
        result = messagebox.askyesno(message="Are you sure you want to delete this project?")
        if not result:
            return
        myDB.delete_job(jobname["values"][0], jobname["values"][1], jobname["values"][2])
        self.spawn_survey_setup_screen()

    def export_OVTemplate(self):
        wb = openpyxl.load_workbook("OV template.xlsm", keep_vba=True)
        try:
            sheet = wb.get_sheet_by_name("Temp")
        except Exception as e:
            messagebox.showinfo(message="Trying to export to excel, sheet Temp doesnt exist in the template file,cannot export")
            return
        classes = self.currentJob["classification"].split(",")
        classes = [x for i,x in enumerate(classes) if i % 2 == 0]
        for i,c in enumerate(classes):
            sheet.cell(row = 1 + i,column=1).value = c
        times = self.currentJob["timeperiod1"].split("-") + self.currentJob["timeperiod2"].split("-") + self.currentJob["timeperiod3"].split("-") + self.currentJob["timeperiod4"].split("-")
        print("times are ",times)
        for i,t in enumerate(times):
            sheet.cell(row=1 + i, column=2).value = t
        sheet.cell(row=1,column=3).value = self.currentJob["interval"]
        col = 4
        for k,v in self.currentJob["sites"].items():
            row = 1
            sheet.cell(row=row,column=col).value = int(k)
            for key,value in v.items():
                row+=1
                sheet.cell(row=row, column=col).value = int(key)
            col+=1
        file = self.currentJob["folder"] + "/" + self.currentJob["jobno"] +  " " + self.currentJob["jobname"] + " - OV Template " + self.currentJob["surveydate"].strftime("%d-%m-%y") +  ".xlsm"
        wb.save(file)
        xl = win32com.client.Dispatch("Excel.Application")
        xl.Workbooks.Open(Filename=file, ReadOnly=1)
        xl.Application.Run("create_template")
        xl.Workbooks(1).Close(SaveChanges=1)
        xl.Application.Quit()
        myDB.update_job_with_progress(self.currentJob["id"], "OVTemplate")

    def load_unclassed_plates(self):
        self.loadUnclassedFunction(self.currentJob)

    def get_comparison_data(self):
        self.dataList = self.getComparisonFunction(self.currentJob)
        if not self.dataList is None:
            self.set_up_comparison_display()

    def load_OV_counts(self):
        self.loadOVCountsFunction(self.currentJob)
        myDB.update_job_with_progress(self.currentJob["id"], "OVCounts")

    def load_classes(self):
        self.loadClassedFunction(self.currentJob)

    def setCallbackFunction(self, text, fun):
        if text == "load unclassed":
            self.loadUnclassedFunction = fun
        if text == "load classed":
            self.loadClassedFunction = fun
        if text == "load job":
            self.loadJobFunction = fun
        if text == "load overview count":
            self.loadOVCountsFunction = fun
        if text == "get unclassed comparison":
            self.getComparisonFunction = fun
        if text == "reprocess data":
            self.reprocessDataFunction = fun
        if text == "set duplicates":
            self.setDuplicatesFunction = fun
        if text == "get cordon in out only data":
            self.getCordonFunction = fun
        if text == "get cordon non directional data":
            self.getNonDirectionalCordonFunction = fun
        if text == "get fs-ls directional data":
            self.getRouteAssignmentFsLsFunction = fun
        if text == "get fs-ls non directional data":
            self.getRouteAssignmentFsLsNonDirectionalFunction = fun





def get_colour(value):
    if isinstance(value,str):
        return "black"
    value = int(value)
    if value == 0:
        return "black"
    if value > 100:
        return "blue"
    if value < 85:
        return  "red"
    return "black"

class VerticalScrolledFrame(tkinter.Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling

    """
    def __init__(self, parent, *args, **kw):
        tkinter.Frame.__init__(self, parent, *args, **kw)
        #print("width of scroll",parent.winfo_width())
        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = tkinter.Scrollbar(self, orient=tkinter.VERTICAL,bg="white")
        vscrollbar.pack(fill=tkinter.Y, side=tkinter.RIGHT, expand=tkinter.TRUE)
        self.canvas = tkinter.Canvas(self, bd=0, highlightthickness=0,bg="white",
                        yscrollcommand=vscrollbar.set,height = 800)
        self.canvas.bind_all("<MouseWheel>",self.on_mousewheel)
        self.canvas.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.TRUE)
        vscrollbar.config(command=self.canvas.yview)

        # reset the view
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = tkinter.Frame(self.canvas,bg="white",width = 100)
        interior_id = self.canvas.create_window(0, 0, window=interior,
                                           anchor=tkinter.NW)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            #print("required size is",size)
            #print("actual size is",canvas.winfo_width(),canvas.winfo_height())
            self.canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != self.canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                self.canvas.config(width=interior.winfo_reqwidth())
            #if interior.winfo_reqheight() != canvas.winfo_height():
                # update the canvas's height to fit the inner frame
                #canvas.config(height=interior.winfo_reqheight())
            #print("actual size is", canvas.winfo_width(), canvas.winfo_height())
        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != self.canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                self.canvas.itemconfigure(interior_id, width=self.canvas.winfo_width())
                self.canvas.bind('<Configure>', _configure_canvas)

    def on_mousewheel(self,event):
        self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")

