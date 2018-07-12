import tkinter
import tktable
import tkinter.font as font

import tkinter.ttk as ttk
from tkinter import messagebox
import datetime
import openpyxl
import win32com.client
from PIL import Image,ImageDraw,ImageTk,JpegImagePlugin,Jpeg2KImagePlugin
from tkinter import filedialog
import threading
import os
import myDB
import pickle
import subprocess
import time
import re
import csv
import matrix
import copy
import pandas as pd
import ANPRproject

class VerticalScrolledFrame(tkinter.Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling

    """
    def __init__(self, parent, *args, **kw):
        tkinter.Frame.__init__(self, parent, *args, **kw)
        print("height of scroll",parent.winfo_height())
        parentOfparent = self.nametowidget(parent.winfo_parent())
        #parentOfparent.configure(bg="black")
        print("parent of parent height is",parentOfparent.winfo_height())
        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = tkinter.Scrollbar(self, orient=tkinter.VERTICAL,bg="white")
        vscrollbar.pack(fill=tkinter.Y, side=tkinter.RIGHT, expand=tkinter.TRUE)
        self.canvas = tkinter.Canvas(self, bd=0, highlightthickness=0,bg="white",
                        yscrollcommand=vscrollbar.set,height = 800-64)
        self.canvas.bind_all("<MouseWheel>",self.on_mousewheel)
        self.canvas.bind("<Enter>",self.on_entry)
        self.canvas.bind("<Leave>", self.on_exit)
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
            #if interior.winfo_reqheight() != self.canvas.winfo_height():
                # update the canvas's height to fit the inner frame
                #self.canvas.config(height=interior.winfo_reqheight())
            #print("actual size is", canvas.winfo_width(), canvas.winfo_height())
        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != self.canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                self.canvas.itemconfigure(interior_id, width=self.canvas.winfo_width())
                self.canvas.bind('<Configure>', _configure_canvas)

    def on_exit(self,event):
        print("left canvas")
        self.canvas.unbind_all("<MouseWheel>")

    def on_entry(self,event):
        print("entered canvas")
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)

    def on_mousewheel(self,event):
        print("psdf")
        self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")





class mainWindow(tkinter.Tk):

    def __init__(self):
        super(mainWindow, self).__init__()
        self.projectId = None
        self.colourLabels = []
        self.entryValues = []
        self.last_focus = None
        self.data = None
        self.numCameras = None
        self.revertButton = None
        self.tracsisBlue = "#%02x%02x%02x" % (20, 27, 77)
        self.tracsisGrey = "#%02x%02x%02x" % (99, 102, 106)
        self.configure(bg="white")
        ttk.Style().configure(".", bg="white",fg="red")
        style = ttk.Style(self)
        style.configure('Treeview', rowheight=40)  # SOLUTION
        self.state('zoomed')
        self.menubar = tkinter.Menu(self)
        menu = tkinter.Menu(self.menubar, tearoff=0)
        menu.add_command(label="Set Database File", command=self.set_database_file)
        self.menubar.add_cascade(label="Settings", menu=menu)
        self.config(menu=self.menubar)
        self.load_settings()
        if myDB.get_db_file() is None:
            self.set_database_file()
        else:
            self.spawn_main_screen()



    def display_project_list(self):
        projects = myDB.get_project_list()
        for index,project in enumerate(projects):
            id = project[0]
            project = ["Delete","Edit","Match","OV Template"] + list(project[1:])
            self.table.insert_row(project,iid=str(id))
            #if index % 2 == 0:
                #self.tree.insert("", "end", values=project, tags=("tree", "even"))
            #else:
                #self.tree.insert("", "end", values=project, tags=("tree", "odd"))


##############################################################################################
#
#
# spawn the various screens
#
#
###############################################################################################



    def spawn_main_screen(self):
        ###
        ### The screen that displays a list of current projects
        ### and allows you to add, edit or delete projects
        ###

        self.entryValues = []
        for child in self.winfo_children()[1:]:
            child.destroy()
        self.wm_title("Project Setup")
        f = tkinter.font.Font(family='Helvetica', size=16, weight=tkinter.font.BOLD)
        frame = tkinter.Frame(self, bg="white")
        frame.pack()#grid(row=0, column=0)
        self.logo = ImageTk.PhotoImage(Image.open("Tracsisplcnewlogo.png").resize((200, 66), Image.ANTIALIAS))
        self.plus = ImageTk.PhotoImage(Image.open("green-plus.png").resize((25, 25), Image.ANTIALIAS))
        label = tkinter.Label(frame,image=self.logo, bg="white")
        label.grid(row=0,column=0,padx=20)
        label = tkinter.Label(frame, text= "MatchPro v2.0", bg="white",font=f)
        label.grid(row=0, column=1,padx=20)

        ###
        ### set up the treeview
        ###
        frame = tkinter.Frame(self, bg="white")
        frame.pack(side = tkinter.TOP)  # grid(row=0, column=0)
        cols = ("Delete", "Edit", "Match","OV Template", "Project Name", "Project No", "Project Date")
        f = tkinter.font.Font(family="times new roman", size=12)
        self.table = tktable.Tk_Table(frame, columns=cols,cell_anchor="center",cell_font=f,row_numbers=False,height=40,stripped_rows=("white", "#f2f2f2"))
        self.table.pack(side=tkinter.LEFT)
        tkinter.Button(frame, image=self.plus, bg="white",command=self.spawn_edit_screen).pack(side=tkinter.LEFT,anchor="n")
        self.table.set_callback(self.table_clicked)
        self.display_project_list()


    def spawn_edit_screen(self):
        for child in self.winfo_children()[2:]:
            child.destroy()
        f = tkinter.font.Font(family="times new roman", size=12)
        headerFont = tkinter.font.Font(family="times new roman", size=20,weight=tkinter.font.BOLD)
        outerFrame = tkinter.Frame(self,bg="white")
        outerFrame.pack()
        frame = tkinter.Frame(outerFrame, width=330, height=150, bg="white", relief=tkinter.GROOVE, borderwidth=2)
        frame.grid(row=0,column=0,sticky="n")
        tkinter.Label(frame,text = "Project Details",bg=self.tracsisBlue,fg="white",font=headerFont).grid(row=0,column=0,columnspan=3,sticky="nsew")
        tkinter.Label(frame, text="Job No", bg="light grey",relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=1, column=0, sticky="nsew")
        tkinter.Label(frame, text="Job Name", bg="light grey",relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=2, column=0, sticky="nsew")
        tkinter.Label(frame, text="Date", bg="light grey",relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=3, column=0, sticky="nsew")
        tkinter.Label(frame, text="Num Cameras", bg="light grey",relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=4, column=0, sticky="nsew")
        tkinter.Label(frame, text="Interval", bg="light grey",relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=5, column=0, sticky="nsew")
        tkinter.Label(frame, text="Start Date", bg="light grey",relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=6, column=0, sticky="nsew")
        tkinter.Label(frame, text="End Date", bg="light grey",relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=7, column=0, sticky="nsew")
        tkinter.Label(frame, text="From", bg="light grey",relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=8, column=0, sticky="nsew")
        tkinter.Label(frame, text="To", bg="light grey",relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=9, column=0, sticky="nsew")
        tkinter.Label(frame, text="Split", bg="light grey",relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=10, column=0, sticky="nsew")
        tkinter.Label(frame, text="Start Date", bg="light grey",relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=11, column=0, sticky="nsew")
        tkinter.Label(frame, text="End Date", bg="light grey",relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=12, column=0, sticky="nsew")
        tkinter.Label(frame, text="From", bg="light grey",relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=13, column=0, sticky="nsew")
        tkinter.Label(frame, text="To", bg="light grey",relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=14, column=0, sticky="nsew")
        tkinter.Label(frame, text="Split", bg="light grey",relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=15, column=0, sticky="nsew")
        tkinter.Label(frame, text="Start Date", bg="light grey",relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=16, column=0, sticky="nsew")
        tkinter.Label(frame, text="End Date", bg="light grey",relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=17, column=0, sticky="nsew")
        tkinter.Label(frame, text="From", bg="light grey",relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=18, column=0, sticky="nsew")
        tkinter.Label(frame, text="To", bg="light grey",relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=19, column=0, sticky="nsew")
        tkinter.Label(frame, text="Split", bg="light grey",relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=20, column=0, sticky="nsew")

        tkinter.Label(frame, text="Classes", bg="light grey",relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=21, column=0, sticky="nsew")
        tkinter.Entry(frame, width=20,  bg="white").grid(row=1, column=1, pady=2,padx=10)
        tkinter.Entry(frame, width=20, bg="white").grid(row=2, column=1, pady=2, padx=10,sticky="w")
        e = tkinter.Entry(frame, width=20, bg="white")
        e.grid(row=3, column=1, pady=2, padx=10,sticky="w")
        e.bind("<FocusOut>", self.date_focus_out)
        e = tkinter.Entry(frame, width=20, bg="white")
        e.grid(row=4, column=1, pady=2, padx=10, sticky="w")
        e.bind("<FocusOut>", self.change_num_cameras)
        box = ttk.Combobox(frame, width=17)
        box["values"] = ("5", "15", "30", "60")
        box.grid(row=5, column=1, pady=2, padx=10, sticky="w")

        e = tkinter.Entry(frame, width=20, bg="white")
        e.grid(row=6, column=1, pady=2, padx=10, sticky="w")
        e.bind("<FocusOut>", self.date_focus_out)#
        e = tkinter.Entry(frame, width=20, bg="white")
        e.grid(row=7, column=1, pady=2, padx=10, sticky="w")
        e.bind("<FocusOut>", self.date_focus_out)
        e = tkinter.Entry(frame, width=20, bg="white")
        e.grid(row=8, column=1, pady=2, padx=10, sticky="w")
        e.bind("<FocusOut>", self.time_focus_out)  #
        e = tkinter.Entry(frame, width=20, bg="white")
        e.grid(row=9, column=1, pady=2, padx=10, sticky="w")
        e.bind("<FocusOut>", self.time_focus_out)
        var = tkinter.IntVar()
        c = tkinter.Checkbutton(frame, text="", bg="white", variable=var)
        c.grid(row=10, column=1)
        c.var = var

        e = tkinter.Entry(frame, width=20, bg="white")
        e.grid(row=11, column=1, pady=2, padx=10, sticky="w")
        e.bind("<FocusOut>", self.date_focus_out)  #
        e = tkinter.Entry(frame, width=20, bg="white")
        e.grid(row=12, column=1, pady=2, padx=10, sticky="w")
        e.bind("<FocusOut>", self.date_focus_out)
        e = tkinter.Entry(frame, width=20, bg="white")
        e.grid(row=13, column=1, pady=2, padx=10, sticky="w")
        e.bind("<FocusOut>", self.time_focus_out)  #
        e = tkinter.Entry(frame, width=20, bg="white")
        e.grid(row=14, column=1, pady=2, padx=10, sticky="w")
        e.bind("<FocusOut>", self.time_focus_out)
        var = tkinter.IntVar()
        c = tkinter.Checkbutton(frame, text="", bg="white", variable=var)
        c.grid(row=15, column=1)
        c.var = var

        e = tkinter.Entry(frame, width=20, bg="white")
        e.grid(row=16, column=1, pady=2, padx=10, sticky="w")
        e.bind("<FocusOut>", self.date_focus_out)  #
        e = tkinter.Entry(frame, width=20, bg="white")
        e.grid(row=17, column=1, pady=2, padx=10, sticky="w")
        e.bind("<FocusOut>", self.date_focus_out)
        e = tkinter.Entry(frame, width=20, bg="white")
        e.grid(row=18, column=1, pady=2, padx=10, sticky="w")
        e.bind("<FocusOut>", self.time_focus_out)  #
        e = tkinter.Entry(frame, width=20, bg="white")
        e.grid(row=19, column=1, pady=2, padx=10, sticky="w")
        e.bind("<FocusOut>", self.time_focus_out)
        var = tkinter.IntVar()
        c = tkinter.Checkbutton(frame, text="", bg="white", variable=var)
        c.grid(row=20, column=1)
        c.var = var

        tkinter.Entry(frame, width=20, bg="white").grid(row=21, column=1, pady=2, padx=10, sticky="w")
        frame = tkinter.Frame(frame, width=330, height=150, bg="white", relief=tkinter.GROOVE, borderwidth=2)
        frame.grid(row=22, column=0,columnspan=2,sticky="n")
        tkinter.Button(frame,text="BACK",command=self.spawn_main_screen).grid(row=0,column=0,sticky="nsew")
        tkinter.Button(frame, text="SAVE",command=self.save_project).grid(row=0, column=1, sticky="nsew")
        tkinter.Button(frame, text="IMPORT").grid(row=0, column=2, sticky="nsew")
        tkinter.Button(frame, text="LOAD PLATES",command=self.add_plates_file).grid(row=1, column=0, columnspan=3,sticky="nsew")
        tkinter.Button(frame, text="CHANGE FOLDER",command=self.change_project_folder).grid(row=2, column=0, columnspan=3,sticky="nsew")
        #tkinter.Button(frame, text="MATCH",command=lambda p = self.project:self.spawn_matching_results_screen(p)).grid(row=2, column=0, columnspan=3,sticky="nsew")
        frame =  tkinter.Frame(outerFrame, width=330, height=800, bg="white", relief=tkinter.GROOVE, borderwidth=2)
        frame.grid(row=0, column=1,rowspan=2,sticky="n")
        self.set_up_movements_frame(0)


    def spawn_duration_matrix_screen(self,project):
        win =tkinter.Toplevel()
        win.state("zoomed")
        width = win.winfo_screenwidth() - 120
        height = win.winfo_screenheight() - 200
        frame=tkinter.Frame(win)
        frame.grid(row=0, column=0, columnspan=3)
        tkinter.Label(frame,text = "Base duration").grid(row=0,column=0)
        e =tkinter.Entry(frame)
        e.grid(row=0,column=1)
        tkinter.Button(frame, text="Fill", command=lambda: self.fill_duration_matrix(e)).grid(row=0, column=2)
        frame = tkinter.Frame(win, bg="white", relief=tkinter.GROOVE, borderwidth=3, width=800, height=800)
        frame.grid(row = 1,column=0,columnspan = 3,padx=10,pady=10)
        self.durationMatrix = matrix.MatrixDisplay(frame, width, height,project,clickable=True)


    def spawn_matching_results_screen(self,project):
        print("project is",project)
        if project is None:
            return
        self.project = project

        for child in self.winfo_children()[2:]:
            if type(self.nametowidget(child)) != tkinter.Toplevel:
                child.destroy()
        if self.winfo_screenheight() >900:
            width = 1000
            height = 800
        else:
            width = self.winfo_screenwidth() - 300
            height = self.winfo_screenheight() - 200
        print("set width and height to ",width,height)
        f = tkinter.font.Font(size=12)
        #tkinter.Label(self, bg="white", text=matchingType + " Matching", font=f, fg=self.tracsisBlue).grid(row=0,column=0,columnspan=3,pady = 20)

        outerFrame = tkinter.Frame(self,bg="white",height = height, relief=tkinter.GROOVE, borderwidth=3)
        outerFrame.pack(anchor="w",fill=tkinter.X)

        controlPanel = tkinter.Frame(outerFrame,bg="white")
        controlPanel.grid(row=0, column=0, sticky="ns")
        e = tkinter.Entry(controlPanel,width=20,bg="white")
        e.grid(row=0,column= 0,sticky="nsew")
        e.bind("<Return>",self.add_filter)
        lb = tkinter.Listbox(controlPanel,bg="light grey",height=5)
        lb.grid(row=1,column=0,sticky="ew")
        lb.bind("<Double-Button-1>", self.remove_filter)
        tkinter.Button(controlPanel, text="Clear",command=lambda: self.button_clicked(0),height=2).grid(row=2, column=0, sticky="nsew")
        tkinter.Button(controlPanel,text = "Run",command=lambda: self.button_clicked(1),height=2).grid(row=3,column=0,sticky="nsew")
        tkinter.Button(controlPanel, text="Non-Dir",command=lambda: self.button_clicked(2),height=2).grid(row=4, column=0, sticky="nsew")
        tkinter.Button(controlPanel, text="Pairs",command=lambda: self.button_clicked(3),height=2).grid(row=5, column=0, sticky="nsew")
        tkinter.Button(controlPanel, text="Fs-Ls",command=lambda: self.button_clicked(4),height=2).grid(row=6, column=0, sticky="nsew")
        tkinter.Button(controlPanel, text="Full \n Journeys",command=lambda: self.button_clicked(5),height=2).grid(row=7, column=0, sticky="nsew")

        tkinter.Label(controlPanel,text = "Durations",bg=self.tracsisBlue,fg="white").grid(row=8,column=0,sticky="nsew",pady=(10,0))
        var = tkinter.IntVar()
        var.trace("w", self.duration_checkbox_clicked)
        c = tkinter.Checkbutton(controlPanel,text = "Duration Check",variable = var)
        c.var = var
        c.grid(row=9,column = 0, sticky="nsew")

        var = tkinter.IntVar()
        tkinter.Radiobutton(controlPanel,text = "Split",state="disabled",value = 0,variable = var).grid(row=10,column=0,sticky="nsew")
        tkinter.Radiobutton(controlPanel, text="Discard",state="disabled",value = 1,variable = var).grid(row=11, column=0,sticky="nsew")
        c.radioVar = var

        var = tkinter.IntVar()
        var.trace("w", self.max_checkbox_clicked)
        c = tkinter.Checkbutton(controlPanel, text="Max", variable=var)
        c.var = var
        c.grid(row=12, column=0, sticky="nsew")
        tkinter.Entry(controlPanel,width=4).grid(row=13,column=0,sticky="nsew")
        var = tkinter.IntVar()
        tkinter.Radiobutton(controlPanel, text="Split", state="disabled",value = 0,variable = var).grid(row=14, column=0, sticky="nsew")
        tkinter.Radiobutton(controlPanel, text="Discard", state="disabled",value = 1,variable = var).grid(row=15, column=0, sticky="nsew")
        c.radioVar = var


        tkinter.Label(controlPanel,text = "Output to Excel",bg=self.tracsisBlue,fg="white").grid(row=16,column=0,sticky="nsew",pady=(10,0))
        var = tkinter.IntVar()
        c = tkinter.Checkbutton(controlPanel, text="Days to separate sheets", variable=var)
        c.var = var
        c.var.set(1)
        c.grid(row=17, column=0, sticky="nsew")
        tkinter.Button(controlPanel, text="Output",command=lambda: self.button_clicked(6),height=2).grid(row=18, column=0, sticky="nsew",pady=(0,10))
        tkinter.Button(controlPanel, text="Open \n Folder",command=lambda: self.button_clicked(7),height=2).grid(row=19, column=0, sticky="nsew")
        tkinter.Button(controlPanel, text="Edit \n Project",command=lambda: self.button_clicked(8),height=2).grid(row=20, column=0, sticky="nsew")
        tkinter.Button(controlPanel, text="Back",command=self.spawn_main_screen,height=2).grid(row=21, column=0, sticky="nsew")

        dataPanel = tkinter.Frame(outerFrame, bg="white")
        dataPanel.grid(row=0, column=1, sticky="ns",padx=20)
        tkinter.Label(dataPanel, text="Movement", bg="grey95",relief=tkinter.GROOVE,borderwidth=2,font=f).grid(row=0, column=0,sticky="nsew")
        tkinter.Label(dataPanel, text="Type", bg="grey95",relief=tkinter.GROOVE,borderwidth=2,font=f).grid(row=1, column=0,sticky="nsew")
        tkinter.Label(dataPanel, text="Plates", bg="grey95",relief=tkinter.GROOVE,borderwidth=2,font=f).grid(row=2, column=0,sticky="nsew")
        tkinter.Label(dataPanel, text="Edge Matches", bg="grey95",relief=tkinter.GROOVE,borderwidth=2,font=f).grid(row=3, column=0,sticky="nsew")
        tkinter.Label(dataPanel, text="Matched %", bg="grey95",relief=tkinter.GROOVE,borderwidth=2,font=f).grid(row=4, column=0,sticky="nsew")
        tkinter.Label(dataPanel, text="Full Matches", bg="grey95",relief=tkinter.GROOVE,borderwidth=2,font=f).grid(row=5, column=0,sticky="nsew")
        tkinter.Label(dataPanel, text="Matched %", bg="grey95",relief=tkinter.GROOVE,borderwidth=2,font=f).grid(row=6, column=0,sticky="nsew")

        box = ttk.Combobox(dataPanel, width=10)
        box["values"] = ("Count", "Max", "Min", "Avg")
        box.bind("<<ComboboxSelected>>", self.display_option_changed)
        box.grid(row=7, column=0,columnspan=2,sticky="nsew")
        box.current(0)

        tkinter.Label(dataPanel, text="", bg="white",relief=tkinter.GROOVE,borderwidth=2,font=f,width=7).grid(row=0, column=1,sticky="nsew")
        tkinter.Label(dataPanel, text="", bg="white",relief=tkinter.GROOVE,borderwidth=2,font=f,width=7).grid(row=1, column=1,sticky="nsew")
        tkinter.Label(dataPanel, text="0", bg="white",relief=tkinter.GROOVE,borderwidth=2,font=f,width=7).grid(row=2, column=1,sticky="nsew")
        tkinter.Label(dataPanel, text="0%", bg="white",relief=tkinter.GROOVE,borderwidth=2,font=f,width=7).grid(row=3, column=1,sticky="nsew")
        tkinter.Label(dataPanel, text="0%", bg="white",relief=tkinter.GROOVE,borderwidth=2,font=f,width=7).grid(row=4, column=1,sticky="nsew")
        tkinter.Label(dataPanel, text="0", bg="white",relief=tkinter.GROOVE,borderwidth=2,font=f,width=7).grid(row=5, column=1,sticky="nsew")
        tkinter.Label(dataPanel, text="0%", bg="white",relief=tkinter.GROOVE,borderwidth=2,font=f,width=7).grid(row=6, column=1,sticky="nsew")

        frame = tkinter.Frame(outerFrame,bg="white")
        frame.grid(row=0,column=2,sticky="n")
        nb = ttk.Notebook(frame)
        nb.grid(row=0,column=0)

        matrixFrame = tkinter.Frame(frame, relief=tkinter.GROOVE, borderwidth=3, bg="white", width=width, height=height)
        self.matrix = matrix.MatrixDisplay(matrixFrame, width, height,project,clickable=False)
        self.matrix.set_matrix_clicked_callback_function(self.display_movement_data)
        nb.add(matrixFrame,text="Matches")

        frame = tkinter.Frame(outerFrame, bg="white")
        frame.grid(row=0, column=2, sticky="n")
        topframe = tkinter.Frame(frame, bg="white")
        topframe.grid(row=0, column=0, sticky="n")

        tkinter.Label(topframe, text="Base duration", bg="white").grid(row=0, column=0)
        e = tkinter.Entry(topframe)
        e.grid(row=0, column=1,sticky="w")
        tkinter.Button(topframe, text="Fill", command=lambda: self.fill_duration_matrix(e)).grid(row=0, column=2,sticky="w")

        matrixFrame = tkinter.Frame(frame, relief=tkinter.GROOVE, borderwidth=3, bg="white", width=width, height=height)
        matrixFrame.grid(row=1,column=0,columnspan=3)

        self.durationMatrix = matrix.MatrixDisplay(matrixFrame, width, height, project,mainCanvasClickable=True)
        nb.add(frame, text="Durations")
        self.durationMatrix.draw(data=self.project.get_durations())
        #nb.bind("<<NotebookTabChanged>>",self.tab_changed)






##############################################################################################
#
#
# do other stuff
#
#
###############################################################################################

    def load_settings(self):
        try:
            f = open("settings.txt", "r")
        except FileNotFoundError as e:
            f = open("settings.txt", "w")
            f.close()
            f = open("settings.txt", "r")
        try:
            file = f.readline().rstrip()

        except Exception as e:
            print(e)
            return None
        if file == "":
            file = None
        print("db file is",file)
        myDB.set_file(file)


    def save_settings(self):
        file = myDB.get_db_file()
        if (file == "") | (file is None):
            #messagebox.showinfo(message="No Database Selected")
            return
        if ".sqlite" not in file:
            #messagebox.showinfo(message="The selected database file must be a .sqlite file")
            return
        dir = os.getcwd()
        print("dir is",dir)
        f = open("settings.txt","w")
        f.write(file +  "\n")
        myDB.set_file(file)


    def set_database_file(self):
        ###
        ### prompt the user with a file navigation dialog, to select the location of the job database
        ### display the selected location in a label in the settings window
        ###

        file = filedialog.askopenfilename()
        if file == "" or ".sqlite" not in file:
            messagebox.showinfo(message="No File Selected")
            return

        myDB.set_file(file)
        self.save_settings()
        self.spawn_main_screen()


    def change_project_folder(self):
        if self.projectId is None:
            messagebox.showinfo(message = "Please select project folder after you have saved the project")
            return
        file = filedialog.askdirectory()
        if file == "" or file is None:
            messagebox.showinfo(message = "No folder selected, change not saved")
            return
        myDB.change_project_folder(self.projectId,file)
        messagebox.showinfo(message="Project Folder Changed")


    def remove_filter(self,event):
        lb = event.widget
        if len(lb.curselection())==0:
            return
        lb.delete(lb.curselection()[0])


    def fill_duration_matrix(self,e):
        text = e.get()
        print("in fill matrix, text is",text)
        if text.strip() == "":
            return
        if self.validate_time(text):
            e.delete(0, tkinter.END)
            if os.path.exists(os.path.join(self.project.folder,"data", "durations.pkl")):
                os.remove(os.path.join(self.project.folder,"data", "durations.pkl"))
            self.project.load_durations(text)
            self.durationMatrix.draw(data=self.project.get_durations())
        else:
            #messagebox.showinfo(message=e.get() + " is not a valid time")
            e.delete(0, tkinter.END)


    def display_movement_data(self,mov):
        #print("looking for movement",mov)
        if self.data is None:
            return
        if mov == "Total":
            return
        frame = self.winfo_children()[2].winfo_children()[1]
        frame.winfo_children()[8].config(text=str(mov))
        frame.winfo_children()[9].config(text=str(self.project.get_direction(mov)))
        frame.winfo_children()[10].config(text=str(self.data[2][mov]))
        frame.winfo_children()[11].config(text=str(self.data[1][mov]))
        if self.data[2][mov] != 0:
            frame.winfo_children()[12].config(text=str(round(self.data[1][mov]*100/self.data[2][mov],2)) + "%")
        else:
            frame.winfo_children()[12].config(text=str(0))
        frame.winfo_children()[13].config(text=str(self.data[3][mov]))
        if self.data[2][mov] != 0:
            frame.winfo_children()[14].config(text=str(round(self.data[3][mov] * 100 / self.data[2][mov], 2)) + "%")
        else:
            frame.winfo_children()[14].config(text=str(0))


    def tab_changed(self,event):
        nb = event.widget.select()
        nb=self.nametowidget(nb)
        print("type of nb is",type(nb))
        matrix = nb.winfo_children()[0]
        print("type of matrix is",type(matrix))


    def duration_checkbox_clicked(self,*args):
        frame = self.winfo_children()[2].winfo_children()[0]
        print("CLICKED!!!!", frame.winfo_children()[9].var.get(),args)
        if frame.winfo_children()[9].var.get():
            frame.winfo_children()[10].config(state=tkinter.NORMAL)
            frame.winfo_children()[11].config(state= tkinter.NORMAL)
            frame.winfo_children()[12].var.set(0)
        else:
            frame.winfo_children()[10].config(state= tkinter.DISABLED)
            frame.winfo_children()[11].config(state= tkinter.DISABLED)


    def max_checkbox_clicked(self,*args):
        frame = self.winfo_children()[2].winfo_children()[0]
        print("CLICKED!!!!", frame.winfo_children()[9].var.get(),args)
        if frame.winfo_children()[12].var.get():
            frame.winfo_children()[14].config(state=tkinter.NORMAL)
            frame.winfo_children()[15].config(state= tkinter.NORMAL)
            frame.winfo_children()[9].var.set(0)
        else:
            frame.winfo_children()[14].config(state= tkinter.DISABLED)
            frame.winfo_children()[15].config(state= tkinter.DISABLED)


    def add_filter(self,event):
        text = event.widget.get()
        lb = self.winfo_children()[2].winfo_children()[0].winfo_children()[1]
        if text == "":
            return
        try:
            i = lb.get(0, tkinter.END).index(text)
            ###its already in the list, we dont want to add it again
        except Exception as e:
            ### its not in the list, so we add it to the end
            if validate_filter(text):
                lb.insert(tkinter.END, text)
        event.widget.delete(0, tkinter.END)


    def add_plates_file(self):
        if self.projectId is None:
            messagebox.showinfo(message = "Please add the plates file after you have saved the project")
            return
        file = filedialog.askopenfilename()
        if file == "":
            messagebox.showinfo(message="No file selected, no plates loaded")
            return
        myDB.set_uploaded_file(self.projectId,file)
        proj = ANPRproject.ANPRproject()
        proj.load_project(self.projectId)
        proj.clear_data_folder()
        messagebox.showinfo(message="Successfully added plates file")


    def display_option_changed(self,event):
        selectedDisplay = event.widget.current()
        if not self.data is None:
            if selectedDisplay> 0:
                self.matrix.draw(self.data[0], index=selectedDisplay,fontsize=7,totals=True)
            else:
                self.matrix.draw(self.data[0],index=selectedDisplay,totals=True)
        pass


    def button_clicked(self,index):
        frame = self.winfo_children()[2].winfo_children()[0]
        lb = self.winfo_children()[2].winfo_children()[0].winfo_children()[1]
        durationCheck = None
        durationBehaviour = None
        if frame.winfo_children()[9].var.get():
            durationCheck = "duration"
            durationBehaviour = ["split", "discard"][frame.winfo_children()[9].radioVar.get()]
        if frame.winfo_children()[12].var.get():
            durationCheck = "max"
            durationBehaviour = ["split", "discard"][frame.winfo_children()[12].radioVar.get()]
        maxVal = frame.winfo_children()[13].get()
        print(durationCheck,durationBehaviour,maxVal)
        selectedDisplay = self.winfo_children()[2].winfo_children()[1].winfo_children()[7].current()
        print("selectedDsiplay is",selectedDisplay)
        timeType = 2#frame.winfo_children()[17].var.get()
        daysInSeparateSheets = frame.winfo_children()[17].var.get()
        filters = []
        if lb.get(0) == "ALL":
            filters = ["I-B*-O","(I-B-B*)-I","O-(B-B*-O)","I-B-B*!","^B-B*-O","^B-B-B*!"]
        else:
            for row in lb.get(0, tkinter.END):
                try:
                    filters.append(row)
                except Exception as e:
                    pass
        print("filters are",filters)
        if index == 0:
            lb.delete(0, tkinter.END)
        if index >=1 and index < 6:
            self.matrix.clear()
            #self.matrix.update()
        if index == 1:
            self.data = self.project.calculate_regex_matching(filters, durationCheck, durationBehaviour, maxVal)
            print("result is", self.data)
            self.matrix.draw(self.data[0],totals=True)
        if index == 2:
            self.data = self.project.calculate_nondirectional_cordon(durationCheck,durationBehaviour,maxVal)
            print("result is",self.data)
            self.matrix.draw(self.data[0],totals=True)
        if index == 3:
            self.data = self.project.calculate_pairs(durationCheck, durationBehaviour, maxVal)
            print("result is", self.data)
            self.matrix.draw(self.data[0],totals=True)
        if index == 4:
            self.data = self.project.calculate_fs_ls(durationCheck, durationBehaviour, maxVal)
            print("result is", self.data)
            self.matrix.draw(self.data[0],totals=True)
        if index == 5:
            self.data = self.project.calculate_full_journeys(durationCheck, durationBehaviour, maxVal)
            print("result is", self.data)
            self.matrix.draw(self.data[0],totals=True)
        if index == 6:
            self.project.save_matched_data(timeType,daysInSeparateSheets)
            messagebox.showinfo(message="Output complete")
        if index == 7:
            print("folder is",self.project.folder)
            if os.path.isdir(self.project.folder):
                p = os.path.normpath(self.project.folder)
                subprocess.Popen('explorer "{0}"'.format(p))
            else:
                messagebox.showinfo(message="Project folder doesnt exist")
        if index == 8:
            self.display_project(self.project.projectId)


    def table_clicked(self,col,iid):
        if col == 0:
            result = messagebox.askyesno(message="Delete this project?")
            if result:
                myDB.delete_project(iid)
                self.table.clear()
                self.display_project_list()
        elif col == 1:
            self.display_project(iid)
        elif col == 2:
            print("loading project", iid)
            folder = myDB.get_folder(iid)
            if folder is None or folder == "" or not os.path.exists(folder):
                messagebox.showinfo(message="No project folder selected, or current project folder doesnt exist. Please select new folder")
                self.display_project(iid)
                return
            file = myDB.get_uploaded_file(iid)
            if file == "" or file is None:
                messagebox.showinfo(message="no plates loaded")
                self.display_project(iid)
                return
            proj = ANPRproject.ANPRproject()
            proj.load_project(iid)
            if len(proj.allMov) == 0:
                messagebox.showinfo(message="no movements, or all movement details are blank")
                self.display_project(iid)
                return

            if not proj.load_plates():
                return
            self.spawn_matching_results_screen(proj)
        #elif col == 3:
         #   print("loading project", iid)
          #  proj = ANPRproject.ANPRproject()
           # proj.load_project(iid)
            #self.project = proj
            #self.spawn_duration_matrix_screen(proj)
            #self.durationMatrix.draw(data = self.project.get_durations())
        else:
            proj = ANPRproject.ANPRproject()
            proj.load_project(iid)
            proj.export_OVTemplate()
            messagebox.showinfo(message="Export Complete")


    def set_up_movements_frame(self,numCams):
        headerFont = tkinter.font.Font(family="times new roman", size=20, weight=tkinter.font.BOLD)
        f = tkinter.font.Font(family="times new roman", size=12)
        outerFrame = self.winfo_children()[2]
        print("no of children",len(outerFrame.winfo_children()))
        movementFrame = outerFrame.winfo_children()[1]
        for child in movementFrame.winfo_children():
            child.destroy()
        tkinter.Label(movementFrame, text="Movements", bg=self.tracsisBlue, fg="white",font=headerFont).grid(row=0, column=0,columnspan=5, sticky="nsew")
        frame = VerticalScrolledFrame(movementFrame,bg="beige")
        frame.grid(row=1,column=0)
        tkinter.Label(frame.interior, text="Site", bg="white",fg=self.tracsisBlue,relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=1, column=0, sticky="nsew")
        tkinter.Label(frame.interior, text="Cam", bg="white",fg=self.tracsisBlue,relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=1, column=1, sticky="nsew")
        tkinter.Label(frame.interior, text="Old", bg="white",fg=self.tracsisBlue,relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=1, column=2, sticky="nsew")
        tkinter.Label(frame.interior, text="New", bg="white",fg=self.tracsisBlue,relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=1, column=3, sticky="nsew")
        tkinter.Label(frame.interior, text="Direction", bg="white",fg=self.tracsisBlue,relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=1, column=4, sticky="nsew")
        for i in range(2*numCams):
            tkinter.Label(frame.interior, text="Site " + str((i//2) + 1), bg="white",fg=self.tracsisBlue,relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=2+i, column=0, sticky="nsew")
            tkinter.Entry(frame.interior, width=10, bg="white").grid(row=2+i, column=1, pady=2, padx=10, sticky="w")
            tkinter.Label(frame.interior, text=str(i+1), bg="white",fg=self.tracsisBlue,relief=tkinter.GROOVE,borderwidth=2, font=f).grid(row=2+i, column=2, sticky="nsew")
            e = tkinter.Entry(frame.interior, width=10, bg="white")
            e.grid(row=2+i, column=3, pady=2, padx=10, sticky="w")
            e.insert(0,str(i+1))
            box = ttk.Combobox(frame.interior, width=15)
            box["values"] = ("In", "Out", "Both")
            box.grid(row=2+i, column=4, pady=2, padx=10, sticky="w")
            box.unbind_class("TCombobox", "<MouseWheel>")


    def display_project(self,projectID):
        self.projectId = projectID
        self.spawn_edit_screen()
        outerFrame = self.winfo_children()[2]
        print("no of children", len(outerFrame.winfo_children()))
        frame = outerFrame.winfo_children()[0]
        project = myDB.get_project_details(self.projectId)
        self.numCameras = project[3]
        for index,i in enumerate(range(22,43)):
            print("looking at",type(frame.winfo_children()[i]))
            if type(frame.winfo_children()[i]) == tkinter.Checkbutton:
                frame.winfo_children()[i].var.set(project[index])
            elif type(frame.winfo_children()[i]) == ttk.Combobox:
                frame.winfo_children()[i].set(project[index])
            else:
                frame.winfo_children()[i].delete(0,"end")
                frame.winfo_children()[i].insert(0,str(project[index]))
        ###
        ### display movements
        ###
        self.set_up_movements_frame(project[3])
        frame = outerFrame.winfo_children()[1].winfo_children()[1]
        movements = myDB.get_project_movements(projectID)
        for movement in movements:
            row = movement[2]
            startIndex = (row*5)
            print(movement,"start index is",startIndex)
            #frame.interior.winfo_children()[startIndex].config(text=str(movement[0]))
            frame.interior.winfo_children()[startIndex + 1].insert(0,str(movement[1]))
            #frame.interior.winfo_children()[startIndex + 2].config(text=str(movement[2]))
            frame.interior.winfo_children()[startIndex + 3].delete(0,"end")
            frame.interior.winfo_children()[startIndex + 3].insert(0,str(movement[3]))
            frame.interior.winfo_children()[startIndex + 4].current(["I","O","B"].index((movement[4])))


    def save_project(self):
        outerFrame = self.winfo_children()[2]
        print("no of children", len(outerFrame.winfo_children()))
        frame = outerFrame.winfo_children()[0]
        data = []
        for i in range(22,43):
            if type(frame.winfo_children()[i]) == tkinter.Checkbutton:
                data.append(frame.winfo_children()[i].var.get())
            else:
                data.append(frame.winfo_children()[i].get())
        print("data is",data)
        if "" in data[0:9]:
            index = data[:9].index("") + 1
            txt = frame.winfo_children()[index].cget("text")
            messagebox.showinfo(message="Empty field :" + txt)
            return
        if data[-1] == "":
            messagebox.showinfo(message="Empty field :Classes")
            return
        d = self.validate_date(frame.winfo_children()[24].get())
        print("date is",d)
        if not d:
            return
        data[2] = d.strftime("%Y-%m-%d")

        ###
        ### validate all the dates and times
        ###

        for i in range(27,41,5):
            d = self.validate_date(frame.winfo_children()[i].get())
            if not d:
                return
            if type(d) == datetime.datetime:
                data[5 + (i-27)] = d.strftime("%Y-%m-%d")
            d = self.validate_date(frame.winfo_children()[i+1].get())
            if not d:
                return
            if type(d) == datetime.datetime:
                data[6+ (i-27)] = d.strftime("%Y-%m-%d")
            d = self.validate_time(frame.winfo_children()[i+2].get())
            if not d:
                return
            if type(d) == datetime.time:
                data[7+ (i-27)] = d.strftime("%H:%M")
            d = self.validate_time(frame.winfo_children()[i+3].get())
            if not d:
                return
            if type(d) == datetime.time:
                data[8+ (i-27)] = d.strftime("%H:%M")

        print("data is now",data)

        movements = []
        frame = outerFrame.winfo_children()[1].winfo_children()[1]
        for child in frame.interior.winfo_children()[5:]:
            if type(child) == tkinter.Label:
                movements.append(child.cget("text"))
            if type(child) == tkinter.Entry or type(child) == ttk.Combobox:
                movements.append(child.get())
        movements = [movements[i:i+5] for i in range(0,len(movements),5)]
        print("movements are",movements)
        self.projectId = myDB.save_project({"project":data,"movements":movements})
        print("project id is",self.projectId)
        if self.projectId:
            proj = ANPRproject.ANPRproject()
            proj.load_project(self.projectId)
            proj.clear_data_folder()
            messagebox.showinfo(message="Saved Successfully")
        else:
            messagebox.showinfo(message="Couldnt Save Project")
            return



    def time_focus_out(self,event):
        if not self.validate_time(event.widget.get()):
            event.widget.delete(0, 'end')


    def date_focus_out(self,event):
       if not self.validate_date(event.widget.get()):
           event.widget.delete(0, 'end')


    def validate_date(self, value):
        #value = event.widget.get()
        if value == "":
            return True
        try:
            d = datetime.datetime.strptime(value, "%d/%m/%Y")
            return d
        except Exception as e:
            pass
        try:
            d = datetime.datetime.strptime(value, "%d/%m/%y")
            return d
        except Exception as e:
            pass
        try:
            d = datetime.datetime.strptime(value, "%Y-%m-%d")
            return d
        except Exception as e:
            pass
        messagebox.showinfo(message="Incorrect Date Format. Must be dd/mm/yyyy or yyyy-mm-dd")

        return False


    def validate_time(self,value):
        #value = event.widget.get()
        if value == "":
            return True
        try:
            d = datetime.datetime.strptime(value,"%H:%M:%S")
            return d.time()
        except Exception as e:
            pass
        try:
            d = datetime.datetime.strptime(value,"%H:%M")
            return d.time()
        except Exception as e:
            pass
        messagebox.showinfo(message="Incorrect Time Format. Must be hh:mm")
        return False


    def change_num_cameras(self,event):
        val = event.widget.get()
        if val=="":
            return
        try:
            val = int(val)
        except Exception as e:
            messagebox.showinfo(message="Number of cameras must be an integer")
            event.widget.delete(0, 'end')
            return
        if val != self.numCameras:
            self.set_up_movements_frame(val)
            self.numCameras = val


    def on_tree_hover(self, event):
        col = self.tree.identify_column(event.x)
        _iid = self.tree.identify_row(event.y)
        if _iid != self.last_focus:
            if self.last_focus:
                self.tree.item(self.last_focus, tags=[])
            self.tree.item(_iid, tags=['focus'])
            self.last_focus = _iid


def validate_filter(filter):
    if filter == "ALL":
        return True
    if "(" in filter:
        if (")" in filter and filter.index("(") > filter.index(")")) or not ")" in filter:
            #messagebox.showinfo(message="Incorrect Brackets")
            return False
    if ")" in filter:
        if ("(" in filter and filter.index("(") > filter.index(")")) or not "(" in filter:
            #messagebox.showinfo(message="Incorrect Brackets")
            return False
    tokens = filter.split("-")
    if len(tokens) < 2:
        #messagebox.showinfo(message="You need to have 2 or more tokens in a filter")
        return False
    if "^" in filter and not "^" in tokens[0]:
        #messagebox.showinfo(message="If you are using ^, it must always be the first character in the filter")
        return False
    if "!" in filter and not "!" in tokens[-1]:
        #messagebox.showinfo(message="If you are using !, it must always be the last character in the filter")
        return False
    if "" in tokens:
        #messagebox.showinfo(message="Blank tokens not allowed")
        return False
    for i, t in enumerate(tokens[:-1]):
        if "*" in t:
            temp = t.replace("*", "")
            print("temp is", temp, "t is", t)
            if temp == tokens[i + 1]:
                temp = t
                tokens[i] = tokens[i + 1]
                tokens[i + 1] = temp
    for t in tokens:
        t = t.replace("*", "")
        t = t.replace("^", "")
        t = t.replace("!", "")
        t = t.replace("¬", "")
        t = t.replace("(", "")
        t = t.replace(")", "")
        print("testing", t)
        if t == "":
            #messagebox.showinfo(message="A token cannot only contain a special char(!,^,*,¬)")
            return False
        if t not in ["I", "B", "O", "A"]:
            try:  #### is it numeric?
                temp = int(t)
            except ValueError as e:
                #messagebox.showinfo(message="A token must contain I,B,O or a number")
                return False
    return True


myDB.set_file("C:/Users/NWatson/PycharmProjects/ANPR/blah.sqlite")
win = mainWindow()
win.mainloop()