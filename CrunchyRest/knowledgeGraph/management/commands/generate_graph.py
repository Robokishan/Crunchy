from django.core.management import BaseCommand
from neo4j import GraphDatabase
from databucket.serializer import CrunchbaseSerializer
from databucket.models import Crunchbase
from tqdm import tqdm


# Define your Neo4j connection credentials
neo4j_uri = "neo4j://localhost:7687"  # Replace with your Neo4j server URI
neo4j_user = "neo4j"   # Replace with your Neo4j username
neo4j_password = "Abcd@1234567890"  # Replace with your Neo4j password

# Create a Neo4j driver instance
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))


class Command(BaseCommand):
    def handle(self, *args, **options):
        page = 1
        page_size = 10
        queryset = Crunchbase.objects.all().order_by("-updated_at")
        start_index = (page - 1) * page_size
        end_index = page * page_size
        serialized_data = CrunchbaseSerializer(
             queryset, many=True).data
        # print("Serialized data", serialized_data)
        print("Loaded Mongo data")
        print("exporting Relations to neo4j")
        with driver.session() as session:
            print("Saving Data to Neo4j")
            for index, _company in tqdm(enumerate(serialized_data), total=len(serialized_data)):
                # print("Company",_company)
                if _company.get('similar_companies') and _company.get('industries'):
                    # print('-----------')
                    # print("_company", type(_company), index, _company)
                    with session.begin_transaction() as tx:
                        create_company_query = """
                        MERGE (company:Company {name: $name})
                        SET company.mongoId = $mongoId,
                            company.funding = $funding,
                            company.website = $website,
                            company.crunchbase_url = $crunchbase_url,
                            company.description = $description
                        """
                        company = tx.run(create_company_query, mongoId=_company.get('_id'),
                            name=_company.get('name'), funding=_company.get('funding'),
                            website=_company.get('website'), crunchbase_url=_company.get('crunchbase_url'),
                            logo=_company.get('logo'), description=_company.get('description'))
                        # print("Company node created:", company)  # Print the company variable
                        

                        # Create or update founder nodes and their relationships
                        if _company.get('founders'):
                            for founder in _company.get('founders', []):
                                create_founder_query = """
                                MATCH (company:Company {mongoId: $companyId})
                                MERGE (founder:Founder {name: $founderName})
                                MERGE (company)-[:FOUNDED_BY]->(founder)
                                """
                                tx.run(create_founder_query, companyId=_company.get("_id"), founderName=founder)

                        # # Create relationships for similar companies
                        for similar_company in _company.get('similar_companies', []):
                            # print('similar_company',similar_company)
                            if similar_company != _company.get('crunchbase_url'):
                                create_similar_query = """
                                MATCH (company:Company {mongoId: $companyId})
                                MATCH (similarCompany:Company {crunchbase_url: $crunchbase_url})
                                MERGE (company)-[:SIMILAR_TO]->(similarCompany)
                                """
                                tx.run(create_similar_query, companyId=_company.get('_id'),
                                    crunchbase_url=similar_company)

                        # Create relationships for tags
                        for industry in _company.get('industries', []):
                            create_industry_query = """
                            MATCH (company:Company {mongoId: $companyId})
                            MERGE (industry:Industry {name: $industry})
                            MERGE (company)-[:IN_INDUSTRY]->(industry)
                            """
                            tx.run(create_industry_query, companyId=_company.get("_id") , industry=industry)
        driver.close()
                
                            
