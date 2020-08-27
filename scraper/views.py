from django.shortcuts import render
from django.http import HttpResponse

from .models import Json, JsonCountyPDFLinks

import requests #Load JSONs if necessary
import json #Str -> JSON,
import re #For senats text replacement

#Constant values which are used by the methods
#Can't use "global" variables, because they cannot be accessed
class CONSTS: 
    YES="YES"
    NO="NO"
    ABSTENTION="ABSTENTION"
    #mapping from json county name to actual displayed county name
    COUNTY_DISPLAY_NAME = {
            "baden_wuerttemberg": "Baden-Württemberg",
            "bayern": "Bayern",
            "berlin": "Berlin",
            "brandenburg": "Brandenburg", 
            "bremen": "Bremen",
            "hamburg": "Hamburg",
            "hessen": "Hessen",
            "mecklenburg_vorpommern": "Mecklenburg-Vorpommern",
            "niedersachsen": "Niedersachsen",
            "nordrhein_westfalen": "Nordrhein-Westfalen",
            "rheinland_pfalz": "Rheinland-Pfalz",
            "saarland": "Saarland",
            "sachsen": "Sachsen",
            "sachsen_anhalt": "Sachsen-Anhalt",
            "schleswig_holstein": "Schleswig-Holstein",
            "thueringen": "Thüringen",
            }
    #mapping from internal opinion string to actual displayed opinion
    OPINION_DISPLAY_NAME = {
            "YES": "Zustimmung",
            "NO": "Ablehnung",
            "ABSTENTION": "Enthaltung",
            "OTHER": "Nicht ermittelbar",
            }


#Out: List of all SessionNumbers [992, 991,...,910]
def getSessionNumbers():
    brRow = Json.objects.get(county="bundesrat")
    brJSON = json.loads(brRow.json)
    allSessionNumbers = list(map(lambda session: session["number"], brJSON))
    return allSessionNumbers

# function for "/" requests
# Output 1: all session numbers for the search field
# Output 2: latest Session URL for main text
def index(request):
    initDBIfEmpty()

    sessionNumbers = getSessionNumbers()
    latestSessionNumber = max(sessionNumbers)

    URL_LATEST_SESSION="https://www.bundesrat.de/SharedDocs/TO/{}/to-node.html"

    return render(request, "index.html", {"sessionNumbers": sessionNumbers, "urlLatestSession": URL_LATEST_SESSION.format(latestSessionNumber)})

# function for "/metaStudies" requests
# Returns all numbers for the 2 bar charts.
def metaStudies(request):
    initDBIfEmpty()
    numZustimmLaws, numEntscheidungsLaws = getNumberOfLaws()
    numZustimmLawsYES, numZustimmLawsNO, numZustimmLawsTOPRemoval, numZustimmLawsMISSING = getPartitionSizesZustimmLaws()
    sessionNumbers = getSessionNumbers() #For Navbar on result site
    #Need min/max session numbers to show user for which session the Meta-Study applies to
    minSessionNumber = min(sessionNumbers)
    maxSessionNumber = max(sessionNumbers)

    return render(request, "meta.html", {"sessionNumbers": sessionNumbers, "minSessionNumber": minSessionNumber, "maxSessionNumber": maxSessionNumber,  "diagramSumLaws": (numZustimmLaws + numEntscheidungsLaws),  "numZustimmLaws": numZustimmLaws, "numEntscheidungsLaws": numEntscheidungsLaws, "numZustimmLawsYES": numZustimmLawsYES, "numZustimmLawsNO": numZustimmLawsNO, "numZustimmLawsTOPRemoval": numZustimmLawsTOPRemoval,  "numZustimmLawsMISSING": numZustimmLawsMISSING})

# function for "/getTopsAJAX" AJAX requests
# Used when session in search changed
def getTopsAJAX(request):
    initDBIfEmpty()

    #TODO Error if not int
    try:
        sessionNumber = request.GET["sNumber"] # TODO Rename to sessionNumber like `loadJSON` Parameter
    except:
        return HttpResponse("{}", content_type='application/json', status=404) #Doesn't recognize response without content_type, empty JSON shouldn't harm anything, only top selection empty. AJAX call, so no error message

    if not isValidSessionNumber(sessionNumber):
        return HttpResponse("{}", content_type='application/json', status=404) #Doesn't recognize response without content_type, empty JSON shouldn't harm anything, only top selection empty, AJAX call, so no error message

    # Get TOPs for given session
    brRow = Json.objects.get(county="bundesrat")
    brJSON = json.loads(brRow.json)
    for session in brJSON:
        if int(session['number']) == int(sessionNumber):
            allTOPs = list(map(lambda top: {'name': top["number"]}, session["tops"]))
            allTOPs.reverse() #TOP 1 at the start afterwards
            break

    return HttpResponse(json.dumps(allTOPs), content_type='application/json') #Doesn't recognize response without content_type


# function for "/loadJSON" requests
# Returns senats texts and number of opinions and meta data for given TOP of given session
def loadJSON(request):
    initDBIfEmpty()
    sessionNumbers = getSessionNumbers() #Always given to request

    # Get reqeustion session number and TOP
    try:
        sessionNumber = request.GET["sessionNumber"]
    except:
        return render(request, "error.html", {"sessionNumbers": sessionNumbers, "missingSessionNumber": True}, status=404)

    try:
        topNumber = request.GET["topNumber"] #Is Subpart + Number, but name in JSON also topNumber, so leave it
    except:
        return render(request, "error.html", {"sessionNumbers": sessionNumbers, "missingTOPNumber": True}, status=404) #Havent valiaded session number by now, so I shouldn't give it to html file
    if not isValidTOP(sessionNumber, topNumber):
        return render(request, "error.html", {"sessionNumbers": sessionNumbers, "inputSessionNumber": sessionNumber, "inputTOP": topNumber}, status=404) #session number and top could be malformed, so don't give them names currentSessionNumber/currentTOP as this can damage search bar with its parameters

    sessionURL, topTitle, topCategory, topBeschlussTenor = getMetaDataTOP(sessionNumber, topNumber)

    countySenatTextAndOpinionAndPDFLink = getCountiesSenatsTextsData(sessionNumber, topNumber)
    # Count number of different opinions 
    opinions = [opinion for (_, opinion, _) in countySenatTextAndOpinionAndPDFLink.values()] #exctract opinion from map
    numYES, numNO, numABSTENTION, numOTHER = countSizeParitionsOpinions(opinions)
    sessionNumbers = getSessionNumbers()

    return render(request, "json.html", {"diagramNumCounties": len(countySenatTextAndOpinionAndPDFLink), "sessionNumbers": sessionNumbers, "currentSessionNumber": int(sessionNumber), "sessionURL": sessionURL,  "top": topNumber, "topTitle" : topTitle, "topCategory": topCategory, "topTenor": topBeschlussTenor, "countiesTextsAndOpinionsAndPDFLinks": countySenatTextAndOpinionAndPDFLink, "numYes": numYES, "numNo": numNO, "numAbstention": numABSTENTION, "numOther": numOTHER}) #If currentSessionNumber not int, then search bar gets reset to session 992 

#Takes session number and TOP
#Returns True if this session is present
#If malformed parameter(from GET Parameters), also return False
def isValidSessionNumber(sessionNumber):
    #Syntax Check
    if isinstance(sessionNumber, int): #Convert back to string for Dict Key later
        sessionNumber = str(sessionNumber)
    if not isinstance(sessionNumber, str): #Something has wrong type and is therefore malformed
        return False
    if not sessionNumber.isdigit(): #returns true only for strings that represent integers >= 0
        return False #Not a non-negative integer

    #Semantic Check, is sessionnumber present?
    brRow = Json.objects.get(county="bundesrat")
    brJSON = json.loads(brRow.json)
    for session in brJSON:
        if str(session["number"]) == sessionNumber:
            return True
    return False #Nothing found in JSON -> Not present

#Takes session number and TOP
#Returns True if this session contains the TOP
#If malformed parameters(from GET Parameters), also return false
#Don't use isValidSessionNumber() because this would do 2 separate DB calls for isValidSessionNumber() and this function here
def isValidTOP(sessionNumber, topNumber):
    #Syntax Check
    if isinstance(sessionNumber, int): #Convert back to string for Dict Key later
        sessionNumber = str(sessionNumber)
    if isinstance(topNumber, int): #Convert back to string, not needed for subpart TOPs
        topNumber = str(topNumber)
    if not isinstance(sessionNumber, str) or not isinstance(topNumber, str): #Something has wrong type and is therefore malformed
        return False

    if not sessionNumber.isdigit(): #returns true only for strings that represent integers >= 0
        return False #Not a non-negative integer

    #Semantic Check, is TOP present?
    brRow = Json.objects.get(county="bundesrat")
    brJSON = json.loads(brRow.json)
    for session in brJSON:
        if str(session["number"]) == sessionNumber:
            for top in session.get("tops", []): #Default is empty list
                if str(top["number"]) == topNumber: #Sometimes int for number TOPs
                    return True
    return False #Nothing found in JSON -> Not present

# Look up TOP title + category + tenor for given TOP
def getMetaDataTOP(sessionNumber, topNumber):
    brRow = Json.objects.get(county="bundesrat")
    brJSON = json.loads(brRow.json)
    sessionURL = ""
    allTOPs = []
    for session in brJSON:
        if int(session['number']) == int(sessionNumber): 
            sessionURL = session['url']
            for top in session["tops"]:
                if top["number"] == topNumber:
                    topTitle = top['title']
                    topCategory = top.get('law_category', 'Ohne Kategorie')#Zustimmungsbedürftig/Einspruchsgesetz/None
                    topBeschlussTenor = top.get('beschlusstenor', 'Kein Beschlusstenor') #Zustimmung/Versagung der Zustimmung/keine Einberufung des Vermittlungsausschusses/...
                    return sessionURL, topTitle, topCategory, topBeschlussTenor

#Returns Map with key country name and value triple (senat_text, opinion, 
def getCountiesSenatsTextsData(sessionNumber, topNumber):
    countySenatTextAndOpinionAndPDFLink = {}
    allRows = Json.objects.all()
    for row in allRows:
        if row.county == "bundesrat": #bundesrat is no county, skip
            continue 

        # Get Senats Text of given county for given session and top, fallbacks if not present
        countyDBName = row.county
        countyRealName=CONSTS.COUNTY_DISPLAY_NAME[row.county]
        countyJSON = json.loads(row.json)
        countySessionTextsJSON = countyJSON.get(str(sessionNumber), {}) #{} is default, but doesn't like keyword "default"
        countySessionTOPTextsJSON = countySessionTextsJSON.get(str(topNumber), {"senat": "Abstimmungsverhalten nicht öffentlich einsehbar"}) #To keep flow, add "No Text" string as dict (NO PDF - Case)
        NOTHING_FOUND = "Keine Aussage zum Abstimmungsverhalten im entsprechenden Dokument gefunden"
        countySessionTOPSenatsText = countySessionTOPTextsJSON.get("senat", NOTHING_FOUND) #PDF there, but nothing for TOP found - Case
        countySessionTOPSenatsText = countySessionTOPSenatsText if (countySessionTOPSenatsText.strip() != "")  else NOTHING_FOUND #Different case with same results

        #get opinion from senats text
        opinion = extractOpinionSenatsText(countySessionTOPSenatsText)
        opinionDisplayName = CONSTS.OPINION_DISPLAY_NAME.get(opinion, CONSTS.OPINION_DISPLAY_NAME["OTHER"])

        #get Link to PDF source with this senats text
        pdfLinksAbstimmungsverhaltenRow = JsonCountyPDFLinks.objects.get(county=countyDBName)
        pdfLinksAbstimmungsverhaltenJSON = json.loads(pdfLinksAbstimmungsverhaltenRow.json)
        pdfLinkCountyCurrentSession = pdfLinksAbstimmungsverhaltenJSON.get(str(sessionNumber), "") #No pdf for county and session ? -> empty link

        # Add triple
        countySenatTextAndOpinionAndPDFLink[countyRealName] = (countySessionTOPSenatsText, opinionDisplayName, pdfLinkCountyCurrentSession)

    return  countySenatTextAndOpinionAndPDFLink

#Returns 4-tuple of the number of the four different results for counties opinion for bar chart
#In: List of display strings opinions of counties
def countSizeParitionsOpinions(opinions):
    # Count number of different opinions 
    numYES = 0
    numNO = 0
    numABSTENTION = 0
    numOTHER = 0
    for opinion in opinions:
        # Counter for bar charts
        if opinion == CONSTS.OPINION_DISPLAY_NAME["YES"]:
            numYES += 1
        elif opinion == CONSTS.OPINION_DISPLAY_NAME["NO"]:
            numNO += 1
        elif opinion == CONSTS.OPINION_DISPLAY_NAME["ABSTENTION"]:
            numABSTENTION += 1
        else: #No PDF or no Text in JSON or can't match string
            numOTHER += 1
    return numYES, numNO, numABSTENTION, numOTHER

#In: some senats text
#Out: Return YES/NO/ABSTENTION if matches keywords TODO Is there an extra/third "Anruf VA" opinion?
#Out: Else return original text
def extractOpinionSenatsText(senatsText):

    #Order important! "keine Zustimmung"(NO) before "Zustimmung" (YES)
    text = senatsText
    text = replaceStringIfSomeMatchWith(text, ["abgesetzt", "Absetzung"], "DONTKNOWOPINION") # 988 7
    text = replaceStringIfSomeMatchWith(text, ["keine zustimmung", "ablehnung", "keine Unterstützung der Ausschussempfehlungen","Keine Unterstützung der Entschließung", "nicht zuzustimmen", "nicht zugestimmt",
        "Nichtfassen der Entschließung" #BAY 981 14
        ], CONSTS.NO )
    text = replaceStringIfSomeMatchWith(text, ["enthaltung", "Absehen von einer Stellungnahme", "enthalten", "Kenntnisnahme der Ausschussverweisung", "Kenntnis zu nehmen", "Kenntnisnahme", "Keine Äußerung", "Keine Stellungnahme", "Von einer Äußerung und einem Beitritt wird abgesehen", "von der Vorlage Kenntnis genommen", "von einer Äußerung und einem Beitritt abzusehen", "hat sich zu dem Verfahren nicht geäußert", "von Äußerung und Beitritt absehen", "Absehen von Stellungnahme", "nicht abzustimmen", "es wird festgestellt, dass der Vermittlungsausschuss nicht angerufen wird" ], CONSTS.ABSTENTION ) #"Enthaltung zur Zustimmung zum Gesetz" exists, so check before YES
    text = replaceStringIfSomeMatchWith(text, 
            [   "keine einwendungen", 
                "hat der Verordnung zugestimmt",
                "Der Verordnung wurde zugestimmt",
                "stimmte dem Gesetz zu",
                "Anrufung des Vermittlungsausschusses nicht verlangt",
                "Einer Überweisung an die Ausschüsse wird nicht widersprochen", #(BB - 949/42) -> Das ist für Gesetzes*entwürfe*, Ausschuss noch vor eigentlicher Gesetzeswahl (Ausschuss != Verfassungsausschuss)  -> YES
                "Keine Anrufung Vermittlungsausschuss", #(SA - 977/1) -> Nur bei Einspruchsgesetzen -> YES
                "Keine Anrufung des Vermittlungsausschusses",
                "Keine Anrufung VA",
                "Keine VA-Anrufung",
                "keine Unterstützung",
                "Keine Anrufung des VA",
                "Zu den Gesetzen einen Antrag auf Anrufung des Vermittlungsausschusses nicht zu stellen",
                "Die Einberufung des Vermittlungsausschusses wurde nicht verlangt",
                "Dem Gesetz wurde einstimmig zugestimmt",
                "Einstimmige Wahl",
                "einstimmig vorschlagsgemäß",
                "Stellungnahme gemäß", #Basically means "agreed to statement"
                "Stellungnahme gem.", 
                "Stellungnahme wie",
                "Stellungnahme entsprechend",
                "Wahl gemäß Vorschlag",
                "einen Antrag auf Anrufung des Vermittlungsausschusses nicht zu stellen",
                "zustimmung",
                "zuzustimmen"
                "zugestimmt",
                "Fassen nach Maßgabe"
                "Wahl von",
                "Freie Hand", #Bremen 988 1a
                "Fassen der Entschließung nach Maßgaben unterstützt",
                "mit den Stimmen Hamburgs zugestimmt",

                "Verweisung in die Ausschüsse", #Next ones exist only for "Gesetzesentwürfe" (e.g. 981 18), not for "Gesetzesbeschlüsse", "Ausschuss" != "Vermittlungsausschuss
                "Ausschussüberweisung",
                "Überweisung an die Ausschüsse",
                "Überweisung in die Ausschüsse",
                "Ausschussüberweisung",
                "Ausschusszuweisung",
                "Die Vorlage wurde an die Ausschüsse zur Beratung überwiesen",

                "Fassen der Entschließung", #SL 973 26
                "Fassung der Entschließung",
                "Entschließung fassen",
                "Annahme der Entschließung",

                "Einbringung", #For "Gesetzesanträge" (985 15)
                "Entsprechend den Anregungen und Vorschlägen zu beschließen",
                "Den Vorlagen ohne Änderung zuzustimmen",
                "Den Gesetzen zuzustimmen",
                "Dem Wahlvorschlag wird zugestimmt", #In the Context of electing people
                "Stellungnahme des Bundesrates unterstützt",
                "Stellungnahme des Bundesrates überwiegend unterstützt",
                "Ein Antrag auf Anrufung des Vermittlungsausschusses lag nicht vor",
                "Ein Antrag auf Anrufung des Vermittlungsausschusses liegt nicht vor", 
                "Es lag kein Antrag auf Anrufung des Vermittlungsaus­schusses vor",
                "Erteilen der Entlastung",
                "Erteilung der Entlastung",
                "Entlastung erteilen",
                "Die Entschließung zu fassen",
                "Entlastung", #SL
                "Die Landesregierung hat dem Benennungsvorschlag zugestimmt",
                "Die Landesregierung hat den Benennungsvorschlägen zugestimmt",
                "Die Landesregierung hat der Verordnung nach Maßgaben zugestimmt",
                "Zuleitung der Verordnung",
                "Entsprechend den Anregungen und Vorschlägen zu beschließen",
                "Dem Gesetz wurde zugestimmt", 
                "Dem Gesetz zuzustimmen"
            ], CONSTS.YES )

    return text

#In: String to match against (Will all be lower cased in the end)
#In: List of strings/words to match
#In: Replacement string if some match in string
#Out: replacement if at least one match, else original
def replaceStringIfSomeMatchWith(inString, toMatchList, replacement):

    toMatchListLC = map(str.lower, toMatchList)

    #Create big regex or with from toMatchList
    regexStr = ".*(" + "|".join(toMatchListLC) + ")"
    regex = re.compile(regexStr)

    if regex.match(inString.lower()): #Find any string from toMatchListLC -> replace
        return replacement
    return inString #Nothing Found, so return original string

#Returns tuple of number of "Zustimmungsbedürfige Gesetze" and "Entscheidungsgesetz" across sessions 910-992
def getNumberOfLaws():
    initDBIfEmpty()
    brRow = Json.objects.get(county="bundesrat")
    brJSON = json.loads(brRow.json)

    numZustimmLaws = 0
    numEntscheidungsLaws = 0
    for session in brJSON:
        for top in session["tops"]:
            topCategory = top.get("law_category", "")
            if topCategory == "Zustimmungsbedürftiges Gesetz":
                numZustimmLaws += 1
            elif topCategory == "Einspruchsgesetz":
                numEntscheidungsLaws += 1
    return (numZustimmLaws, numEntscheidungsLaws)

#Returns 4-tuple of the number of the four different results for Zustimmungsbedürftige Gesetze in the BR
def getPartitionSizesZustimmLaws():
    initDBIfEmpty()
    brRow = Json.objects.get(county="bundesrat")
    brJSON = json.loads(brRow.json)

    numZustimmLawsYES = 0
    numZustimmLawsNO = 0
    numZustimmLawsTOPRemoval = 0 #Not Discussed
    numZustimmLawsMISSING = 0 #No Tenor e.g. 989 2
    #If special string found, increment right number by one
    for session in brJSON:
        for top in session["tops"]:
            topCategory = top.get("law_category", "")
            if topCategory == "Zustimmungsbedürftiges Gesetz":
                tenor = top.get("beschlusstenor", "")
                if tenor in ["Zustimmung; Entschließung", "Zustimmung; Entschließungen", "Feststellung, dass das Gesetz der Zustimmung des Bundesrates mit zwei Dritteln seiner Stimmen bedarf, Zustimmung, Entschließung", "Zustimmung"]:
                    numZustimmLawsYES += 1
                elif tenor in ["Versagung der Zustimmung", "Anrufung des Vermittlungsausschusses", "Stellungnahme"]: #Stellungnahme from 948 1a, seems to be a NO
                    numZustimmLawsNO += 1
                elif tenor in ["Fristeinrede; Absetzung von TO", "Absetzung von TO"]:
                    numZustimmLawsTOPRemoval += 1
                elif  tenor == "":
                    numZustimmLawsMISSING += 1
                else: #Raise Error if one text can't be categorized. Don't do this for senats texts, as there are to many to successfully parse all right now
                    raise Exception('Cannot get opinion from following tenor text: "{}".'.format(tenor))
    return (numZustimmLawsYES, numZustimmLawsNO, numZustimmLawsTOPRemoval, numZustimmLawsMISSING)

#If DB is empty, load JSONs from GitHub repo
def initDBIfEmpty():
    if not Json.objects.exists(): #Table empty -> Load JSONs
        loadSessionJSONsInDB()

    if not JsonCountyPDFLinks.objects.exists(): #Load PDF Link JSONs
        loadJSONsPDFLinksInDB()

# Store Scraped Session JSONs form GitHub Repo in DB
def loadSessionJSONsInDB():
    #Store all counties in DB
    jsonSessionsUrl = "https://raw.githubusercontent.com/okfde/bundesrat-scraper/master/{}/session_tops.json" #Repo link to sessions JSONs
    storeResponsesCountriesInDB(jsonSessionsUrl, Json)

    #bundesrat folder with Session->TOPs mapping extra
    #Minimally different, so own segment
    brUrl = "https://raw.githubusercontent.com/okfde/bundesrat-scraper/master/bundesrat/sessions.json"
    response = loadURL(brUrl)
    storeJSONResponseAsRowInTable(Json, countyName="bundesrat", jsonResponse = response)

def loadJSONsPDFLinksInDB():
    jsonPDFsUrl = "https://raw.githubusercontent.com/okfde/bundesrat-scraper/master/{}/session_urls.json" #Repo link to PDF Links JSONs
    storeResponsesCountriesInDB(jsonPDFsUrl, JsonCountyPDFLinks)

#Used to store PDF Link JSONs as well as Session JSONs
#url with {} placeholder for county name
def storeResponsesCountriesInDB(urlFormatString, TableName):
    for county in CONSTS.COUNTY_DISPLAY_NAME.keys(): #loop over all county names
        countyJsonUrl = urlFormatString.format(county)
        response = loadURL(countyJsonUrl)
        storeJSONResponseAsRowInTable(TableName, county, response)

#Load request for given URL
def loadURL(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception('{} not found'.format(url))
    return response

#Store given JSON from request as new table
def storeJSONResponseAsRowInTable(TableName, countyName, jsonResponse):
    json = jsonResponse.content.decode() #If one doesn't decode bytearray, there is a problem when storing (bytearray) string and rereading it later to json
    rowTable = TableName(county=countyName, json=json) #Init new row
    rowTable.save()
