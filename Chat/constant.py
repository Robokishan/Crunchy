CYPHER_GENERATION_TEMPLATE = """Task:Generate Cypher statement to query a graph database.
    Instructions:
    Use only the provided relationship types and properties in the schema.
    Do not use any other relationship types or properties that are not provided.
    Schema:
    {schema}
    Note: Do not include any explanations or apologies in your responses.
    Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
    Do not include any text except the generated Cypher statement.
    Do not use two Match in one query.
    Do not use two return in one query.
    Follow these Cypher example when Generating Cypher statements:
    # How many Companies are there?
    MATCH (m:Company)
    RETURN count(*) AS result 

    # What does Open AI do?
    MATCH (m:Company)
    where m.name =~ ".*Open AI*."
    RETURN m.description AS short_description, m.long_description as long_description

    # List of Founders having companies in same industry as Founded by Sam Altman
    MATCH (t:Founder)-[:FOUNDED_BY]-(c:Company)-[:IN_INDUSTRY]-(i:Industry)-[:IN_INDUSTRY]-(c2:Company)-[:FOUNDED_BY]-(t2:Founder)
    WHERE t.name =~ '.*Sam Altman.*'
    RETURN t2.name as name

    # List of companies in Artificial Intelligence industry having large funding
    MATCH (c:Company)-[:IN_INDUSTRY]-(i:Industry)
    WHERE i.name =~ '.*Artificial Intelligence*.'
    return c.name, c.funding
    ORDER BY c.funding DESC

    # List of companies in Artificial Intelligence industry having very less funding
    MATCH (c:Company)-[:IN_INDUSTRY]-(i:Industry)
    WHERE i.name =~ '.*Artificial Intelligence*.' and c.funding > 0
    return c.name, c.funding
    ORDER BY c.funding ASC

    # List of companies in Artificial Intelligence industry who did not get any funding
    MATCH (c:Company)-[:IN_INDUSTRY]-(i:Industry)
    WHERE i.name =~ '.*Artificial Intelligence*.' and c.funding = 0
    return c.name, c.funding

    # when was Open AI last funded?
    MATCH (c:Company)
    where c.name =~ ".*Open AI*."
    RETURN c.name, c.lastfunding

    # List of Companies got acquired
    MATCH (c:Company)
    where c.acquired is not null
    return c.name, c.acquired


    The question is:
    {question}"""


CYPHER_QA_TEMPLATE = """You are an assistant that helps to form nice and human understandable answers.
        The information part contains the provided information that you must use to construct an answer.
        The provided information is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
        Make the answer sound as a response to the question. Do not mention that you based the result on the given information.
        Here is an example:

        Question: Which managers own Neo4j stocks?
        Context:[manager:CTL LLC, manager:JANE STREET GROUP LLC]
        Helpful Answer: CTL LLC, JANE STREET GROUP LLC owns Neo4j stocks.

        Follow this example when generating answers.
        If the provided information is empty, say that you don't know the answer.
        Information:
        {context}

        Question: {question}
        Helpful Answer:"""
