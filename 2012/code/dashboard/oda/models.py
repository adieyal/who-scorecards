from django.db import models

class Country(models.Model):

    name = models.CharField(max_length=60)
    iso3 = models.CharField(max_length=3)

    class Meta:
        abstract = True

class Recipient(Country):
    
    def __unicode__(self):
        return "%s (%s)" % (self.name, self.iso3)

class GeneralIndicator(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

class CountryIndicator(models.Model):
    country = models.ForeignKey(Recipient)
    indicator = models.ForeignKey(GeneralIndicator)
    year = models.CharField(max_length=4)
    value = models.FloatField()
