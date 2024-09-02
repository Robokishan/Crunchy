from re import escape
from django.conf import settings
from .contextmanager import Neo4jDBSessionManager
from neo4j.debug import watch
import sys

manager = Neo4jDBSessionManager(settings.NEO4J_RESOURCE_URI, settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD, False)

# watch("neo4j", out=sys.stdout) #Output debug to stdout 

def get_companies_by_industry(industry):
    q = f'''
        MATCH (i:Industry)<-[:IN_INDUSTRY]-(c:Company)-[:FOUNDED_BY]-(f:Founder)
        WHERE i.name =~ '(?i).*{industry}.*'
        WITH c, i, c.crunchbase_url AS url, c.funding AS companyFunding, COLLECT(DISTINCT f.name) AS founders
        MATCH (c)-[:IN_INDUSTRY]->(otherIndustry:Industry)
        RETURN c.name AS company, url, companyFunding, founders, COLLECT(DISTINCT otherIndustry.name) AS industries
        ORDER BY companyFunding DESC
        '''
    with manager.session as s:
        result = s.run(q, {'industry': industry})
        return result.data()
        

def get_founders_by_industry(industry):
    q = f'''
        MATCH (i:Industry)<-[:IN_INDUSTRY]-(c:Company)-[:FOUNDED_BY]-(t:Founder)
        WHERE i.name =~ '(?i).*{industry}.*'
        WITH DISTINCT t, c, c.funding AS companyFunding, i.name as via
        RETURN t.name as founder, via, c.name AS company, c.crunchbase_url AS url, c.funding AS companyFunding
        ORDER BY companyFunding DESC
        '''
    with manager.session as s:
        result = s.run(q, {'industry': industry})
        return result.data()

def get_industry_by_industry(industry):
    q = f'''
        MATCH (i:Industry)<-[:IN_INDUSTRY]-(c:Company)-[:IN_INDUSTRY]-(t:Industry)
        WHERE i.name =~ '(?i).*{industry}.*'
        RETURN i.name as industry, c.funding AS companyFunding, t.name as similarIndustry, c.name AS company, c.crunchbase_url AS url
        ORDER BY companyFunding DESC
        '''
    with manager.session as s:
        result = s.run(q, {'industry': industry})
        return result.data()  
        


def get_industry_by_founder(founder):
    q = f'''
        MATCH (t:Founder)-[:FOUNDED_BY]-(c:Company)-[:IN_INDUSTRY]->(i:Industry)
        WHERE t.name =~ '(?i).*{founder}.*'
        RETURN t.name as founder, c.name as company, c.crunchbase_url as url, collect(i.name) as industries, c.funding as companyFunding
        order by companyFunding desc
        '''
    with manager.session as s:
        result = s.run(q, {'founder': founder})
        return result.data()

def get_companies_by_founder(founder):
    q = f'''
        MATCH (t:Founder)-[:FOUNDED_BY]-(c:Company)-[:IN_INDUSTRY]->(i:Industry)-[:IN_INDUSTRY]-(t2:Company)
        WHERE t.name =~ '(?i).*{founder}.*'
        RETURN t.name as founder,i.name as via, t2, c.name AS company, c.crunchbase_url AS url, c.funding AS companyFunding
        ORDER BY companyFunding DESC
        '''
    with manager.session as s:
        result = s.run(q, {'founder': founder})
        return result.data()

def get_founders_by_founder(founder):
    q = f'''
        MATCH (t:Founder)-[:FOUNDED_BY]-(c:Company)-[:IN_INDUSTRY]-(i:Industry)-[:IN_INDUSTRY]-(c2:Company)-[:FOUNDED_BY]-(t2:Founder)
        WHERE t.name =~ '(?i).*{founder}.*'
        RETURN t.name as query, c.name as via, i.name as industry_via, collect(t2.name) as founders, c2.name as company, c2.crunchbase_url as url, c2.funding as companyFunding
        ORDER BY companyFunding DESC
        '''
    with manager.session as s:
        result = s.run(q, {'founder': founder})
        return result.data()

def get_companies_by_company(company):
    q = f'''
        MATCH (c:Company)-[:IN_INDUSTRY]-(i:Industry)-[:IN_INDUSTRY]-(t:Company)-[:IN_INDUSTRY]-(i2:Industry)
        WHERE c.name =~ '(?i).*{company}.*'
        RETURN t.name AS company, i.name as via, collect(i2.name) as industry, t.crunchbase_url AS url, t.funding AS companyFunding
        ORDER BY t.funding DESC
        '''
    with manager.session as s:
        result = s.run(q, {'company': company})
        return result.data()
    

def get_founders_by_company(company):
    q = f'''
        MATCH (c:Company)-[:FOUNDED_BY]-(t:Founder)
        WHERE c.name =~ '(?i).*{company}.*'
        RETURN c as company, collect(t.name) as founders
        order by c.funding desc
        '''
    with manager.session as s:
        result = s.run(q, {'company': company})
        return result.data()
    

def get_industries_by_company(company):
    q = f'''
        MATCH (c:Company)-[:IN_INDUSTRY]-(i:Industry)
        WHERE c.name =~ '(?i).*{company}.*'
        RETURN c as company, collect(i.name) as industries
        order by c.funding desc
        '''
    with manager.session as s:
        result = s.run(q, {'company': company})
        return result.data()
