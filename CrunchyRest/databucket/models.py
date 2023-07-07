from djongo import models

# Create your models here.


class Crunchbase(models.Model):
    _id = models.ObjectIdField()
    name = models.TextField()
    funding = models.TextField()
    website = models.URLField()
    crunchbase_url = models.URLField()
    logo = models.URLField()
    founders = models.JSONField(default=[])
    similar_companies = models.JSONField(default=[])
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    long_description = models.TextField()
    acquired = models.TextField()
    industries = models.JSONField(default=[])
    founded = models.TextField()
    lastfunding = models.TextField()
    stocksymbol = models.TextField()
