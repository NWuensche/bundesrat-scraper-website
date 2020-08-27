from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, RequestFactory

from .views import index,loadJSON,metaStudies, getTopsAJAX #Needs __init__.py in same folder, else error when executing tests
from .models import Json, JsonCountyPDFLinks
import json


class Tests(TestCase):

    #Init DB only once, not for every test again
    @classmethod
    def setUpClass(cls):
        factory = RequestFactory()
        request = factory.get("/")
        request.user = AnonymousUser()
        response = index(request)

    #Needed because I have setUpClass, else error
    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.currentSession = 992 #Last BR Session Number, needed for many tests

    def test_DB_setup(self):
        # Check DB Tables
        self.assertEqual(Json.objects.all().count(), 16+1) #16 rows for counties, 1 for bundesrat
        self.assertEqual(JsonCountyPDFLinks.objects.all().count(), 16) 
        #Test all rows are present
        #Website would crash if some table is malformed, so only test some parts
        row = Json.objects.get(county="baden_wuerttemberg")
        rowJSON = json.loads(row.json)
        self.assertEqual(len(rowJSON), self.currentSession - 916 + 1)

        row = Json.objects.get(county="bundesrat")
        rowJSON = json.loads(row.json)
        self.assertEqual(len(rowJSON), self.currentSession -910 + 1) #992-910 + 1 = 83 different sessions

    def testIndexSite(self):
        # Create an instance of a GET request.
        request = self.factory.get("/")
        request.user = AnonymousUser()

        response = index(request)
        self.assertEqual(response.status_code, 200)

        indexHTML = response.content.decode()
        self.assertTrue("Suchen Sie hier nach dem konkreten Abstimmungsverhalten jedes Bundeslandes im Bundesrat" in indexHTML)
        self.assertTrue('<a href="https://www.bundesrat.de/SharedDocs/TO/{}/to-node.html">hier</a>'.format(self.currentSession) in indexHTML) #Check right link to latest session

    def testSearchResultSuccess(self):
        #TODO Test Search Bar
        request = self.factory.get("/loadJSON?sessionNumber=992&topNumber=4") #Session 992, TOP 4 is latest TOP with 3 bars none zero and 1 bar zero
        request.user = AnonymousUser()

        response = loadJSON(request)
        self.assertEqual(response.status_code, 200)

        searchHTML = response.content.decode()

        self.assertTrue('<option value="992" selected>Sitzung 992</option>' in searchHTML) #Check 992 as session selected in search bar

        #Test meta data present and correct
        self.assertTrue("TOP 992/4" in searchHTML)
        self.assertTrue("Titel: 320/20 Gesetz zur Verbesserung der Hilfen für Familien bei Adoption (Adoptionshilfe-Gesetz)" in searchHTML)
        self.assertTrue("Kategorie: Zustimmungsbedürftiges Gesetz" in searchHTML)
        self.assertTrue("Beschlusstenor im Bundesrat: Versagung der Zustimmung" in searchHTML)

        #Check some links and texts in table
        self.assertTrue('<a href="https://landesvertretung-brandenburg.de/wp-content/uploads/992_Abstimmungverhalten-BB.pdf">Brandenburg</a>' in searchHTML) #Check link to PDF present
        self.assertTrue('Haltung SL: Enthaltung zum Anrufungsgrund und Zustimmung zum Gesetz' in searchHTML) #Check Text present
        self.assertTrue('<th>Ablehnung</th>' in searchHTML) #Check opinion parsed correctly

        #Check Diagram
        self.assertTrue('<div class="bar yes" data-value="3"' in searchHTML) #3 counties voted with YES, style floating points change randomly
        self.assertTrue('<div class="bar no" data-value="3"' in searchHTML) #3 counties voted with NO
        self.assertTrue('<div class="bar abstention" data-value="10"' in searchHTML) #10 counties voted with ABSTENTION
        self.assertTrue('<div class="bar other" data-value="0"' in searchHTML) #0 texts couldn't be parsed

    def testSearchResultSuccess2(self):
        request = self.factory.get("/loadJSON?sessionNumber=973&topNumber=25b") #Session 973, TOP 25a is a TOP with all four bars present
        request.user = AnonymousUser()

        response = loadJSON(request)
        self.assertEqual(response.status_code, 200)

        searchHTML = response.content.decode()

        self.assertTrue('<option value="973" selected>Sitzung 973</option>' in searchHTML) #Check 992 as session selected in search bar

        #Test meta data present and correct
        self.assertTrue("TOP 973/25b" in searchHTML)
        self.assertTrue("Titel: 575/18 Entwurf eines Dreizehnten Gesetzes zur Änderung des Bundes-Immissionsschutzgesetzes" in searchHTML)
        self.assertTrue("Kategorie: Ohne Kategorie" in searchHTML)
        self.assertTrue("Beschlusstenor im Bundesrat: Stellungnahme" in searchHTML)

        #Check some links and texts in table
        self.assertTrue('<a href="https://staatskanzlei.hessen.de/sites/default/files/media/abstimmungsverhalten_hessens_in_der_973._sitzung_des_bundesrates.pdf">Hessen</a>' in searchHTML) #Check link to PDF present
        self.assertTrue('Keine Einwendungen gemäß Ausschussempfehlung in Drucksache 575/1/18 Buchst. B Nr. 17.' in searchHTML) #Check Text present
        self.assertTrue('<th>Zustimmung</th>' in searchHTML) #Check opinion parsed correctly

        #Check Diagram
        self.assertTrue('<div class="bar yes" data-value="4"' in searchHTML) #4 counties voted with YES, style floating points change randomly
        self.assertTrue('<div class="bar no" data-value="2"' in searchHTML) #2 counties voted with NO
        self.assertTrue('<div class="bar abstention" data-value="4"' in searchHTML) #4 counties voted with ABSTENTION
        self.assertTrue('<div class="bar other" data-value="6"' in searchHTML) #6 texts couldn't be parsed

    def testSearchResultBothPresentSessionExistsTOPDoesNot(self):
        request = self.factory.get("/loadJSON?sessionNumber=973&topNumber=1337")
        request.user = AnonymousUser()

        response = loadJSON(request)
        self.assertEqual(response.status_code, 404)

        searchHTML = response.content.decode()
        self.assertTrue('Für die Sitzung "973" existiert kein Tagesordnungspunkt "1337". Bitte suchen Sie erneut.' in searchHTML)
        self.assertTrue('<option value="992" selected>Sitzung 992</option>' in searchHTML) #Check 992 as session selected in search bar after error, although 973 is valid session I don't check this at this point, so I don't give it as a parameter to the html file

    def testSearchResultTOPMissing(self):
        request = self.factory.get("/loadJSON?sessionNumber=973")
        request.user = AnonymousUser()

        response = loadJSON(request)
        self.assertEqual(response.status_code, 404)

        searchHTML = response.content.decode()
        self.assertTrue("Leider wurde kein Tagesordnungspunkt übergeben. Bitte suchen Sie erneut." in searchHTML)
        self.assertTrue('<option value="992" selected>Sitzung 992</option>' in searchHTML) #Check 992 as session selected in search bar after error, although 973 is valid session I don't check this at this point, so I don't give it as a parameter to the html file

    def testSearchResultSessionMissing(self):
        request = self.factory.get("/loadJSON?topNumber=1")
        request.user = AnonymousUser()

        response = loadJSON(request)
        self.assertEqual(response.status_code, 404)

        searchHTML = response.content.decode()
        self.assertTrue("Leider wurde keine Sitzungsnummer übergeben. Bitte suchen Sie erneut." in searchHTML)
        self.assertTrue('<option value="992" selected>Sitzung 992</option>' in searchHTML) #Check 992 as session selected in search bar after error

    def testSearchResultSessionAndTOPMissing(self):
        request = self.factory.get("/loadJSON")
        request.user = AnonymousUser()

        response = loadJSON(request)
        self.assertEqual(response.status_code, 404)

        searchHTML = response.content.decode()
        self.assertTrue("Leider wurde keine Sitzungsnummer übergeben. Bitte suchen Sie erneut." in searchHTML)
        self.assertTrue('<option value="992" selected>Sitzung 992</option>' in searchHTML) #Check 992 as session selected in search bar after error

    def testSearchResultBothPresentSessionMalformed(self):
        request = self.factory.get("/loadJSON?sessionNumber=a&topNumber=1")
        request.user = AnonymousUser()

        response = loadJSON(request)
        self.assertEqual(response.status_code, 404)

        searchHTML = response.content.decode()
        self.assertTrue('Für die Sitzung "a" existiert kein Tagesordnungspunkt "1". Bitte suchen Sie erneut.' in searchHTML)
        self.assertTrue('<option value="992" selected>Sitzung 992</option>' in searchHTML) #Check 992 as session selected in search bar after error

    def testSearchResultBothPresentTOPMalformed(self):
        request = self.factory.get("/loadJSON?sessionNumber=990&topNumber=a")
        request.user = AnonymousUser()

        response = loadJSON(request)
        self.assertEqual(response.status_code, 404)

        searchHTML = response.content.decode()
        self.assertTrue('Für die Sitzung "990" existiert kein Tagesordnungspunkt "a". Bitte suchen Sie erneut.' in searchHTML)
        self.assertTrue('<option value="992" selected>Sitzung 992</option>' in searchHTML) #Check 992 as session selected in search bar after error

    def testSearchResultBothPresentSessionTooLow(self):
        request = self.factory.get("/loadJSON?sessionNumber=909&topNumber=1")
        request.user = AnonymousUser()

        response = loadJSON(request)
        self.assertEqual(response.status_code, 404)

        searchHTML = response.content.decode()
        self.assertTrue('Für die Sitzung "909" existiert kein Tagesordnungspunkt "1". Bitte suchen Sie erneut.' in searchHTML)
        self.assertTrue('<option value="992" selected>Sitzung 992</option>' in searchHTML) #Check 992 as session selected in search bar after error
    
    def testMetaStudies(self):
        request = self.factory.get("/metaStudies")
        request.user = AnonymousUser()

        response = metaStudies(request)
        self.assertEqual(response.status_code, 200)

        metaHTML = response.content.decode()

        self.assertTrue('<option value="992" selected>Sitzung 992</option>' in metaHTML) #Check 992 as session selected in search bar

        #Test Title correct
        self.assertTrue("Meta-Analysen der Bundesrats-Sitzungen 910 - {}".format(self.currentSession) in metaHTML)

        #Test first diagram correct
        self.assertTrue('<div class="bar yes" data-value="322"' in metaHTML) #322 zustimmungsbedürftige Gesetze
        self.assertTrue('<div class="bar other" data-value="581"' in metaHTML) #581 Einspruchsgesetze

        # Test second diagram correct
        self.assertTrue('<div class="bar yes" data-value="292"' in metaHTML) #292 Yes
        self.assertTrue('<div class="bar no" data-value="12"' in metaHTML) #12 No
        self.assertTrue('<div class="bar abstention" data-value="8"' in metaHTML) #8 abstained
        self.assertTrue('<div class="bar other" data-value="10"' in metaHTML) #10 No Result published

    def testgetTOPSAJAXSSuccess(self):
        request = self.factory.get("/getTopsAJAX/?sNumber=992")
        request.user = AnonymousUser()

        response = getTopsAJAX(request)
        self.assertEqual(response.status_code, 200)
        topHTML = response.content.decode()

        self.assertTrue(topHTML == '[{"name": "999e"}, {"name": "999d"}, {"name": "999c"}, {"name": "999b"}, {"name": "999a"}, {"name": "88"}, {"name": "87b"}, {"name": "87a"}, {"name": "86"}, {"name": "85"}, {"name": "84"}, {"name": "83"}, {"name": "82"}, {"name": "81"}, {"name": "80"}, {"name": "79"}, {"name": "78"}, {"name": "77"}, {"name": "76"}, {"name": "75b"}, {"name": "75a"}, {"name": "74"}, {"name": "73"}, {"name": "72"}, {"name": "71"}, {"name": "70b"}, {"name": "70a"}, {"name": "69d"}, {"name": "69c"}, {"name": "69b"}, {"name": "69a"}, {"name": "68"}, {"name": "67"}, {"name": "66"}, {"name": "65"}, {"name": "64"}, {"name": "63"}, {"name": "62"}, {"name": "61"}, {"name": "60"}, {"name": "59"}, {"name": "58"}, {"name": "57"}, {"name": "56"}, {"name": "55"}, {"name": "54"}, {"name": "53"}, {"name": "52"}, {"name": "51"}, {"name": "50"}, {"name": "49"}, {"name": "48"}, {"name": "47"}, {"name": "46"}, {"name": "45"}, {"name": "44"}, {"name": "43"}, {"name": "42"}, {"name": "41"}, {"name": "40c"}, {"name": "40b"}, {"name": "40a"}, {"name": "39"}, {"name": "38"}, {"name": "37"}, {"name": "36"}, {"name": "35"}, {"name": "34"}, {"name": "33"}, {"name": "32"}, {"name": "31"}, {"name": "30"}, {"name": "29"}, {"name": "28"}, {"name": "27"}, {"name": "26"}, {"name": "25"}, {"name": "24"}, {"name": "23b"}, {"name": "23a"}, {"name": "22"}, {"name": "21"}, {"name": "20"}, {"name": "19"}, {"name": "18"}, {"name": "17"}, {"name": "16"}, {"name": "15"}, {"name": "14"}, {"name": "13"}, {"name": "12"}, {"name": "11"}, {"name": "10"}, {"name": "9"}, {"name": "8"}, {"name": "7"}, {"name": "6"}, {"name": "5"}, {"name": "4"}, {"name": "3"}, {"name": "2"}, {"name": "1"}]') #Check JSON for Session 992 correct, reversed because django html loop starts from end

    def testgetTOPSAJAXSSuccess2(self):
        request = self.factory.get("/getTopsAJAX/?sNumber=973")
        request.user = AnonymousUser()

        response = getTopsAJAX(request)
        self.assertEqual(response.status_code, 200)
        topHTML = response.content.decode()

        self.assertTrue(topHTML == '[{"name": "47"}, {"name": "46"}, {"name": "45"}, {"name": "44"}, {"name": "43"}, {"name": "42"}, {"name": "41"}, {"name": "40"}, {"name": "39"}, {"name": "38"}, {"name": "37"}, {"name": "36"}, {"name": "35"}, {"name": "34"}, {"name": "33"}, {"name": "32"}, {"name": "31"}, {"name": "30"}, {"name": "29"}, {"name": "28"}, {"name": "27"}, {"name": "26"}, {"name": "25c"}, {"name": "25b"}, {"name": "25a"}, {"name": "24"}, {"name": "23"}, {"name": "22"}, {"name": "21"}, {"name": "20"}, {"name": "19"}, {"name": "18"}, {"name": "17"}, {"name": "16"}, {"name": "15"}, {"name": "14"}, {"name": "13"}, {"name": "12"}, {"name": "11"}, {"name": "10"}, {"name": "9"}, {"name": "8"}, {"name": "7"}, {"name": "6"}, {"name": "5"}, {"name": "4"}, {"name": "3"}, {"name": "2"}, {"name": "1"}]') #Check JSON for Session 973 correct, reversed because django html loop starts from end

    def testgetTOPSAJAXSsNumberMissing(self):
        request = self.factory.get("/getTopsAJAX/")
        request.user = AnonymousUser()

        response = getTopsAJAX(request)
        self.assertEqual(response.status_code, 404)
        topHTML = response.content.decode()
        self.assertTrue(topHTML == "{}") #Empty JSON

    def testgetTOPSAJAXSsNumberWrongType(self):
        request = self.factory.get("/getTopsAJAX/?sNumber=a")
        request.user = AnonymousUser()

        response = getTopsAJAX(request)
        self.assertEqual(response.status_code, 404)
        topHTML = response.content.decode()
        self.assertTrue(topHTML == "{}") #Empty JSON

    def testgetTOPSAJAXSsNumberTooLow(self):
        request = self.factory.get("/getTopsAJAX/?sNumber=909")
        request.user = AnonymousUser()

        response = getTopsAJAX(request)
        self.assertEqual(response.status_code, 404)
        topHTML = response.content.decode()
        self.assertTrue(topHTML == "{}") #Empty JSON
