from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, RequestFactory

from .views import index,loadJSON,metaStudies, searchTOPTitles #Needs __init__.py in same folder, else error when executing tests
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
        request = self.factory.get("/loadJSON?sessionNumber=992&topNumber=4") #Session 992, TOP 4 is latest TOP with 3 bars none zero and 1 bar zero
        request.user = AnonymousUser()

        response = loadJSON(request)
        self.assertEqual(response.status_code, 200)

        searchHTML = response.content.decode()

        #Test meta data present and correct
        #self.assertTemplateUsed needs more setup (Django test Client), threrefore I check signal strings so that I know right template was used.
        self.assertTrue("TOP 992/4" in searchHTML)
        self.assertTrue("Titel: 320/20 Gesetz zur Verbesserung der Hilfen für Familien bei Adoption (Adoptionshilfe-Gesetz)" in searchHTML)
        self.assertTrue("Kategorie: Zustimmungsbedürftiges Gesetz" in searchHTML)
        self.assertTrue("Beschlusstenor im Bundesrat: Versagung der Zustimmung" in searchHTML)

        #Check some links and texts in table
        self.assertTrue('<a href="https://landesvertretung-brandenburg.de/wp-content/uploads/992_Abstimmungverhalten-BB.pdf">Brandenburg</a>' in searchHTML) #Check link to PDF present
        self.assertTrue('Haltung SL: Enthaltung zum Anrufungsgrund und Zustimmung zum Gesetz' in searchHTML) #Check Text present
        self.assertTrue('<th>Ablehnung</th>' in searchHTML) #Check opinion parsed correctly

        #Check Diagram
        #self.assertContains could check for semanticly same HTML, but this method always raises error for some reason
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
        self.assertTrue('<div class="bar yes" data-value="3"' in searchHTML) #4 counties voted with YES, style floating points change randomly
        self.assertTrue('<div class="bar no" data-value="3"' in searchHTML) #2 counties voted with NO
        self.assertTrue('<div class="bar abstention" data-value="4"' in searchHTML) #4 counties voted with ABSTENTION
        self.assertTrue('<div class="bar other" data-value="6"' in searchHTML) #6 texts couldn't be parsed

    def testSearchResultBothPresentSessionExistsTOPDoesNot(self):
        request = self.factory.get("/loadJSON?sessionNumber=973&topNumber=1337")
        request.user = AnonymousUser()

        response = loadJSON(request)
        self.assertEqual(response.status_code, 404)

        searchHTML = response.content.decode()
        self.assertTrue('Für die Sitzung "973" existiert kein Tagesordnungspunkt "1337". Bitte suchen Sie erneut.' in searchHTML)

    def testSearchResultTOPMissing(self):
        request = self.factory.get("/loadJSON?sessionNumber=973")
        request.user = AnonymousUser()

        response = loadJSON(request)
        self.assertEqual(response.status_code, 404)

        searchHTML = response.content.decode()
        self.assertTrue("Leider wurde kein Tagesordnungspunkt übergeben. Bitte suchen Sie erneut." in searchHTML)

    def testSearchResultSessionMissing(self):
        request = self.factory.get("/loadJSON?topNumber=1")
        request.user = AnonymousUser()

        response = loadJSON(request)
        self.assertEqual(response.status_code, 404)

        searchHTML = response.content.decode()
        self.assertTrue("Leider wurde keine Sitzungsnummer übergeben. Bitte suchen Sie erneut." in searchHTML)

    def testSearchResultSessionAndTOPMissing(self):
        request = self.factory.get("/loadJSON")
        request.user = AnonymousUser()

        response = loadJSON(request)
        self.assertEqual(response.status_code, 404)

        searchHTML = response.content.decode()
        self.assertTrue("Leider wurde keine Sitzungsnummer übergeben. Bitte suchen Sie erneut." in searchHTML)

    def testSearchResultBothPresentSessionMalformed(self):
        request = self.factory.get("/loadJSON?sessionNumber=a&topNumber=1")
        request.user = AnonymousUser()

        response = loadJSON(request)
        self.assertEqual(response.status_code, 404)

        searchHTML = response.content.decode()
        self.assertTrue('Für die Sitzung "a" existiert kein Tagesordnungspunkt "1". Bitte suchen Sie erneut.' in searchHTML)

    def testSearchResultBothPresentTOPMalformed(self):
        request = self.factory.get("/loadJSON?sessionNumber=990&topNumber=a")
        request.user = AnonymousUser()

        response = loadJSON(request)
        self.assertEqual(response.status_code, 404)

        searchHTML = response.content.decode()
        self.assertTrue('Für die Sitzung "990" existiert kein Tagesordnungspunkt "a". Bitte suchen Sie erneut.' in searchHTML)

    def testSearchResultBothPresentSessionTooLow(self):
        request = self.factory.get("/loadJSON?sessionNumber=909&topNumber=1")
        request.user = AnonymousUser()

        response = loadJSON(request)
        self.assertEqual(response.status_code, 404)

        searchHTML = response.content.decode()
        self.assertTrue('Für die Sitzung "909" existiert kein Tagesordnungspunkt "1". Bitte suchen Sie erneut.' in searchHTML)
    
    def testMetaStudies(self):
        request = self.factory.get("/metaStudies")
        request.user = AnonymousUser()

        response = metaStudies(request)
        self.assertEqual(response.status_code, 200)

        metaHTML = response.content.decode()

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


    def testSearchTitlesStringGETParameterMissing(self):
        request = self.factory.get("/searchTOPTitles")
        request.user = AnonymousUser()

        response = searchTOPTitles(request)
        #self.assertEqual(response.status_code, 200)

        searchHTML = response.content.decode()
        self.assertTrue('Leider wurde keine Suchanfrage übergeben. Bitte suchen Sie erneut.' in searchHTML)

    def testSearchTitlesNoResultsForString(self):
        request = self.factory.get("/searchTOPTitles?searchString=Nothing")
        request.user = AnonymousUser()

        response = searchTOPTitles(request)
        self.assertEqual(response.status_code, 200)

        searchHTML = response.content.decode()
        self.assertTrue('Keine Suchergebnisse für "Nothing" gefunden!' in searchHTML)

    def testSearchTitlesSomeResultsForString(self):
        request = self.factory.get("/searchTOPTitles?searchString=620%2F18") #Search 620/18, only one result
        request.user = AnonymousUser()

        response = searchTOPTitles(request)
        self.assertEqual(response.status_code, 200)

        searchHTML = response.content.decode()
        self.assertTrue('620/18 Mitteilung der Kommission an das Europäische Parlament, den Europäischen Rat, den Rat, die Europäische Zentralbank, den Europäischen Wirtschafts- und Sozialausschuss und den Ausschuss der Regionen: Kapitalmarktunion - Zeit für neue Anstrengungen zugunsten konkreter Ergebnisse bei Investitionen, Wachstum und stärkerer Rolle des Euro' in searchHTML)
        self.assertTrue('loadJSON?sessionNumber=974&topNumber=999c' in searchHTML) #Correct redirect link for search
