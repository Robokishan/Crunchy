from djongo import models

# Create your models here.


class Crunchbase(models.Model):
    """Raw scraped data from Crunchbase."""
    _id = models.ObjectIdField()
    name = models.TextField()
    funding = models.TextField()
    funding_usd = models.FloatField()
    rate = models.FloatField()
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
    # NEW: normalized domain for entity matching
    normalized_domain = models.TextField(null=True, blank=True)
    # True when a TracxnRaw with same normalized_domain exists (for analytics: False = CB-only)
    merged_with_tracxn = models.BooleanField(default=False)

    objects = models.DjongoManager()

    class Meta:
        indexes = [
            models.Index(fields=['normalized_domain']),
            models.Index(fields=['merged_with_tracxn']),
        ]


class InterestedIndustries(models.Model):
    _id = models.ObjectIdField()
    industries = models.JSONField(default=[])
    key = models.TextField()

    objects = models.DjongoManager()


class TracxnRaw(models.Model):
    """Raw scraped data from Tracxn."""
    _id = models.ObjectIdField()
    name = models.TextField()
    tracxn_url = models.URLField()
    website = models.URLField(null=True, blank=True)
    normalized_domain = models.TextField(null=True, blank=True)
    funding_total = models.TextField(null=True, blank=True)
    funding_total_usd = models.FloatField(default=0)
    funding_rounds = models.JSONField(default=list)
    founders = models.JSONField(default=list)
    description = models.TextField(null=True, blank=True)
    logo = models.URLField(null=True, blank=True)
    founded = models.TextField(null=True, blank=True)
    hq_location = models.TextField(null=True, blank=True)
    matched = models.BooleanField(default=False)
    # True when a Crunchbase with same normalized_domain exists (for analytics: False = Tracxn-only)
    merged_with_crunchbase = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.DjongoManager()

    class Meta:
        indexes = [
            models.Index(fields=['normalized_domain']),
            models.Index(fields=['matched']),
            models.Index(fields=['merged_with_crunchbase']),
        ]


class Company(models.Model):
    """Golden record -- merged from multiple sources."""
    _id = models.ObjectIdField()
    name = models.TextField()
    normalized_domain = models.TextField(null=True, blank=True)
    website = models.URLField(null=True, blank=True)

    # Source linkage
    crunchbase_url = models.URLField(null=True, blank=True)
    tracxn_url = models.URLField(null=True, blank=True)
    match_confidence = models.FloatField(default=1.0)

    # From Crunchbase (primary for these fields)
    industries = models.JSONField(default=list)
    similar_companies = models.JSONField(default=list)
    description = models.TextField(null=True, blank=True)
    long_description = models.TextField(null=True, blank=True)

    # From Tracxn (primary for these fields)
    funding_total_usd = models.FloatField(default=0)
    funding_rounds = models.JSONField(default=list)
    last_funding_date = models.TextField(null=True, blank=True)
    last_funding_type = models.TextField(null=True, blank=True)

    # Common fields (take from whichever is more complete)
    founders = models.JSONField(default=list)
    logo = models.URLField(null=True, blank=True)
    founded = models.TextField(null=True, blank=True)
    acquired = models.TextField(null=True, blank=True)
    stocksymbol = models.TextField(null=True, blank=True)

    # Provenance tracking
    sources = models.JSONField(default=list)  # ["crunchbase", "tracxn"]
    source_priority = models.JSONField(default=dict)  # per-field source tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.DjongoManager()

    class Meta:
        indexes = [
            models.Index(fields=['normalized_domain']),
        ]


class MatchQueue(models.Model):
    """Low-confidence matches for manual review."""
    _id = models.ObjectIdField()
    crunchbase_id = models.TextField()
    tracxn_id = models.TextField()
    confidence = models.FloatField()
    match_signals = models.JSONField(default=dict)  # which signals matched
    status = models.TextField(default='pending')  # pending, approved, rejected
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.DjongoManager()

    class Meta:
        indexes = [
            models.Index(fields=['status']),
        ]


class DiscoveryCache(models.Model):
    """Cache for Google search results -- avoids re-searching."""
    _id = models.ObjectIdField()
    domain = models.TextField(unique=True)
    company_name = models.TextField()
    tracxn_url = models.URLField(null=True, blank=True)  # None = searched, not found
    searched_at = models.DateTimeField(auto_now=True)

    objects = models.DjongoManager()

    class Meta:
        indexes = [
            models.Index(fields=['domain']),
        ]
