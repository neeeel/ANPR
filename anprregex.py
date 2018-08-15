

import re

# regular expression like matching for Journeys
#

def sublistExists(list, sublist):
    if list==sublist:
        return -1
    for i in range(len(list)-len(sublist)+1):
        if sublist == list[i:i+len(sublist)]:
            return i
    return -1

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
    if list==sublist:
        return False
    for i in range(len(list)-len(sublist)+1+start):
        if sublist == list[i:i+len(sublist)]:
            return True
    return False


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
    first = False
    last  = False
    if "^" in regstring:
        first = True
        regstring = regstring.replace("^", "")
    if "!" in regstring:
        last = True
        regstring = regstring.replace("!", "")
    if "(" in regstring:
        #print(regstring.replace("-",""))
        start = regstring.replace("-","").index("(")
        end = regstring.replace("-","").index(")")
        #print("start",start,end)
        main = regstring.replace("(", "")
        main = main.replace(")", "")
        regex = main.split("-")
        matches = verify2(data,regex,first=first,last=last)
        if last:
            matches = [match for match in matches if match[-1] == data[-1]]
        matches = [match[start:end-1] for match in matches]
    else:
        regex = regstring.split("-")
        matches = verify2(data, regex, first=first,last=last)
        if last:
            matches = [match for match in matches if match[-1] == data[-1]]
    matches = [m for m in matches if len(m) > 1]
    remainders  = []
    segmentStart = 0
    for start, end in [[data.index(m[0]), data.index(m[-1])] for m in matches]:
        #print(segmentStart,start,end)
        remainders.append(data[segmentStart:start])
        segmentStart = end + 1
    #print(segmentStart, start, end)
    remainders.append(data[segmentStart:len(data)])
    remainders = [r for r in remainders if len(r) > 1]
    #print("remainders are", remainders)
    #print("matches are", matches)
    return [matches,remainders]



def verify2(fullJourney,fullRegex,first=False,last=False):
    ###
    ### this function does the actual matching of the regstring against a journey
    ### journey is a list of tuples, each tuple is (movementNo,time,direction)
    ## eg ("7","07:50:16","I"). Each tuple represents the time and site at which a plate was seen
    ###  in this verify, we are looking at the whole journey, and seeing if a subset of it matches the regex
    ###
    ### returns finish indexes of match
    ### otherwise None
    ###
    ### Note: this function is NOT recursive
    ###
    start = 0
    i = 0

    matches = []
    while i <len(fullJourney):
       #print("fulljouorney is",fullJourney)
        if first and i > 0:
            return matches
        start = i
        regex = fullRegex
        journey = fullJourney[i:]
        finish = i
        while len(regex) > 0:
            #print("received", journey, regex, "length of journey is", len(journey),start,finish)
            if len(journey)==0:
                if (len(regex)==1 and "*" in regex[0] and finish-start>1):
                    matches.append(fullJourney[start:finish + 1])
                    #print("found match from", start, "to", finish)
                    i = finish + 1
                    break
                if len(regex)>1 and "*" in regex[0]:
                    regex = regex[1:]
                    continue
                else:
                    i += 1
                    regex = ""
                    break
            zeroOrMoreFlag = False
            notFlag = False
            matched = False
            anythingFlag = False
            item = regex[0]
            #print("item is",item)
            if "*" in item:
                zeroOrMoreFlag = True
                item = item[:-1]
            else:
                zeroOrMoreFlag = False
            if "¬" in item:
                notFlag = True
                item = item[1:]
            else:
                notFlag = False
            if item == "A":
                ###
                ### if zeroOrMoreFlag is not true, we can just match to anything
                if not zeroOrMoreFlag:
                    matched = True
                else:
                    ###
                    ### if it is true, we need to look at the next token, since we want to match anything
                    ### except something that matches the next token
                    ###
                    if len(regex) == 1:
                        ### if the A* is the last item in the regex, we just match everything
                        #print("a wibble",regex,journey)
                        matched = True
                    else:
                        ### otherwise, replace current token with the next token, set
                        ### and set anythingFlag to true because we need to do different things on a match
                        ###
                        item = regex[1]
                        item = item.replace("*","")
                        anythingFlag = True
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


            if (matched != notFlag): ### same as XOR
                #print("matched, zeroormoreflag is",zeroOrMoreFlag)
                finish += 1
                journey = journey[1:]
                if anythingFlag:
                    ### if anythingflag is true , that means that the current journey segment has matched the NEXT
                    ### token in the regex, and the current token is A*
                    ###
                    if len(regex) == 2:
                        ###
                        ### if len(regex) is 2, then we have matched the current journey segment to the last item
                        ### in the regex, so we can set this as a matched journey
                        matches.append(fullJourney[start:finish])
                        #print("0-found match from", start, "to", finish)
                        i = finish
                        break
                    else:
                        ###
                        ### we have found the end of an A* sequence, but there are more things to match, so chop off
                        ### the A* and the matched token, and continue on
                        regex = regex[2:]
                        continue
                if len(regex)==1:
                    ### we are on the last token
                    if not zeroOrMoreFlag:
                        ###
                        ### we have matched the last token to something, add the match
                        matches.append(fullJourney[start:finish])
                        #print("1-found match from",start,"to",finish)
                        i = finish
                        break
                else:
                    if not zeroOrMoreFlag:
                        ## only consume a token if its not a zero or more.
                        regex =regex[1:]
            else:
                if zeroOrMoreFlag:
                    if anythingFlag:
                        ### if anythingFlag is true and we didnt match , that means we didnt match the
                        ### NEXT regex token to the current journey segment, this means we can continue because we havent
                        ### found an end point, and we are still matching A*, so move to next journey segment
                        journey = journey[1:]
                        finish+=1
                        continue
                    if len(regex) == 1:
                        matches.append(fullJourney[start:finish])
                        #print("2-found match from", start, "to", finish,fullJourney[start:finish])
                        i = finish
                        break
                    regex = regex[1:]
                    continue
                #print("failed , token didnt match direction")
                ### reach here, and the match has failed
                regex=""
                i+=1
                break
    return matches

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

    print("received",journey,regex,"length of journey is",len(journey))
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
        print("item is",item)
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
        if item == "A":
            ###
            ### does the current regex minus the A match the rest of the journey?
            if zeroOrMoreFlag:
                if verify(journey,regex[1:]):
                    return True
            if verify(journey[1:],regex[1:]):
                print("yes it does")
                return True
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
            #print("matched, zeroormoreflag is",zeroOrMoreFlag)
            if notFlag:
                #print("failed due to not")
                return False
            if len(journey) == 1 and len(regex)==1:
                return True
            else:
                if zeroOrMoreFlag:
                    #print("retrying with",journey[1:],regex)
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

    print(matches)
    #return matches
    finalMatches = []
    for index, item in enumerate(matches):
        print(item)
        for itemToCompare in matches[index:]:
            print("comparing", item, "with", itemToCompare)
            result = sublistExists(itemToCompare, item)
            print("sublist exists at ",result)
            if result != -1:
                print("replacing",item,itemToCompare)
                matches[index + result] = itemToCompare
                item = itemToCompare

    matches = list(reversed(matches))
    for index, item in enumerate(matches):
        print(item)
        for itemToCompare in matches[index:]:
            print("comparing", item, "with", itemToCompare)
            result = sublistExists(itemToCompare, item)

            if result != -1:
                print("replacing in second ", item, itemToCompare)
                matches[index + result] = itemToCompare
                item = itemToCompare


    result = []
    [result.append(item) for item in matches if not item in result]
    return result

def split_list(fullList,partial):
    start = fullList.index(partial[0])
    end = fullList.index(partial[-1])
    p1 = list(fullList[:start])
    p2 = list(fullList[end+1:])
    return[p for p in [p1,p2] if len(p) > 1]



#result = []
journey = [('17:37:25', '3', 'B'),('17:40:25', '4', 'O'), ('17:46:31', '3', 'B'), ('17:52:48', '4', 'I'), ('18:46:31', '3', 'I'), ('18:52:48', '4', 'O')]
filters = ["(B-O-B)-I","I-I"]
for f in filters:
    matches,rem = match2(journey, f)
    print(matches,rem)
#remainders = []
#for f in filters:
#    print("trying filter",f)
#    matches,rem = match2(journey, f)
#    print(matches)
#    bbbb = [["a", "b"] + [item[1], item[0]] for m in matches for item in m]
#print(bbbb)
