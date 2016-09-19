import pandas as pd
import numpy as np
import datetime
import openpyxl
from tkinter import messagebox,filedialog
import os.path
import mainwindow
import myDB
import pickle

flag = False


def convert_movement_to_site(val,job):
    ###
    ### function to convert one column of the pandas dataframe.
    ### val is the original movement number for a vehicle
    ### returns the site number for that specific original movement
    ###
    for siteNo,site in job["sites"].items():
        for moveNo, movement in site.items():
            if val in movement["originalmovements"]:
                #print("site",siteNo,"contains original movement",val)
                return siteNo
    return 0

def convert_old_movement_to_new(val,job):
    ###
    ### function to convert one column of the pandas dataframe
    ### val is the original movement number for a specific vehicle
    ### returns the new movement number
    ###
    for siteNo, site in job["sites"].items():
        for moveNo, movement in site.items():
            if val in movement["originalmovements"]:
                # print("site",siteNo,"contains original movement",val)
                return moveNo

def convert_movement_to_dir(val,job):
    ###
    ### function to convert a column of the pandas dataframe
    ### val is the new movement number for a specific vehicle
    ### returns the direction (0=in,1=out,2=both)
    ###
    for siteNo, site in job["sites"].items():
        for moveNo, movement in site.items():
            if val == moveNo:
                # print("site",siteNo,"contains original movement",val)
                return movement["dir"]

def load_unclassed_plates(job):
    global df
    ###
    ### Load unclassed vehicles file, sort out columns etc
    ###

    folder = job["folder"]
    if os.path.isfile(folder + "/data.pkl"):
        result =  messagebox.askquestion("Warning",
                                      "The unclassed plates have previously been loaded, do you want to reload them?")
        if result == "no":
            return
    result = messagebox.askquestion("Warning",message="This will reset all the files in the project, and wipe any progress, do you want to continue?")
    if result == "no":
        return
    try:
        os.remove(job["folder"]+"/data.pkl")
    except Exception as e:
        pass
    try:
        os.remove(job["folder"] + "/classedData.pkl")
    except Exception as e:
        pass
    try:
        os.remove(job["folder"] + "/edited.pkl")
    except Exception as e:
        pass

    file = filedialog.askopenfilename(initialdir=folder)
    if file == "":
        messagebox.showinfo(message = "No file selected,no plates loaded")
        return
    ext = file[file.rfind("."):]
    print("extension is",ext)
    print("looking for file ",file)
    if ext not in (".xlsx",".csv",".xlsm",".xls"):
        messagebox.showinfo(message="Not valid CSV file, No plates loaded")
        return

    try:
        df = pd.read_excel(file, converters={"VRN": str, "Direction": str, "Date": str, "Time": str},parse_cols=[0, 2, 3, 6])
        df["Date"] = pd.to_datetime(df["Date"] + " " + df["Time"])
        df.drop(["Time"], inplace=True, axis=1)
        #df.set_index(["Date"],inplace=True)
        df["Class"] = ""

        ###
        ### set up the timediff and duplicates column
        ###

        df["Duplicates"] = "N"
        df["Site"] = df["Movement"].apply(convert_movement_to_site, args=(job,))
        df["newMovement"] = df["Movement"].apply(convert_old_movement_to_new, args=(job,))
        df["dir"] = df["newMovement"].apply(convert_movement_to_dir, args=(job,))
        df.sort_values(by=["VRN", "newMovement"], inplace=True, ascending=[True, True])
       #df.reset_index(inplace=True)
        df["timeDiff"] = df["Date"].diff()
        df.set_index(["Date"],inplace=True)
        mask = (df["VRN"] != df["VRN"].shift(-1)) | (df["newMovement"] != df["newMovement"].shift())
        df["timeDiff"][mask] = np.nan
        #df = df["2016-07-05"]

        df.to_pickle(folder + "/data.pkl")

    except Exception as e:
        messagebox.showinfo(message="Error occured while loading csv file ," + e)
        df = None
        return
    myDB.update_job_with_progress(job["id"],"unclassed")
    compute_comparison_data(job)
    load_job(job)
    return

    ###
    ### drop any plates that have a length less than 4
    ###

    print("before dropping short plates, df has ", len(df), "entries")
    df = df[df["VRN"].str.len() > 4]
    print("after dropping short plates, df has ", len(df), "entries")

    ###
    ### drop duplicates that have same Reg no and same movement no
    ###

    print("before dropping duplicate plate/movement, df has ", len(df), "entries")
    df.drop_duplicates(["VRN", "Movement"], inplace=True)
    print("after dropping duplicate plate/movement, df has ", len(df), "entries")

    ###
    ### drop singletons
    ###

    print("before dropping, df has ",len(df),"entries")
    counts = df.VRN.value_counts()
    mask = df["VRN"].isin(counts[counts > 1].index)
    df= df[mask]
    print("after dropping, df has ", len(df), "entries")
    #print(df[mask])

def load_completed_count(job):
    global overviewDf
    overviewDf = None
    dataframes = []
    seen = set()
    classes = [x for i, x in enumerate(job["classification"].split(",")) if i % 2 == 0 and x not in seen and not seen.add(x)]
    classes.insert(0, "Time")
    numClasses = int(len(classes))
    file = filedialog.askopenfilename(initialdir=job["folder"])
    try:
        wb = openpyxl.load_workbook(file,data_only=True)
        for siteNo,siteDetails in job["sites"].items():
            print("loading site ",siteNo)
            print("site is",siteDetails)
            for movement,x in siteDetails.items():
                print("loading movement",movement)
                data = []
                print("movement details are ",x)
                try:
                    ws = wb.get_sheet_by_name("site " + str(siteNo))
                except openpyxl.utils.exceptions.SheetTitleException as e:
                    try:
                        ws = wb.get_sheet_by_name("Site " + str(siteNo))
                    except openpyxl.utils.exceptions.SheetTitleException as e:
                        print("bad sheet")
                        continue
                except KeyError as e:
                    try:
                        ws = wb.get_sheet_by_name("Site " + str(siteNo))
                    except KeyError as e:
                        print("couldnt find sheet")
                        print(e)
                        continue
                firstMovementOnSheet = ws["C3"].value
                if movement == firstMovementOnSheet:
                    offset = 1
                else:
                    offset = numClasses + 3

                for row in ws.iter_rows(column_offset=offset,row_offset=7):
                    #print("row is",row)
                    rowData = []
                    for cell in row[:numClasses]:
                        if isinstance(cell.value,datetime.time):
                            rowData.append(cell.value.strftime("%H:%M:%S"))
                        else:
                            rowData.append(cell.value)
                    if rowData != [] and "hr" not in str(rowData[0]).lower() and "total" not in str(rowData[0]).lower() :
                        data.append(rowData)
                data.insert(0,classes)
                countsDf = pd.DataFrame(data[1:],columns=data[0])
                countsDf.dropna(inplace =True)
                countsDf["Site"] = siteNo
                countsDf["Movement"] = movement
                countsDf["Date"] = datetime.datetime.strftime(job["surveydate"],"%d/%m/%y")
                countsDf["Date"] = pd.to_datetime(countsDf["Date"] + " " + countsDf["Time"],dayfirst=True)
                countsDf.drop(["Time"], inplace=True, axis=1)
                countsDf.set_index(["Date"], inplace=True)
                dataframes.append(countsDf)
    except Exception as e:
        print("oh phoo")
        print(e)
        messagebox.showinfo(message="Something went wrong when trying to read site "+ str(siteNo) + ", please check the format of the sheet")
        overviewDf=None
        #wb.close()
        return
    overviewDf = pd.concat(dataframes)
    for cl in classes[1:]:
        overviewDf[cl] = overviewDf[cl].astype(int)
    overviewDf.to_pickle(job["folder"] + "/OVData.pkl")
    compute_comparison_data(job)

def load_classes(job):
    global df
    folder = job["folder"]
    if not os.path.isfile(folder + "/data.pkl"):
        messagebox.showinfo(message="You havent loaded any unclassed plates yet")
        return
    if os.path.isfile(folder + "/classes.pkl"):
        if not messagebox.askquestion("Warning","The classes have previously been loaded, do you want to reload them?"):
            return
    file = filedialog.askopenfilename(initialdir=folder)
    if file == "":
        messagebox.showinfo(message="No file selected,no classes loaded")
        return
    ext = file[file.rfind("."):]
    if ext not in (".xlsx", ".csv", ".xlsm", ".xls"):
        messagebox.showinfo(message="Not valid file, No classes loaded")
        return
    if not os.path.isfile(folder + "/data.pkl"):
        messagebox.showinfo(message="The unclassed plates havent been loaded")
        return
    try:
        df = pd.read_pickle(job["folder"] + "/data.pkl")
        tempdf = pd.read_excel(file)
        tempdf.to_pickle(job["folder"] + "/classes.pkl")
        df.drop("Class", inplace=True)
        df = df.reset_index().merge(tempdf, how="left", on="VRN").set_index("Date")
        df.drop("Class_x", axis=1, inplace=True)
        df.rename(columns={"Class_y": "Class"}, inplace=True)
        #df = df[pd.notnull(df["Class"])]
        df.to_pickle(folder + "/classedData.pkl")
        myDB.update_job_with_progress(job["id"],"classed")
        compute_comparison_data(job)
    except Exception as e:
        messagebox.showinfo(message="Something went wrong when trying to load the classes, please check that the file is a valid file")
        df = None
        return
    compute_comparison_data(job)

def load_job(job):
    global df,overviewDf
    ### load plates, classed or unclassed, from pickled dataframe file

    try:
        df = pd.read_pickle(job["folder"] + "/classedData.pkl")
        #print(df.info())
    except FileNotFoundError as e:
        # messagebox(message="Data file is missing, you will need to load the unclassed plates")
        print("No classed data found, trying to load unclassed data")
        try:
            df = pd.read_pickle(job["folder"] + "/data.pkl")
            #print(df.info())
        except FileNotFoundError as e:
            messagebox.showinfo(message="Data file is missing, you will need to load the unclassed plates")
            print("No unclassed data found")
            return True
        print("Loaded unclassed plates, no of entries",len(df))



    ###
    ### load comparison
    ###
    try:
        overviewDf = pd.read_pickle(job["folder"] + "/OVData.pkl")
        print("Loaded completed overview count")
    except FileNotFoundError as e:
        # messagebox(message="Data file is missing, you will need to load the unclassed plates")
        print("No comparison data found")
        #load_completed_count(job)
    except Exception as e:
        print(e)
        print("ERRRRRRRROR")
        return False

    duplicates = []
    print(df.head())
    for i in range(31):
        duplicates.append (len(df[df["timeDiff"] == pd.Timedelta(seconds=i)]))

    for i in range(0, 465, 15):
        mask = (df["timeDiff"] >= pd.Timedelta(seconds=i)) & (df["timeDiff"] < pd.Timedelta(seconds=i + 15))
        duplicates.append (len(df[mask]))
    job["duplicateValues"] = duplicates
    set_duplicates(job["selectedduplicates"])
    print("duplicates are",duplicates)
    return True

def get_comparison_data(job):
    ###
    ### retrieve and return the comparison data for a job
    ### If we have previously computed it, load it from the pickled file
    ### otherwise, compute it
    ###
    if os.path.isfile(job["folder"] + "/comparisondata.pkl"):
        with open(job["folder"] + '/comparisondata.pkl', 'rb') as handle:
            data = pickle.load(handle)
            site = data[0]
            print("loaded site",site)
            l = [movement for key, movement in sorted(site["movements"].items())]
            movement = l[0]
            print("after loading, data is~",movement["data"])
    else:
        data = compute_comparison_data(job)
    print("finished getting comparison data")
    return data

def compute_comparison_data(job):
    ###
    ### compute the comparison data from the loaded plates and overview count
    ### do this for each site in the job.
    ### the data for each site is a dictionary, with sub-dictionaries for each movement
    ### each sub dictionary has a list of data, in the format
    ###[[original OV data],[Edited OV data],[unclassed original ANPR data],[unclassed ANPR data -duplicates removed],[classed original ANPR data],[classed ANPR data-duplicates removed]]
    ### each movement also has a subdictionary with summary details.
    ### each set of data is set up ready to display, with column and row totals, and timestamps already entered
    ###

    global df,overviewDf
    if overviewDf is None:
        messagebox.showinfo(message="No Overview counts loaded")
        return None
    if df is None:
        messagebox.showinfo(message="No Classed or Unclassed plates loaded")
        return None
    results = []
    seen = set()
    ANPRClasses = [x for i, x in enumerate(job["classification"].split(",")) if i % 2 == 1 and x not in seen and not seen.add(x)]
    seen = set()
    OVClasses = [x for i, x in enumerate(job["classification"].split(",")) if i % 2 == 0 and x not in seen and not seen.add(x)]
    ANPRtoOVdict = {} ### this will hold a dictionary of how we combine the OV classes into the ANPR classes
    for cl in ANPRClasses:
        ANPRtoOVdict[cl] = []
        for item in [i for i, x in enumerate(job["classification"].split(",")) if x == cl and i % 2 == 1]:
            ANPRtoOVdict[cl].append(OVClasses.index(job["classification"].split(",")[item-1]))
    times = [x for x in job["timeperiod1"].split("-") + job["timeperiod2"].split("-") + job["timeperiod3"].split("-")
             + job["timeperiod4"].split("-") if x != ""]
    d = datetime.datetime.strftime(job["surveydate"],"%Y-%m-%d")
    for siteNo, siteDetails in job["sites"].items():
        site = {}
        #print("site details",siteDetails)
        site["siteNo"] = int(siteNo)
        site["movements"] = {}

        for movement, original in siteDetails.items():
            #print("processing site",siteNo,"movement",movement)
            mvt = {}
            mvt["movementNo"] = movement
            mvt["data"] = [[], [], [], [], [], []]
            mvt["summary"] = {}
            mvt["summary"]["OVTotal"] = 0
            mvt["summary"]["ANPRTotal"] = 0
            mvt["summary"]["AvgCapture"] = 0
            mvt["summary"]["MinCapture"] = 1000
            mvt["summary"]["MaxCapture"] = 0
            mvt["summary"]["TimeLessThan"] = 0
            site["movements"][movement] = mvt
            ANPRdata  = []
            OVdata = []
            for i in range(0, len(times) - 1, 2):
                result = get_OV_data(job,movement,times[i],times[i+1])
                for item in result:
                    OVdata.append(item)

            ###
            ### set up the OVdata for display
            ###

            newList = []
            first = True
            rowList = []
            for i, item in enumerate(OVdata):
                # print("processing item", item, "time fs", item[0])
                t = datetime.datetime.strptime(item[0], "%H:%M:%S")
                mvt["summary"]["OVTotal"] = mvt["summary"]["OVTotal"] + int(sum(item[1:]))
                if t.minute == 0 and not first:
                    rowList = [int(sum(r)) for r in zip(*rowList)]
                    rowList.insert(0, "1 Hr")
                    newList.append(list(rowList))
                    rowList = []
                first = False
                rowList.append(list(item[1:]))
                newList.append(list(item))
            rowList = [int(sum(r)) for r in zip(*rowList)]
            rowList.insert(0, "1 Hr")
            newList.append(list(rowList))
            OVdata = newList
            mvt["data"][0] = OVdata
            mvt["data"][1] = list(OVdata) # the edited version of OVdata, is same as original initally

            for index,combination in enumerate([(0,0),(1,0),(0,1),(1,1)]): #combinations of classed,unclassed,duplicates,etc
                a,b = combination
                ANPRdata = []
                for t in range(0, len(times) - 1, 2):
                    result = get_ANPR_data(job, movement, times[t], times[t + 1], a, b)
                    for item in result:
                        ANPRdata.append(item)

                ###
                ### set up ANPR data for display
                ###

                newList = []
                first = True
                rowList = []  ### holds the blocks of data that we want to sum by column
                for i, item in enumerate(ANPRdata):
                    # print("processing",item)
                    t = datetime.datetime.strptime(item[0], "%H:%M:%S")
                    if t.minute == 0 and not first:
                        rowList = [int(sum(r)) for r in zip(*rowList)]
                        rowList.insert(0, "1 Hr")
                        newList.append(list(rowList))
                        rowList = []
                    first = False
                    mvt["summary"]["ANPRTotal"] = mvt["summary"]["ANPRTotal"] + item[-1]
                    rowList.append(list(item[1:]))
                    newList.append(list(item))
                    # print("newlist is",newList)
                rowList = [int(sum(r)) for r in zip(*rowList)]
                rowList.insert(0, "1 Hr")
                newList.append(list(rowList))
                ANPRdata = newList
                mvt["data"][2+index] = ANPRdata
            mvt["summary"]["TimeLessThan"] = datetime.timedelta(
                seconds=mvt["summary"]["TimeLessThan"] * job["interval"] * 60)
            if mvt["summary"]["OVTotal"] != 0:
                # print("ovtotal",site["summary"]["OVTotal"])
                mvt["summary"]["AvgCapture"] = int(
                    mvt["summary"]["ANPRTotal"] * 100 / mvt["summary"]["OVTotal"])
        results.append(site)
    print("finished processing")
    with open(job["folder"] + '/comparisondata.pkl', 'wb') as handle:
        pickle.dump(results, handle)
    return results

def get_ANPR_data(job,movement,startTime,endTime,classed,duplicates_removed):
    ANPRdata = []
    d = datetime.datetime.strftime(job["surveydate"], "%Y-%m-%d")
    mask = "newMovement == " + str(movement)
    seen = set()
    ANPRClasses = [x for i, x in enumerate(job["classification"].split(",")) if i % 2 == 1 and x not in seen and not seen.add(x)]
    ANPRFrames = []  # a list of lists, 1 list for each ANPR class, each list is the count of that class for each timeslice
    rng = pd.date_range(d + " " + startTime, d + " " + endTime, freq=str(job["interval"]) + "T", closed="left")
    indexDf = pd.DataFrame(index=rng)
    numRows = len(indexDf)
    tempdf = df[d].query(mask).between_time(startTime, endTime, include_end=False)
    tempdf.sort_index(inplace=True)

    for cl in ANPRClasses:
        ###
        ### find all vehicles of a class cl
        ###
        if classed == True:
            try:
                count = tempdf[tempdf["Class"] == cl]
            except Exception as e:
                count = []
        else:
            count = []
        if len(count) == 0:
            ANPRFrames.append([0] * numRows)  ### if theres no classed data, just build a dummy list of 0's
        else:

            ###
            ### resample the vehicles, giving us a series with the number of vehicles of a given class
            ### for each time sample
            ###


            if duplicates_removed == True:
                #print("before removing", len(count))
                try:
                    count = count[count["Duplicates"] == "N"]
                except TypeError as e:
                    print()
                #print("after removing", len(count))

            count = count.resample(str(job["interval"]) + "T").count()

            ###
            ### we use the indexDf to make sure that any times that have no vehicles are registered
            ### as a 0 for that time period
            ###

            count = indexDf.copy().merge(count, how="left", left_index=True, right_index=True).fillna(0)
            ANPRFrames.append(count["VRN"].values.tolist())


    if not classed:
        ###
        ### we arent looking at classed plates, so just want the total number of vehicles for each time sample
        ### use the indexdf to fill in any time samples where there are no vehicles
        ###

        if duplicates_removed == True:
            #print("before removing", len(tempdf))
            try:
                result = tempdf[tempdf["Duplicates"] == "N"]
                #print("after removing", len(result))
                result = result.resample(str(job["interval"]) + "T").count()
            except TypeError as e:
                result = tempdf.resample(str(job["interval"]) + "T").count()
        else:
            result = tempdf.resample(str(job["interval"]) + "T").count()
        df_filtered = indexDf.copy().merge(result, how="left", left_index=True, right_index=True).fillna(0)
        #print("not classed")
        del df_filtered["Movement"]
        del df_filtered["Class"]
        del df_filtered["Duplicates"]
        del df_filtered["timeDiff"]
        del df_filtered["Site"]
        del df_filtered["newMovement"]
        del df_filtered["dir"]
        #print(df_filtered.head())
    else:

        ###
        ### set up a dataframe based on the time series index, with a column for the total ANPR vehicle counts
        ### to give us the "Total" column for the comparison display
        ###

        sumList = [int(sum(r)) for r in zip(*ANPRFrames)]
        indexDf.reset_index(inplace=True)
        df_filtered = indexDf.copy().merge(pd.DataFrame(sumList), how="left", left_index=True, right_index=True).fillna(0)
        df_filtered.columns = ["Date", "total"]
        df_filtered.set_index(["Date"], inplace=True)


    if len(df_filtered) == 0:
        pass
        ### construct a dummy dataframe if the search returns empty

    ###
    ### insert columns corresponding to ANPR classes, remove unneeded columns
    ###

    for j, cl in enumerate(ANPRClasses):
        ###
        ### ANPRFrames is a list of lists, one list for each class of vehicle. This list has a count of
        ### that vehicle type for each time period. We want to insert this list as a column into the
        ### filtered_df, which currently holds the total number of vehicles for each time period
        ### We insert each list as a column labeled "cl" where cl is the class name, eg car, LGV etc
        ###
        #print(j, "th frame", "lenght", len(ANPRFrames[j]), ANPRFrames[j])
        df_filtered.insert(j, cl, ANPRFrames[j])

    ###
    ### now df_filtered is in the correct structure, a column for each class, and a column for total vehicles
    ### we remove unneeded columns, and produce a list of lists, one list for each time sample
    ###
    #print(df_filtered.head())
    df_filtered.index.name = "Date"
    df_filtered.reset_index(inplace=True)
    df_filtered["Date"] = df_filtered["Date"].dt.strftime("%H:%M:%S")
    for item in df_filtered.values.tolist():
        ANPRdata.append(item)
    return ANPRdata

def get_OV_data(job,movement,startTime,endTime):
    #print("trying to get OC data for movement ",movement)
    d = datetime.datetime.strftime(job["surveydate"], "%Y-%m-%d")
    rng = pd.date_range(d + " " + startTime, d + " " + endTime, freq=str(job["interval"]) + "T", closed="left")
    indexDf = pd.DataFrame(index=rng)
    seen = set()
    OVClasses = [x for i, x in enumerate(job["classification"].split(",")) if i % 2 == 0 and x not in seen and not seen.add(x)]
    OVCounts = overviewDf[d].query("Movement == " + str(movement))
    OVCounts.index.to_datetime(dayfirst=True)
    OVCounts = OVCounts.between_time(startTime, endTime, include_end=False)
    OVCounts.reset_index(inplace=True)
    OVCounts["Date"] = OVCounts["Date"].dt.strftime("%H:%M:%S")
    del OVCounts["Site"]
    del OVCounts["Movement"]
    OVdata = []
    if len(OVCounts) == 0:
        temp = indexDf.copy(deep=True)
        temp.reset_index(inplace=True)
        temp.rename(columns={"index": "Date"}, inplace=True)
        temp["Date"] = temp["Date"].dt.strftime("%H:%M:%S")
        for j, cl in enumerate(OVClasses):
            temp.insert(j + 1, cl, [0] * len(temp))
        temp.insert(j + 1, "total", [0] * len(temp))
        for item in temp.values.tolist():
            OVdata.append(item)
            #print("FIlled OVData is", OVdata)
    else:
        OVCounts["Date"] = pd.to_datetime(
            datetime.datetime.strftime(job["surveydate"], "%Y-%m-%d") + " " + OVCounts["Date"])
        OVCounts.set_index(["Date"], inplace=True)
        OVCounts = indexDf.merge(OVCounts, how="left", left_index=True, right_index=True).fillna(0)
        OVCounts["total"] = OVCounts.sum(axis=1)
        OVCounts.reset_index(inplace=True)
        OVCounts.rename(columns={"index": "Date"}, inplace=True)
        OVCounts["Date"] = OVCounts["Date"].dt.strftime("%H:%M:%S")
        for item in OVCounts.values.tolist():
            OVdata.append(item)
    return OVdata

def reprocess_data(job,OVdata,ANPRdata):
    seen = set()
    ANPRClasses = [x for i, x in enumerate(job["classification"].split(",")) if
                   i % 2 == 1 and x not in seen and not seen.add(x)]
    seen = set()
    OVClasses = [x for i, x in enumerate(job["classification"].split(",")) if
                 i % 2 == 0 and x not in seen and not seen.add(x)]
    ANPRtoOVdict = {}  ### this will hold a dictionary of how we combine the OV classes into the ANPR classes
    for cl in ANPRClasses:
        #print("looing for ", cl)
        ANPRtoOVdict[cl] = []
        for item in [i for i, x in enumerate(job["classification"].split(",")) if x == cl and i % 2 == 1]:
            ANPRtoOVdict[cl].append(OVClasses.index(job["classification"].split(",")[item - 1]))

    rowList = []  ### holds the blocks of data that we want to sum by column
    site ={}
    site["summary"] = {}
    site["summary"]["OVTotal"] = 0
    site["summary"]["ANPRTotal"] = 0
    site["summary"]["AvgCapture"] = 0
    site["summary"]["MinCapture"] = 1000
    site["summary"]["MaxCapture"] = 0
    site["summary"]["TimeLessThan"] = 0


    ###
    ### set up the OVdata for display
    ### OVData already has the row totals , but we need to remove them and recalculate them
    ###

    newList = []
    for i, item in enumerate(OVdata):
        print("processing item",item)

        if item[0] == "1 Hr":
            rowList = [int(sum(r)) for r in zip(*rowList)]
            site["summary"]["OVTotal"] = site["summary"]["OVTotal"] + int(rowList[-1])
            print("OVTotal is",site["summary"]["OVTotal"])
            rowList.insert(0, "1 Hr")
            newList.append(list(rowList))
            rowList = []
        else:
            item[-1] =(int(sum(item[1:-1])))
            rowList.append(list(item[1:]))
            #item.insert(0, timestamp.strftime("%H:%M"))
            newList.append(list(item))

    OVdata = newList


    ###
    ### set up the ANPR data for display
    ###

    for row in ANPRdata:
        if row[0] == "1 Hr":
            site["summary"]["ANPRTotal"] = site["summary"]["ANPRTotal"] + row[-1]

    ###
    ### set up the comparison data for display


    compData = []
    first = True
    for i, row in enumerate(OVdata):
        compRowData = []
        OVrow = row[1:]
        ANPRrow = ANPRdata[i][1:]
        timestamp = row[0]
        #print("ovrow", OVrow, "ANPR row", ANPRrow)
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
                if value < site["summary"]["MinCapture"]:
                    site["summary"]["MinCapture"] = value
                if value > site["summary"]["MaxCapture"]:
                    site["summary"]["MaxCapture"] = value
                if value < 85:
                    site["summary"]["TimeLessThan"] += 1
            compRowData.append(value)
        compRowData.insert(0, timestamp)
        compData.append(compRowData)

    site["summary"]["TimeLessThan"] = datetime.timedelta(seconds=site["summary"]["TimeLessThan"] * job["interval"] * 60)
    if site["summary"]["OVTotal"] != 0:
        #print("ovtotal",site["summary"]["OVTotal"])
        site["summary"]["AvgCapture"] = int(site["summary"]["ANPRTotal"] *100 / site["summary"]["OVTotal"])

    print("site summary is", site["summary"])


    return[OVdata,ANPRdata,compData,site["summary"]]

def set_duplicates(index):
    global df
    if index == -1:
        return
    if index <= 30:
        mask = (df["timeDiff"] <= pd.Timedelta(seconds = index))
    else:
        start = (index -31) * 15
        mask = (df["timeDiff"] < pd.Timedelta(seconds=start + 15))
    df["Duplicates"] = "N"
    df.ix[mask,"Duplicates"] = "Y"
    print("set no of duplicates",len(df[df["Duplicates"] == "Y"]))

def set_new_duplicates_value(index,job):
    ###
    ### index : index of which label was clicked in the window, relating to the time value we want to set for excluding
    ### any duplicates,eg index 0 refers to all duplicates with a time diff of 0, 1 refers to duplicates with a time diff
    ### of 1, etc. Any index over 30 refers to a 15 second chunk of time
    ###
    ### when we are setting a new duplicates value, we need to re-compute the comparison data
    set_duplicates(index)
    compute_comparison_data(job)

file = "C:/Users/NWatson/Desktop/ANPR data/3279-Lon, Oxford_Unclassed_Plates_9d3f3926-36ba-47b2-bda9-70516b735a874085337599898377328 (4).xlsx"
#file = "C:/Users/NWatson/Desktop/ANPR data/test.xlsx" ## cut down version of above file

df = None
overviewDf = None

def test():
    global df,overviewDf
    myDB.set_file("C:/Users/NWatson/PycharmProjects/ANPR/blah.sqlite")
    job = myDB.load_job("3279-LON","A34 Oxford","05/07/16")
    load_job(job)
    load_unclassed_plates(job)
    df.to_csv("dumped.csv")
    exit()
    #data = compute_comparison_data(job)
    with open('filename.pickle', 'rb') as handle:
        data = pickle.load(handle)
    print(data[0])
    exit()
    with open('filename.pickle', 'wb') as handle:
        pickle.dump(data, handle)

    exit()


#test()

win = mainwindow.mainWindow()
win.setCallbackFunction("load unclassed",load_unclassed_plates)
win.setCallbackFunction("load job",load_job)
win.setCallbackFunction("load overview count",load_completed_count)
win.setCallbackFunction("load classed",load_classes)
win.setCallbackFunction("get unclassed comparison",get_comparison_data)
win.setCallbackFunction("reprocess data",reprocess_data)
win.setCallbackFunction("set duplicates",set_new_duplicates_value)
win.mainloop()

#df = pd.read_pickle("pickled.txt")
#d1 = datetime.datetime.strptime("05/07/16 12:00:00","%d/%m/%y %H:%M:%S")
#get_movement_data(1,15,"09:00","16:00")
#print(df["2016-07-05"])
#exit()
#print(df["2016-07-05"].between_time("13:00","16:00").resample("15T").count())
#exit()
#print(df.Movement.unique())
#df["VRN"][df["VRN"]=="T6CBL"] = "OU16EZH"
#df["Movement"][df["VRN"]=="CV52NSZ"] = 2
#df["VRN"][df["VRN"]=="CV52NSZ"] = "Y742BOK"
#counts =df.VRN.value_counts()
#print(counts[counts==2].index)
#print(df[counts[counts==1].index])
#print(df)
#print(df[df[["VRN","Movement"]].duplicated()])
#df.drop_duplicates(["VRN","Movement"],inplace=True)
#print("-"*20)
#counts =df.VRN.value_counts()
#print(df.loc[df["VRN"].isin(counts[counts==2].index)])
#print(df.resample("40S",how="count").head())
#print(df.info())
#get_movement_data(1,15)
#print(df.iloc[1])