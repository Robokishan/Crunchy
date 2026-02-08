"""
Generate Neo4j knowledge graph from unified Company model.

Creates nodes for:
- Company (from unified Company model)
- Founder
- Industry
- Investor (from Tracxn funding rounds)
- DataSource (crunchbase, tracxn)

Creates relationships:
- FOUNDED_BY (Company -> Founder)
- IN_INDUSTRY (Company -> Industry)
- SIMILAR_TO (Company -> Company)
- FUNDED_BY (Company -> Investor)
- HAS_SOURCE (Company -> DataSource)

Usage:
    python manage.py generate_graph
    python manage.py generate_graph --use-unified  # Use Company model (default)
    python manage.py generate_graph --use-crunchbase  # Use legacy Crunchbase model
"""

from django.core.management import BaseCommand
from django.conf import settings
from neo4j import GraphDatabase
from databucket.serializer import CrunchbaseSerializer, CompanySerializer
from databucket.models import Crunchbase, Company
from tqdm import tqdm

# Create a Neo4j driver instance
driver = GraphDatabase.driver(settings.NEO4J_RESOURCE_URI, auth=(
    settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD))


class Command(BaseCommand):
    help = 'Generate Neo4j knowledge graph from Company data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--use-crunchbase',
            action='store_true',
            help='Use legacy Crunchbase model instead of unified Company model'
        )
        parser.add_argument(
            '--use-unified',
            action='store_true',
            default=True,
            help='Use unified Company model (default)'
        )

    def handle(self, *args, **options):
        use_crunchbase = options.get('use_crunchbase', False)
        
        if use_crunchbase:
            self._generate_from_crunchbase()
        else:
            self._generate_from_company()

    def _generate_from_company(self):
        """Generate graph from unified Company model."""
        queryset = Company.objects.all().order_by("-updated_at")
        serialized_data = CompanySerializer(queryset, many=True).data
        
        print(f"Loaded {len(serialized_data)} companies from unified Company model")
        print("Exporting relations to Neo4j...")
        
        with driver.session() as session:
            with session.begin_transaction() as tx:
                print("Saving Data to Neo4j")
                
                for index, _company in tqdm(enumerate(serialized_data), total=len(serialized_data), ascii=' ='):
                    if not _company.get('name'):
                        continue

                    # Create or update Company node
                    create_company_query = """
                        MERGE (company:Company {normalized_domain: $normalized_domain})
                        SET company.mongoId = $mongoId,
                            company.name = $name,
                            company.funding = $funding,
                            company.website = $website,
                            company.description = $description,
                            company.long_description = $long_description,
                            company.acquired = $acquired,
                            company.founded = $founded,
                            company.crunchbase_url = $crunchbase_url,
                            company.tracxn_url = $tracxn_url,
                            company.match_confidence = $match_confidence,
                            company.logo = $logo
                        """
                    tx.run(
                        create_company_query,
                        mongoId=_company.get('_id'),
                        normalized_domain=_company.get('normalized_domain') or _company.get('name'),
                        name=_company.get('name'),
                        funding=_company.get('funding_total_usd', 0) or 0,
                        long_description=_company.get('long_description', ''),
                        acquired=_company.get('acquired', ''),
                        founded=_company.get('founded', ''),
                        website=_company.get('website', ''),
                        crunchbase_url=_company.get('crunchbase_url', ''),
                        tracxn_url=_company.get('tracxn_url', ''),
                        match_confidence=_company.get('match_confidence', 1.0),
                        logo=_company.get('logo', ''),
                        description=_company.get('description', '')
                    )

                    # Create Founder relationships
                    for founder in _company.get('founders', []):
                        if founder:
                            create_founder_query = """
                                MATCH (company:Company {mongoId: $companyId})
                                MERGE (founder:Founder {name: $founderName})
                                MERGE (company)-[:FOUNDED_BY]-(founder)
                                """
                            tx.run(create_founder_query, 
                                   companyId=_company.get("_id"), 
                                   founderName=founder)

                    # Create Industry relationships
                    for industry in _company.get('industries', []):
                        if industry:
                            create_industry_query = """
                                MATCH (company:Company {mongoId: $companyId})
                                MERGE (industry:Industry {name: $industry})
                                MERGE (company)-[:IN_INDUSTRY]-(industry)
                                """
                            tx.run(create_industry_query, 
                                   companyId=_company.get("_id"), 
                                   industry=industry)

                    # Create Similar Company relationships
                    for similar_company in _company.get('similar_companies', []):
                        if similar_company and similar_company != _company.get('crunchbase_url'):
                            create_similar_query = """
                                MATCH (company:Company {mongoId: $companyId})
                                MATCH (similarCompany:Company {crunchbase_url: $crunchbase_url})
                                MERGE (company)-[:SIMILAR_TO]-(similarCompany)
                                """
                            tx.run(create_similar_query, 
                                   companyId=_company.get('_id'),
                                   crunchbase_url=similar_company)

                    # NEW: Create Investor relationships from funding rounds
                    for funding_round in _company.get('funding_rounds', []):
                        investors = funding_round.get('investors', [])
                        round_type = funding_round.get('round_type', 'Unknown')
                        amount_usd = funding_round.get('amount_usd', 0)
                        
                        for investor in investors:
                            if investor:
                                create_investor_query = """
                                    MATCH (company:Company {mongoId: $companyId})
                                    MERGE (investor:Investor {name: $investorName})
                                    MERGE (company)-[r:FUNDED_BY]->(investor)
                                    SET r.round_type = $roundType,
                                        r.amount_usd = $amountUsd
                                    """
                                tx.run(
                                    create_investor_query,
                                    companyId=_company.get('_id'),
                                    investorName=investor,
                                    roundType=round_type,
                                    amountUsd=amount_usd or 0
                                )

                    # NEW: Create DataSource relationships for provenance
                    for source in _company.get('sources', []):
                        if source:
                            create_source_query = """
                                MATCH (company:Company {mongoId: $companyId})
                                MERGE (ds:DataSource {name: $sourceName})
                                MERGE (company)-[:HAS_SOURCE]-(ds)
                                """
                            tx.run(create_source_query,
                                   companyId=_company.get('_id'),
                                   sourceName=source)

        driver.close()
        print("Knowledge graph generation complete!")

    def _generate_from_crunchbase(self):
        """Generate graph from legacy Crunchbase model (backwards compatibility)."""
        queryset = Crunchbase.objects.all().order_by("-updated_at")
        serialized_data = CrunchbaseSerializer(queryset, many=True).data
        
        print(f"Loaded {len(serialized_data)} companies from Crunchbase model (legacy mode)")
        print("Exporting relations to Neo4j...")
        
        with driver.session() as session:
            with session.begin_transaction() as tx:
                print("Saving Data to Neo4j")
                
                for index, _company in tqdm(enumerate(serialized_data), total=len(serialized_data), ascii=' ='):
                    if _company.get('similar_companies') and _company.get('industries'):
                        create_company_query = """
                            MERGE (company:Company {name: $name, crunchbase_url: $crunchbase_url})
                            SET company.mongoId = $mongoId,
                                company.funding = $funding,
                                company.funding_txt = $funding_txt,
                                company.website = $website,
                                company.description = $description,
                                company.long_description = $long_description,
                                company.acquired = $acquired,
                                company.founded = $founded,
                                company.lastfunding = $lastfunding
                            """
                        tx.run(create_company_query, mongoId=_company.get('_id'),
                               name=_company.get('name'), 
                               funding=_company.get('funding_usd', 0) or 0,
                               funding_txt=_company.get('funding'),
                               long_description=_company.get('long_description'),
                               acquired=_company.get('acquired'),
                               founded=_company.get('founded'),
                               lastfunding=_company.get('lastfunding'),
                               website=_company.get('website'), 
                               crunchbase_url=_company.get('crunchbase_url'),
                               logo=_company.get('logo'), 
                               description=_company.get('description'))

                        # Create Founder relationships
                        for founder in _company.get('founders', []):
                            if founder:
                                create_founder_query = """
                                    MATCH (company:Company {mongoId: $companyId})
                                    MERGE (founder:Founder {name: $founderName})
                                    MERGE (company)-[:FOUNDED_BY]-(founder)
                                    """
                                tx.run(create_founder_query, 
                                       companyId=_company.get("_id"), 
                                       founderName=founder)

                        # Create Similar Company relationships
                        for similar_company in _company.get('similar_companies', []):
                            if similar_company != _company.get('crunchbase_url'):
                                create_similar_query = """
                                    MATCH (company:Company {mongoId: $companyId})
                                    MATCH (similarCompany:Company {crunchbase_url: $crunchbase_url})
                                    MERGE (company)-[:SIMILAR_TO]-(similarCompany)
                                    """
                                tx.run(create_similar_query, 
                                       companyId=_company.get('_id'),
                                       crunchbase_url=similar_company)

                        # Create Industry relationships
                        for industry in _company.get('industries', []):
                            if industry:
                                create_industry_query = """
                                    MATCH (company:Company {mongoId: $companyId})
                                    MERGE (industry:Industry {name: $industry})
                                    MERGE (company)-[:IN_INDUSTRY]-(industry)
                                    """
                                tx.run(create_industry_query, 
                                       companyId=_company.get("_id"), 
                                       industry=industry)
        
        driver.close()
        print("Knowledge graph generation complete (legacy mode)!")
