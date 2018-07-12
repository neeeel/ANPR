__author__ = 'neil'

import sqlite3
import datetime
import time
import logging
from tkinter import filedialog
from tkinter import messagebox
import itertools
import os


conn = None
cur = None
transactionQueue = []
processTransactions = False
settings = None

def create_Db():
    '''
    Create a new Database to store Job Details
    '''

    file = filedialog.asksaveasfilename()
    print(file)
    if file == "":
        return
    index = len(file) - file[::-1].index("/")
    path=file[:index]
    fileName = file[index:] + ".sqlite"


    global conn,cur
    conn = sqlite3.connect(path+fileName, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()

    cur.execute('''CREATE TABLE if NOT EXISTS Job (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    jobNo TEXT,
                    name TEXT,
                    surveyDate DATE,
                    timePeriod1 TEXT,
                    timePeriod2 TEXT,
                    timePeriod3 TEXT,
                    timePeriod4 TEXT,
                    noOfCameras INTEGER,
                    interval INTEGER,
                    OVTemplate DATE,
                    OVCounts DATE,
                    unclassed DATE,
                    classed DATE,
                    comparison DATE,
                    completed DATE,
                    createdBy TEXT,
                    createdDate DATE,
                    classification TEXT,
                    folder TEXT,
                    selectedDuplicates INTEGER,
                    plateRestriction INTEGER
                    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS Site (
                    id	INTEGER PRIMARY KEY AUTOINCREMENT,
                    siteNo INTEGER,
                    jobNo INTEGER,
                    FOREIGN KEY(JobNo) REFERENCES Job(ID)
                )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS Movement (
                    id	INTEGER PRIMARY KEY AUTOINCREMENT,
                    siteID INTEGER,
                    cameraNo TEXT,
                    originalMovementNum INTEGER,
                    combinedMovementNum INTEGER,
                    dir INTEGER,
                    comment TEXT,
                    FOREIGN KEY(siteID) REFERENCES Site(ID)
                )''')
    conn.commit()
    #messagebox.askyesno(message="Do you want to set this new database as the working database?")
    return path+fileName


def delete_project(projectID):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    result = cur.execute(("SELECT * FROM project WHERE id =  ?"),
                         (projectID,)).fetchone()
    if result is None:
        return
    jobID = result[0]
    print("job id is",jobID)
    try:
        cur.execute('''DELETE from movement where jobID = ? ''', (jobID,)).fetchall()
        cur.execute('''DELETE from project where id = ? ''', (jobID,))
        conn.commit()
    except sqlite3.OperationalError as e:
        messagebox.showinfo(message="Database is locked, couldnt save project\n, please try again later.")
        return False


def save_project(data):
    print("din myDB data is,",data)
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    print("successfully opend db")
    job = data["project"]
    movements = data["movements"]
    uploadedData = None
    jobID = None
    ###
    ### check job doesnt already exist
    ###
    print("looking for",job)
    result = cur.execute('''SELECT  * from project where projectNumber = ? and projectName = ? and projectDate = ?''',(job[0],job[1],job[2]))
    row = result.fetchone()
    if row is not None:
        if messagebox.askyesno(message="This job already exists, do you want to overwrite it?"):
            jobID = row[0]
            try:
                cur.execute('''DELETE from movement where jobID = ? ''', (jobID,))
                cur.execute('''DELETE from project where id = ? ''', (jobID,))
                folder = row[26]
                uploadedData = row[11]
            except sqlite3.OperationalError as e:
                print("eror:",e)
                messagebox.showinfo(message="Database is locked, couldnt save project\n, please try again later.")
                return False
        else:
            return False
    else:
        folder = filedialog.askdirectory(title="Please select Project Location",initialdir="S:\\SCOTLAND DRIVE 2\\JOB FOLDERS\\")
        if folder == "":
            messagebox.showinfo(message="No Project Location selected, project not saved")
            return False

    print("selected job folder is",folder)
    job.append(folder)
    job.append(uploadedData)
    print("job is",job)
    createdDate = datetime.datetime.today().strftime("%Y-%m-%d")
    job.append(createdDate)
    print("inserting",tuple(job))
    print(len(job))
    try:
        cur.execute("INSERT INTO project (projectNumber,projectName,projectDate,numCameras,interval,start1,end1,"
                    "from1,to1,split1,start2,end2,from2,to2,split2,start3,end3,from3,end3,split3,classes,beingProcessed,folder,uploadedData,addedDate) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,?,?,?)",tuple(job)
                    )
        jobID = cur.lastrowid
    except sqlite3.OperationalError as e:
        print(e)
        messagebox.showinfo(message="Database is locked, couldnt save project\n, please try again later.")
        print(e)
        return False
    #result= cur.execute('''SELECT  ID from job where name = ? ''', (job["jobname"],))

    print("inserted new job, id is ",jobID)
    print("site data to be inserted is",movements)
    for mov in movements:
        if mov[3] != "" and mov[4] != "":
            siteNo = mov[0]
            cam = mov[1]
            old = int(mov[2])
            new=int(mov[3])
            dir = mov[4][0]
            try:
                cur.execute("INSERT INTO Movement(siteID,oldMov,newMov,dir,cameraNo,jobId) VALUES (?,?,?,?,?,?)",
                        (siteNo, old, new, dir,cam,jobID))
            except sqlite3.OperationalError as e:
                print(e)
                messagebox.showinfo(message="Database is locked, couldnt save project\n, please try again later.")
                return False
            print("inserting new movement")
        print("committing")
        #conn.commit()
    conn.commit()
    try:
        os.mkdir(folder + "/output")
    except Exception as e:
        print(e,type(e))
    try:
        os.mkdir(folder + "/data")
    except Exception as e:
        print(e, type(e))
    return jobID


def get_project_details(id):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    print("successfully opend db")
    result = cur.execute('''SELECT  projectNumber,projectName,strftime('%d/%m/%Y',projectDate),numCameras,interval,strftime('%d/%m/%Y',start1),strftime('%d/%m/%Y',end1),from1,to1,split1,
                            strftime('%d/%m/%Y',start2),strftime('%d/%m/%Y',end2),from2,to2,split2,strftime('%d/%m/%Y',start3),strftime('%d/%m/%Y',end3),from3,to3,split3,classes from project where id = ? ''',(id,)).fetchone()
    if result is not None:
        result = [i if not i is None else "" for i in result]
        return result
    return None


def get_folder(id):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    print("successfully opend db")
    result = cur.execute("SELECT folder from project where id = ?",(id,)).fetchone()
    if not result is None:
        return result[0]
    return result


def get_uploaded_file(id):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    print("successfully opend db")
    result = cur.execute("SELECT uploadedData from project where id = ?", (id,)).fetchone()
    if not result is None:
        return result[0]
    return result


def set_uploaded_file(id,file):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    print("successfully opend db")
    result = cur.execute("UPDATE project set  uploadedData = ?  where id = ?", (file,id)).fetchone()
    conn.commit()


def change_project_folder(id,file):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    print("successfully opend db")
    result = cur.execute("UPDATE project set  folder = ?  where id = ?", (file,id)).fetchone()
    conn.commit()


def get_times(id):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    print("successfully opend db")
    result = cur.execute("SELECT start1,end1,from1,to1,split1,start2,end2,from2,to2,split2,start3,end3,from3,to3,split3 from project where id = ?", (id,)).fetchone()
    if not result is None:
        return result
    return []


def get_project_movements(id):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    print("successfully opend db")
    result = cur.execute('''SELECT siteId,cameraNo,oldMov,newMov,dir  from movement where jobid = ? ''',(id,)).fetchall()
    #result = [i if not i is None else "" for i in result]
    print("result is",result)
    return result


def get_project_list():
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    result = cur.execute("SELECT id,projectName,projectNumber,projectDate from project ORDER BY addedDate DESC").fetchall()
    return result


def get_classes(id):
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    result = cur.execute("SELECT classes from project where id = ?", (id,)).fetchone()
    if not result is None:
        return result[0].split(",")
    return result


def get_movements(jobId):
    print("job id is", jobId, databaseFile)
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    inMov = cur.execute(
        "SELECT newMov from movement "
        "WHERE jobID = ? and dir = 'I'", (str(jobId),)).fetchall()
    outMov = cur.execute(
        "SELECT newMov from movement "
        "WHERE jobID = ? and dir = 'O'", (str(jobId),)).fetchall()
    allMov = cur.execute(
        "SELECT newMov from movement "
        "WHERE jobID = ?", (str(jobId),)).fetchall()
    return [[i[0] for i in inMov], [i[0] for i in outMov], [i[0] for i in allMov]]


def get_db_file():
    global databaseFile
    return databaseFile


def set_file(file):
    global databaseFile
    databaseFile = file

##################################################################################################################
#
# below here is old code
#
#####################################################################################################################

def load_job(jobNo,jobName,jobDate):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    job = {}
    d = jobDate
    print(d)
    result = cur.execute(("SELECT * FROM job WHERE name =? and jobNo = ? and surveydate = ?"),(jobName,jobNo,d)).fetchone()
    if result is None:
        return job
    print("job id is",result[0])
    job["id"] = result[0]
    job["jobno"] = result[1]
    job["jobname"] = result[2]
    job["surveydate"] = result[3]
    job["timeperiod1"] = result[4]
    job["timeperiod2"] = result[5]
    job["timeperiod3"] = result[6]
    job["timeperiod4"] = result[7]
    job["noOfCameras"] = result[8]
    job["interval"] = result[9]
    job["ovtemplate"] = result[10]
    job["ovcounts"] = result[11]
    job["unclassed"] = result[12]
    job["classed"] = result[13]
    job["comparison"] = result[14]
    job["completed"] = result[15]
    job["createdby"] = result[16]
    job["createddate"] = result[17]
    job["classification"] = result[18]
    job["folder"] = result[19]
    job["selectedduplicates"] = result[20]
    job["platerestriction"] = result[21]
    job["platerestrictionpercentages"] = []
    job["duplicateValues"] = []
    job["timeAdjustmentsDictionary"] = {}
    job["durationsDictionary"] = {}
    print("on loading project, folder is",job["folder"])
    result = cur.execute("SELECT site.siteno,movement.combinedmovementnum,movement.originalmovementnum,movement.dir,movement.comment,movement.siteID FROM site JOIN job "
                         "ON site.jobno = job.ID JOIN Movement ON site.id = movement.siteid "
                         "WHERE job.id = ?",(job["id"],)).fetchall()


    if not os.path.exists(job["folder"]):
        messagebox.showinfo(message="The assigned folder for this project doesnt exist. Please select a folder location")
        dir = ""
        while dir == "":
            dir = filedialog.askdirectory(title="Please select Project Location",initialdir="S:\\SCOTLAND DRIVE 2\\JOB FOLDERS\\")
        job["folder"] = dir
        update_value_of_field(job["id"],"folder",dir)
        try:
            os.mkdir(job["folder"] + "/output")
        except Exception as e:
            print(e, type(e))
        try:
            os.mkdir(job["folder"] + "/data")
        except Exception as e:
            print(e, type(e))

    l = []
    if result is not None:
        l = [[item for item in r]  for r in result]
    print(l)
    sites = {}
    comments = []
    for item in l:
        siteNo = item[0]
        movement = item[1]
        original = item[2]
        dir = item[3]
        if dir == "":
            dir = 0
        print("looking for site",siteNo,",movement",movement)
        site = sites.get(siteNo,{})
        print("after searching, site is",site)
        mvmt = site.get(movement,{"newmovement":movement,"originalmovements":[]})
        print("mvmt is",mvmt)
        mvmt["originalmovements"].append(original)
        mvmt["dir"] = dir
        site[movement]=mvmt
        print("site is",site)
        sites[siteNo] = site
    result = cur.execute("SELECT id FROM site WHERE jobNo = ?",(job["id"],)).fetchall()
    for r in result:
        for c in cur.execute("SELECT comment,combinedmovementnum from movement WHERE siteId = ?  group by combinedmovementnum",(r[0],)).fetchall():
            #print("comment is",c[0])
            comments.append(c[0])
    #print("comments are",comments)
    job["comments"] =comments
    #print("sites are",sites)
    job["sites"] = sites
    return job





def update_duplicates(jobID,duplicates):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    d = datetime.datetime.today().date()
    try:
        cur.execute("UPDATE job SET selectedDuplicates= ? WHERE ID = ?", (duplicates, jobID))
    except sqlite3.OperationalError as e:
        messagebox.showinfo(message="database is locked, try again later")
        return
    conn.commit()

def update_job_with_progress(jobID,entry):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    d = datetime.datetime.today().date()
    print("trying to update",entry)
    try:
        cur.execute("UPDATE job SET " + entry + " = ? WHERE ID = ?",(d,jobID))
    except sqlite3.OperationalError as e:
        messagebox.showinfo(message="database is locked, couldnt update progress of job")
        return
    conn.commit()

def get_value_of_field(jobID,field):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    print("trying to update", field)
    try:
        result = cur.execute("SELECT " + field + " from job WHERE ID = ?", ( jobID,)).fetchone()
        return result[0]

    except sqlite3.OperationalError as e:
        messagebox.showinfo(message="database is locked, couldnt update progress of job")
        return

def update_value_of_field(jobID,field,value):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    d = datetime.datetime.today().date()
    print("trying to update",field)
    try:
        cur.execute("UPDATE job SET " + field + " = ? WHERE ID = ?",(value,jobID))
    except sqlite3.OperationalError as e:
        messagebox.showinfo(message="database is locked, couldnt update progress of job")
        return
    conn.commit()

def process_transactions():
    global processTransactions,settings
    conn = sqlite3.connect('markets.sqlite', detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    processTransactions = True
    while processTransactions == True:
        while len(transactionQueue) > 0:
            transaction = transactionQueue.pop(0)
            #print("trying to process  ",transaction[0],transaction[1])
            cur.execute(transaction[0],transaction[1])
        if settings != None:
            try:
                cur.execute("DELETE FROM settings")
                for s in settings:
                    #print ("setting is " ,s)
                    width,height,x,y = s
                    cur.execute("INSERT  INTO settings  VALUES (NULL,?,?,?,?,NULL)",(x,y,width,height))
                settings = None
            except sqlite3.OperationalError as e:
                messagebox.showinfo(message="Database is locked, couldnt save settings\n, please try again later.")
                return False
        #print("committing")
        conn.commit()
        time.sleep(.5)
    cur.close()
    conn.close()
    logging.info("exiting process transactions thread")

def stop_transactions():
    global processTransactions
    processTransactions = False

def get_jobs():
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    jobs = []
    result = cur.execute('''SELECT * FROM job ORDER BY createdDate DESC''').fetchall()
    if result is not None:
        for row in result:
            job= []
            job.append(row[1])
            job.append(row[2])
            job.append (datetime.datetime.strftime(row[3],"%d/%m/%y"))
            #job.append )row[4])
            times = row[4]
            for i in range(5,8):
                #print("item is ",row[i],":")
                if row[i] != "-":
                    times = times + " & "  + row[i]
            job.append(times)
            if row[10] is None:
                job.append("")
            else:
                job.append(row[10].strftime("%d/%m/%y"))
            if row[11] is None:
                job.append("")
            else:
                job.append(row[11].strftime("%d/%m/%y"))
            if row[12] is None:
                job.append("")
            else:
                job.append(row[12].strftime("%d/%m/%y"))
            if row[13] is None:
                job.append("")
            else:
                job.append(row[13].strftime("%d/%m/%y"))
            if row[14] is None:
                job.append("")
            else:
                job.append(row[14].strftime("%d/%m/%y"))
            if row[15] is None:
                job.append("")
            else:
                job.append(row[15].strftime("%d/%m/%y"))
            if row[16] is None:
                job.append("")
            else:
                job.append(row[16])
            job.append(datetime.datetime.strftime(row[17],"%d/%m/%y"))
            print("job is",job)
            jobs.append(job)
    return jobs

def update_comment(jobID,siteNo,move,text):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    siteID = cur.execute("SELECT id from site WHERE siteNo = ? AND jobNo =  ?",(siteNo,jobID)).fetchone()[0]
    try:
        cur.execute("UPDATE movement SET comment = ? WHERE siteID = ?  and combinedMovementNum = ?",(text,siteID,move))
        conn.commit()
    except sqlite3.OperationalError as e:
        messagebox.showinfo(message="Database is locked, couldnt save comment\n, please try again later.")
        return False

def getSettings():
    conn = sqlite3.connect('markets.sqlite', detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    settings = cur.execute(("SELECT * FROM settings ORDER BY settings.x,settings.y"))
    result = [(s[1],s[2],s[3],s[4]) for s in settings.fetchall()]
    cur.close()
    conn.close()
    return result

def saveSettings(s):
    global settings
    settings = s

def open_db():
    global conn, cur
    conn = sqlite3.connect('markets.sqlite', detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()

def close_db():
    global conn, cur
    cur.close()
    conn.close()

def set_file(file):
    global databaseFile
    databaseFile = file

def check_Db_file():
    global databaseFile
    try:
        conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cur = conn.cursor()
        #result = cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",("User",))
        result = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        result = [item[0] for item in result]
        print(result)
        if len(result) != 5:
            cur.close()
            return False
        if result[0] == "Project"  and result[2] == "User" and result[3] == "Role" and result[4] == "workedOn":
            cur.close()
            return True
        cur.close()
        return False
    except Exception as e:
        return False

databaseFile = None
#save_Job(data,file)
#job = load_job("3279-Lon","Oxford","07/05/16")
#print(job["folder"])



























