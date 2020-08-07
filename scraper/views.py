from django.shortcuts import render
from django.http import HttpResponse

from .models import Json, JsonCountyPDFLinks

import requests #Load JSONs if necessary
import json #Str -> JSON,
import re #For senats text replacement

class CONSTS: #Can't use "global" vars else
    YES="YES"
    NO="NO"
    ABSTENTION="ABSTENTION"
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
    OPINION_DISPLAY_NAME = {
            "YES": "Zustimmung",
            "NO": "Ablehnung",
            "ABSTENTION": "Enthaltung",
            "OTHER": "Nicht ermittelbar",
            }

#If DB is empty, load stuff
def initDBIfEmpty():
    if not Json.objects.exists(): #Table empty -> Load JSONs
        loadJSONsInDB()

    if not JsonCountyPDFLinks.objects.exists(): #Load 
        loadJSONsPDFLinksInDB()

#Out: List of all SessionNumbers [992, 991,...,910]
def getSessionNumbers():
    brRow = Json.objects.get(county="bundesrat")
    brJSON = json.loads(brRow.json)
    allSessionNumbers = list(map(lambda session: session["number"], brJSON))
    return allSessionNumbers

def index(request):
    initDBIfEmpty()

    sessionNumbers = getSessionNumbers()

    URL_LATEST_SESSION="https://www.bundesrat.de/SharedDocs/TO/{}/to-node.html"
    latestSessionNumber = max(sessionNumbers)

    return render(request, "index.html", {"sessionNumbers": sessionNumbers, "urlLatestSession": URL_LATEST_SESSION.format(latestSessionNumber)})

def metaStudies(request):
    initDBIfEmpty()
    numZustimmLaws, numEntscheidungsLaws = getNumberLaws()
    numZustimmLawsYES, numZustimmLawsNO, numZustimmLawsTOPRemoval, numZustimmLawsMISSING = getPartitionSizesZustimmLaws()
    sessionNumbers = getSessionNumbers() #For Navbar on result site

    #Need them to show where Meta-Study applies to
    minSessionNumber = min(sessionNumbers)
    maxSessionNumber = max(sessionNumbers)

    return render(request, "meta.html", {"sessionNumbers": sessionNumbers, "minSessionNumber": minSessionNumber, "maxSessionNumber": maxSessionNumber,  "diagramSumLaws": (numZustimmLaws + numEntscheidungsLaws),  "numZustimmLaws": numZustimmLaws, "numEntscheidungsLaws": numEntscheidungsLaws, "numZustimmLawsYES": numZustimmLawsYES, "numZustimmLawsNO": numZustimmLawsNO, "numZustimmLawsTOPRemoval": numZustimmLawsTOPRemoval,  "numZustimmLawsMISSING": numZustimmLawsMISSING})

def getTopsAJAX(request):
    initDBIfEmpty()

    sessionNumber = int(request.GET['sNumber'])
    brRow = Json.objects.get(county="bundesrat")
    brJSON = json.loads(brRow.json)
    for session in brJSON:
        if int(session['number']) == sessionNumber:
            allTOPs = list(map(lambda top: {'name': top["number"]}, session["tops"]))
            allTOPs.reverse() #TOP 1 at the start afterwards
            break
    return HttpResponse(json.dumps(allTOPs), content_type='application/json') #Doesn't recognize without content_type

def loadJSONsInDB():
    counties = [
            "baden_wuerttemberg",
            "bayern",
            "berlin",
            "brandenburg", 
            "bremen",
            "hamburg",
            "hessen",
            "mecklenburg_vorpommern",
            "niedersachsen",
            "nordrhein_westfalen",
            "rheinland_pfalz",
            "saarland",
            "sachsen",
            "sachsen_anhalt",
            "schleswig_holstein",
            "thueringen",
            ]
    jsonUrl = "https://raw.githubusercontent.com/okfde/bundesrat-scraper/master/{}/session_tops.json"
    for county in counties:
        countyJsonUrl = jsonUrl.format(county)
        response = requests.get(countyJsonUrl)
        if response.status_code != 200:
            raise Exception('{} not found'.format(countyJsonUrl))
        #TODO rename county attribute
        countyDBRow = Json(county = county, json = response.content.decode()) #If not decode bytearraw, then problem when storing (bytearray) string and rereading it to json
        countyDBRow.save()
    
    #bundesrat folder with Session->TOPs mapping extra
    brUrl = "https://raw.githubusercontent.com/okfde/bundesrat-scraper/master/bundesrat/sessions.json"
    #TODO remove double code
    response = requests.get(brUrl)
    if response.status_code != 200:
        raise Exception('{} not found'.format(brUrl))
    #TODO rename county attribute
    brDBRow = Json(county = "bundesrat", json = response.content.decode()) #If not decode bytearraw, then problem when storing (bytearray) string and rereading it to json
    brDBRow.save()

#TODO Merge with loadJSONsInDB, but no bundesrat folder used here
def loadJSONsPDFLinksInDB():
    counties = [
            "baden_wuerttemberg",
            "bayern",
            "berlin",
            "brandenburg", 
            "bremen",
            "hamburg",
            "hessen",
            "mecklenburg_vorpommern",
            "niedersachsen",
            "nordrhein_westfalen",
            "rheinland_pfalz",
            "saarland",
            "sachsen",
            "sachsen_anhalt",
            "schleswig_holstein",
            "thueringen",
            ]
    jsonUrl = "https://raw.githubusercontent.com/okfde/bundesrat-scraper/master/{}/session_urls.json"
    for county in counties:
        countyJsonUrl = jsonUrl.format(county)
        response = requests.get(countyJsonUrl)
        if response.status_code != 200:
            raise Exception('{} not found'.format(countyJsonUrl))
        #TODO rename county attribute
        countyDBRow = JsonCountyPDFLinks(county = county, json = response.content.decode()) #If not decode bytearraw, then problem when storing (bytearray) string and rereading it to json
        countyDBRow.save()

def loadJSON(request):
    initDBIfEmpty()
    sessionNumber = int(request.GET["sessionNumber"])
    topNumber = request.GET["topNumber"] #TODO Is Subpart + Number , should rename JS Parameter
    brRow = Json.objects.get(county="bundesrat")
    brJSON = json.loads(brRow.json)
    sessionURL = ""
    allTOPs = []
    for session in brJSON:
        if int(session['number']) == sessionNumber:
            sessionURL = session['url']
            for top in session["tops"]:
                if top["number"] == topNumber:
                    topTitle = top['title']
                    topCategory = top.get('law_category', 'Ohne Kategorie')#Zustimmungsbedürftig/Einspruchsgesetz/None
                    topBeschlussTenor = top.get('beschlusstenor', 'Kein Beschlusstenor') #Zustimmung/Versagung der Zustimmung/keine Einberufung des Vermittlungsausschusses/...
            break
    numYES = 0
    numNO = 0
    numABSTENTION = 0
    numOTHER = 0
    countySenatTextAndOpinionAndPDFLink = {}
    allRows = Json.objects.all()
    for row in allRows:
        if row.county == "bundesrat": #TODO besser
            continue #already processed
        countyDBName = row.county
        countyRealName=CONSTS.COUNTY_DISPLAY_NAME[row.county]
        countyJSON = json.loads(row.json)
        countySessionTextsJSON = countyJSON.get(str(sessionNumber), {}) #{} is default, but doesn't like keyword "default"
        countySessionTOPTextsJSON = countySessionTextsJSON.get(str(topNumber), {"senat": "Abstimmungsverhalten nicht öffentlich einsehbar"}) #To keep flow, add "No Text" string as dict (NO PDF - Case)
        NOTHING_FOUND = "Keine Aussage zum Abstimmungsverhalten im entsprechenden Dokument gefunden"
        countySessionTOPSenatsText = countySessionTOPTextsJSON.get("senat", NOTHING_FOUND) #PDF there, but nothing for TOP found - Case
        countySessionTOPSenatsText = countySessionTOPSenatsText if (countySessionTOPSenatsText.strip() != "")  else NOTHING_FOUND
        opinion = extractOpinionSenatsText(countySessionTOPSenatsText)

        # Counter for diagram
        if opinion == CONSTS.YES:
            numYES += 1
        elif opinion == CONSTS.NO:
            numNO += 1
        elif opinion == CONSTS.ABSTENTION:
            numABSTENTION += 1
        else: #No PDF or no Text in JSON or can't match string
            numOTHER += 1
        opinionDisplayName = CONSTS.OPINION_DISPLAY_NAME.get(opinion, CONSTS.OPINION_DISPLAY_NAME["OTHER"])

        pdfLinksAbstimmungsverhaltenRow = JsonCountyPDFLinks.objects.get(county=countyDBName)
        pdfLinksAbstimmungsverhaltenJSON = json.loads(pdfLinksAbstimmungsverhaltenRow.json)
        pdfLinkCountyCurrentSession = pdfLinksAbstimmungsverhaltenJSON.get(str(sessionNumber), "") #No pdf for county and session ? -> empty link

        countySenatTextAndOpinionAndPDFLink[countyRealName] = (countySessionTOPSenatsText, opinionDisplayName, pdfLinkCountyCurrentSession)

    sessionNumbers = getSessionNumbers() #For Navbar on result site

    return render(request, "json.html", {"diagramNumCounties": len(countySenatTextAndOpinionAndPDFLink), "sessionNumbers": sessionNumbers, "currentSessionNumber": sessionNumber, "sessionURL": sessionURL,  "top": topNumber, "topTitle" : topTitle, "topCategory": topCategory, "topTenor": topBeschlussTenor, "countiesTextsAndOpinionsAndPDFLinks": countySenatTextAndOpinionAndPDFLink, "numYes": numYES, "numNo": numNO, "numAbstention": numABSTENTION, "numOther": numOTHER})

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
    text = replaceStringIfSomeMatchWith(text, ["enthaltung", "Absehen von einer Stellungnahme", "enthalten", "Kenntnisnahme der Ausschussverweisung", "Kenntnis zu nehmen", "Kenntnisnahme", "Keine Äußerung", "Keine Stellungnahme", "Von einer Äußerung und einem Beitritt wird abgesehen", "von der Vorlage Kenntnis genommen", "von einer Äußerung und einem Beitritt abzusehen", "hat sich zu dem Verfahren nicht geäußert", "von Äußerung und Beitritt absehen" ], CONSTS.ABSTENTION ) #"Enthaltung zur Zustimmung zum Gesetz" exists, so check before YES
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
                "einen Antrag auf Anrufung des Vermittlungsausschusses nicht zu stellen",
                "zustimmung",
                "zuzustimmen",
                "zugestimmt",
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
                "Erteilen der Entlastung",
                "Erteilung der Entlastung",
                "Entlastung erteilen",
                "Die Entschließung zu fassen",
                "Entlastung", #SL
                "Die Landesregierung hat dem Benennungsvorschlag zugestimmt",
                "Die Landesregierung hat den Benennungsvorschlägen zugestimmt",
                "Die Landesregierung hat der Verordnung nach Maßgaben zugestimmt",
                "Zuleitung der Verordnung",
                "Dem Gesetz wurde zugestimmt", 
                "Dem Gesetz zuzustimmen"
            ], CONSTS.YES )

    return text

#In: String to match against (Will all be lower cased in the end)
#In: List of strings/words to match
#In: Replacement string if some match in string
#Out: replacement if match, else original
def replaceStringIfSomeMatchWith(inString, toMatchList, replacement):

    toMatchListLC = map(str.lower, toMatchList)

    #Create big regex or with from toMatchList
    regexStr = ".*(" + "|".join(toMatchListLC) + ")"
    regex = re.compile(regexStr)

    if regex.match(inString.lower()): #Find any string from toMatchListLC -> replace
        return replacement
    return inString #Nothing Found, so return original string

#Returns tuple of number of "Zustimmungsbedürfige Gesetze" and "Entscheidungsgesetz" across sessions 910-992
def getNumberLaws():
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

#Returns 4-tuple of size of Results of Zustimmungsbedürftige Gesetze
def getPartitionSizesZustimmLaws():
    initDBIfEmpty()
    brRow = Json.objects.get(county="bundesrat")
    brJSON = json.loads(brRow.json)

    numZustimmLawsYES = 0
    numZustimmLawsNO = 0
    numZustimmLawsTOPRemoval = 0 #Not Discussed
    numZustimmLawsMISSING = 0 #No Tenor e.g. 989 2
    for session in brJSON:
        for top in session["tops"]:
            topCategory = top.get("law_category", "")
            if topCategory == "Zustimmungsbedürftiges Gesetz":
                tenor = top.get("beschlusstenor", "")
                if tenor in ["Zustimmung; Entschließung", "Zustimmung; Entschließungen", "Zustimmung"]:
                    numZustimmLawsYES += 1
                elif tenor in ["Versagung der Zustimmung", "Anrufung des Vermittlungsausschusses", "Stellungnahme"]: #Stellungnahme from 948 1a, seems to be a NO
                    numZustimmLawsNO += 1
                elif tenor in ["Fristeinrede; Absetzung von TO", "Absetzung von TO"]: 
                    numZustimmLawsTOPRemoval += 1
                elif  tenor == "":
                    numZustimmLawsMISSING += 1
    return (numZustimmLawsYES, numZustimmLawsNO, numZustimmLawsTOPRemoval, numZustimmLawsMISSING)

