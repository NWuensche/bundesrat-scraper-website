from django.db import models

#TODO Rename to JsonTexts
class Json(models.Model):
    county = models.TextField("County", default="")
    json = models.TextField("JSON", default="")

class JsonCountyPDFLinks(models.Model):
    county = models.TextField("County", default="")
    json = models.TextField("JSON", default="")
