from django.db import models

class Mytest(models.Model):
    myfield = models.DateTimeField("my field", auto_now_add=True)

class Number(models.Model):
    number = models.IntegerField("the number", default=0)

class Json(models.Model):
    county = models.TextField("County", default="")
    json = models.TextField("JSON", default="")
