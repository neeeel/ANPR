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
                    duplicatesSelected INTEGER
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

def delete_job(jobNo,jobName,jobDate):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    d = datetime.datetime.strptime(jobDate, "%d/%m/%y").date()
    result = cur.execute(("SELECT * FROM job WHERE name =? and jobNo = ? and surveyDate = ?"),
                         (jobName, jobNo, d)).fetchone()
    if result is None:
        return
    jobID = result[0]
    print("job id is",jobID)
    sites = cur.execute('''SELECT * from Site where jobNo = ? ''', (jobID,)).fetchall()
    for site in sites:
        siteID = site[0]
        print("looking at site",siteID)
        cur.execute('''DELETE from movement where siteid = ? ''', (siteID,))
    conn.commit()
    cur.execute('''DELETE from site where jobno = ? ''', (jobID,))
    cur.execute('''DELETE from job where id = ? ''', (jobID,))
    conn.commit()

def save_Job(data):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    job = data["job"]
    sites = data["sites"]

    ###
    ### check job doesnt already exist
    ###
    print("looking for",job["jobname"])
    result = cur.execute('''SELECT  * from Job where name = ? and surveyDate = ?''',(job["jobname"],datetime.datetime.strptime(job["surveyDate"],"%d/%m/%y").date()))
    row = result.fetchone()
    if row is not None:
        if messagebox.askyesno(message="This job already exists, do you want to overwrite it?"):
            print("phoo")
            jobID = row[0]

            for site in cur.execute('''SELECT * from Site where jobNo = ? ''',(jobID,)).fetchall():
                siteID = site[0]
                cur.execute('''DELETE from movement where siteid = ? ''',(siteID,))
            cur.execute('''DELETE from site where jobno = ? ''', (jobID,))
            cur.execute('''DELETE from job where id = ? ''', (jobID,))
        else:
            return

    d = datetime.datetime.strptime(job["surveyDate"],"%d/%m/%y").date()
    createdDate = datetime.datetime.today().date()
    cur.execute("INSERT INTO job (name,jobNo,surveydate,timeperiod1,timeperiod2,timeperiod3,timeperiod4,noofcameras,interval,classification,folder,selectedDuplicates,createdDate) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (job["jobname"],job["jobno"],d,job["timeperiod1"]
                                                    ,job["timeperiod2"],job["timeperiod3"],job["timeperiod4"]
                                                    ,job["noOfCameras"],job["interval"],job["classification"],job["folder"],-1,createdDate))
    #result= cur.execute('''SELECT  ID from job where name = ? ''', (job["jobname"],))
    jobID = cur.lastrowid
    print("inserted new job, id is ",jobID)
    print("site data to be inserted is",sites)
    for site in sites:
        print("looking to add to database, site",site)
        siteNo = site[0]
        combined = int(site[1])
        original=int(site[2])
        dir = int(site[3])
        cam = site[4]
        print("looking for site",siteNo,"for job",job["jobname"])
        result = cur.execute('''SELECT  * from Site where siteno = ?  AND jobNo = ?''', (siteNo,jobID))
        row = result.fetchone()
        if row is None:
            print("didnt find site",siteNo," adding to database, site",siteNo)
            cur.execute("INSERT INTO Site (siteno,jobno) VALUES(?,?)",(siteNo,jobID))
            siteID = cur.lastrowid ## primary key of site that we just inserted
            cur.execute("INSERT INTO Movement(siteID,combinedMovementNum,originalMovementNum,dir,cameraNo) VALUES (?,?,?,?,?)",(siteID,combined,original,dir,cam))
            print("inserting new movement for site",siteNo,"siteID",siteID)
        else:
            siteID = row[0]  ### the primary key for a site, we need it to create a new movement record
            print("We found site",row[1],"with id",siteID)
            cur.execute("INSERT INTO Movement(siteID,combinedMovementNum,originalMovementNum,dir,cameraNo) VALUES (?,?,?,?,?)",
                        (siteID, combined, original, dir,cam))
            print("inserting new movement")
        print("committing")
        conn.commit()
    conn.commit()

def load_job(jobNo,jobName,jobDate):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    job = {}
    d = datetime.datetime.strptime(jobDate,"%d/%m/%y").date()
    print(d)
    result = cur.execute(("SELECT * FROM job WHERE name =? and jobNo = ? and surveyDate = ?"),(jobName,jobNo,d)).fetchone()
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
    job["noofcameras"] = result[8]
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
    result = cur.execute("SELECT site.siteno,movement.combinedmovementnum,movement.originalmovementnum,movement.dir,movement.comment,movement.siteID FROM site JOIN job "
                         "ON site.jobno = job.ID JOIN Movement ON site.id = movement.siteid "
                         "WHERE job.id = ?",(job["id"],)).fetchall()
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
        #print("checking site with id",r[0])
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
        messagebox.showinfo(message="database is locked, try again later")
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
            cur.execute("DELETE FROM settings")
            for s in settings:
                #print ("setting is " ,s)
                width,height,x,y = s
                cur.execute("INSERT  INTO settings  VALUES (NULL,?,?,?,?,NULL)",(x,y,width,height))
            settings = None
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
    result = cur.execute('''SELECT * FROM job ''').fetchall()
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
    cur.execute("UPDATE movement SET comment = ? WHERE siteID = ?  and combinedMovementNum = ?",(text,siteID,move))
    conn.commit()

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



databaseFile = ""
#save_Job(data,file)
#job = load_job("3279-Lon","Oxford","07/05/16")
#print(job["folder"])



























