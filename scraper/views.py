from django.shortcuts import render
from django.http import HttpResponse

from .models import Mytest, Number
from django.views.decorators.csrf import csrf_exempt

def index(request):
    return render(request, "index.html")

@csrf_exempt  #TODO Remove annotation
def update_counter(request):
    cou = Mytest()
    cou.save()

    cou.save()
    cous = Mytest.objects.all()
    message = 'update successful {}x'.format("test")
    return render(request, "mycounter.html", {"counters": cous})

def sendMethod(request):
    numbers = Number.objects.all()
    if len(numbers) == 0:
        number = Number()
        number.save()
    number = Number.objects.first() #get (maybe new) number, only one number in DB
    oldNumber = number.number

    number.number = request.POST["textfield"]
    number.save()
    return render(request, "number.html", {"oldNumber": oldNumber, "newNumber": number.number, "IO": request.POST["textfield"] })

def tef(request=None):
    pass

#TODO Calculate real votes for selected Session+TOP Pair
def showDiagram(request):
    return render(request, "diagram.html", {"yes": 10, "no": 5, "out": 3})

def getTopsAJAX(request):
    jsons = Json.objects.all() #TODO Check if any, don't load all (Multiple methods here use this)
    if len(jsons) == 0: #Load 
        loadJSONsInDB()
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
