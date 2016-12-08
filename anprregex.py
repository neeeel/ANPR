

import re

# regular expression like matching for Journeys
#


def build_combinations(l,last):
    ###
    ### takes a list, and returns a list of combinations of that list
    ### eg, for a list [1,2,3,4]
    ### it will return [[1,2],[1,2,3],[1,2,3,4]]
    ###
    ### if last is True, that means that the last item in the list must always be present in the combination
    ### so for the list above, it would return [[1,2,3,4],[2,3,4],[3,4],[4]]
    ###
    result = []
    if last:
        for i in range(0, len(l) - 1):
            if l[i:] not in result:
                result.append(l[i:])
    else:
        for i in range(2,len(l)+1):
            result.append(l[:i])
    return result

def get_all_combinations(data,first=False,last=False):
    ###
    ### data is a list of tuples, each tuple is (movementNo,time,direction)
    ## eg ("7","07:50:16","I"). Each tuple represents the time and site at which a plate was seen
    ### so data represents all the sites and movements at which a particular plate was seen
    ### we want to get all combinations of the data, as this makes it easier to match the regstring
    ###
    ### first indicates that the very first instance of a plate must be matched. similar to regex where you can say that
    ### the match string must appear at the beginning of the string being searched
    ###
    ### last indicates that the very last instance of a plate must be matched, again similar to regex
    ###
    ### this function takes a list, and returns a list of combinations of that list
    ### eg if the list was [1,2,3,4]
    ### it would return [[1,2],[1,2,3],[1,2,3,4],[2,3],[2,3,4],[3,4]]
    ###
    if first and last:
        return [data] ### if first and last are true, we basically want to match the whole journey to the regstring
    combinations = []
    if not first:
        end = len(data)
    else:
        end = 1
    for i in range(0, end):
        result = (build_combinations(data[i:],last))
        [combinations.append(item) for item in result if item not in combinations]
    return combinations

def getSublistIndex(list, sublist,start=0):
    for i in range(len(list)-len(sublist)+1+start):
        if sublist == list[i:i+len(sublist)]:
            return i
    return -1


def match3(data,regstring):
    result = []
    #print("data",data,"regstring",regstring)
    matchstring = [d[1] for d in data]
    matchstring = ",".join(matchstring)
    regex = re.compile(regstring)
    match = regex.finditer(matchstring)
    result = []
    #print(matchstring)
    for m in match:
        start = m.start()
        try:
            s = m.group(1)
        except Exception as e:
            s = m.group()
            print(e)
        print("matched",s)
        if s[0] == ",":
            start+=1
        if s != "," and s != "":
            if s[-1] == ",":
                s = s[:-1]
            if s[0] == ",":
                s = s[1:]
            if s != "":
                length = len(s.split(","))
                commas = matchstring[0:start].count(",")
                result.append(data[commas:commas+length])
    return result

def match2(data,regstring):
    result = []
    #print("data",data,"regstring",regstring)
    matchstring = [d[1] for d in data]
    matchstring = ",".join(matchstring)
    match = re.finditer(regstring,matchstring)
    result = []
    #print(matchstring)
    for m in match:
        start = m.start()
        s = m.group()
        #print("matched",s)
        if s[0] == ",":
            start+=1
        if s != "," and s != "":
            if s[-1] == ",":
                s = s[:-1]
            if s[0] == ",":
                s = s[1:]
            if s != "":
                length = len(s.split(","))
                commas = matchstring[0:start].count(",")
                result.append(data[commas:commas+length])
    return result

def verify(journey,regex):
    ###
    ### this function does the actual matching of the regstring against a journey
    ### journey is a list of tuples, each tuple is (movementNo,time,direction)
    ## eg ("7","07:50:16","I"). Each tuple represents the time and site at which a plate was seen
    ### journey is a (partial) segment of the full journey of a vehicle
    ###
    ### returns True if journey is a match for regex
    ### otherwise False
    ###
    ### Note: this function is recursive
    ###

    #print("received",journey,regex,"length of journey is",len(journey))
    if len(journey)==0 and len(regex)==0:
        return True
    if len(journey)==0 and len(regex)!=0:
        if "*" in regex[0]:
            return verify(journey,regex[1:])
        else:
            return False
    zeroOrMoreFlag = False
    notFlag = False
    matched = False
    for item in regex:
        if "*" in item:
            zeroOrMoreFlag = True
            item = item[:-1]
        if "¬" in item:
            notFlag = True
            item = item[1:]

        if item in ["I","B","O"]:
            #print("checking",journey[0][2] , item)
            if journey[0][2] == item:
                matched = True

        try: #### is it numeric?
            if int(item) !=0:
                if int(journey[0][1]) == int(item):
                    matched = True
        except ValueError as e:
            pass ### regex value wasnt a number

        if "|" in item: ### its a list of numbers(movements) OR'ed together
            numlist = [int(num) for num in item.split("|")]
            if int(journey[0][1]) in numlist:
                matched = True


        if matched:
            if notFlag:
                #print("failed due to not")
                return False
            if len(journey) == 1 and len(regex)==1:
                return True
            else:
                if zeroOrMoreFlag:
                    return verify(journey[1:], regex)
                return verify(journey[1:],regex[1:])
        else:
            if notFlag:
                if len(journey) == 1 and len(regex) == 1:
                    return True
                if zeroOrMoreFlag:
                    return verify(journey[1:], regex)
                return verify(journey[1:], regex[1:])
            if zeroOrMoreFlag:
                return verify(journey,regex[1:])
            #print("failed , token didnt match direction")
            return False





def match(data,regstring):
    matches = []
    #print("-" * 100)
    #print("in match, received",data,"regstring is",regstring,type(regstring))
    first=False
    last= False
    if "^" in regstring:
        #print("detected first")
        first = True
        regstring = regstring.replace("^","")
        #print("regstring is now",regstring)
    if "!" in regstring:
        #print("detected last")
        last = True
        regstring = regstring.replace("!", "")
        #print("regstring is now", regstring)
    for combi in get_all_combinations(data,first=first,last=last):
        #print("checiking combi ",combi)
        tempMatches = []
        if "(" in regstring:
            main = regstring.replace("(", "")
            main = main.replace(")", "")
            #print(main)
            regex = main.split("-")
            if verify(combi, regex):
                #print("-" * 100)
                #print(combi, "True")
                #print("-" * 100)
                main = regstring.split("(")[1]
                main = main.split(")")[0]
                main = main.split("-")
                #print("main is", main)
                for subcombis in get_all_combinations(combi):
                    if verify(subcombis, main):
                        if len(tempMatches) == 0:
                            #print("appending ",subcombis)
                            tempMatches.append(subcombis)
                        else:
                            if not subcombis in tempMatches:
                                if len(subcombis) > len(tempMatches[-1]): ## in case any subset of the subtring matches
                                    #print("changing ", subcombis)
                                    tempMatches[0]=subcombis
                for match in tempMatches:
                    #print("-" * 100)
                    #print(match, "True")
                    #print("-" * 100)
                    matches.append(match)


        else:
            regex = regstring.split("-")
            if verify(combi, regex):
                #print("-" * 100)
                #print(combi, "True")
                if not combi in matches:
                    matches.append(combi)
                #print("-" * 100)
    return matches