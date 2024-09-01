match (i:Industry)<-[:IN_INDUSTRY]-(c:Company)-[:IN_INDUSTRY]-(oi:Industry)
where i.name = "Artificial Intelligence"
return oi
order by  c.funding desc

--Query to get founders list company funding ascending in Artificial Intelligence space
MATCH (i:Industry {name: "Artificial Intelligence"})<-[:IN_INDUSTRY]-(c:Company)-[:FOUNDED_BY]-(t:Founder)
WHERE i.name = "Artificial Intelligence"
WITH DISTINCT t, c, c.funding AS companyFunding
RETURN t, c.name AS companyName
ORDER BY companyFunding ASC

-- Query to get founders list company funding descending in Artificial Intelligence space
MATCH (i:Industry {name: "Artificial Intelligence"})<-[:IN_INDUSTRY]-(c:Company)-[:FOUNDED_BY]-(t:Founder)
WHERE i.name = "Artificial Intelligence"
WITH DISTINCT t, c, c.funding AS companyFunding
RETURN t, c.name AS companyName
ORDER BY companyFunding DESC

-- get founders list
MATCH (i:Industry)<-[:IN_INDUSTRY]-(c:Company)-[:FOUNDED_BY]-(t:Founder)
WHERE i.name = "Artificial Intelligence" and c.funding IS NOT NULL
WITH DISTINCT t, c, c.funding AS companyFunding
RETURN t, c AS companyName
ORDER BY companyFunding ASC

-- first can be country specific if the currency is multiple like australian dollar or simple dollar,
second currency sign if it is country specific other wise number
last again optional short form



-- part2 31/08/2024
MATCH (i:Founder {name: "Dimitar Jetchev"})<-[:FOUNDED_BY]-(c:Company)-[:FOUNDED_BY]-(t:Founder)
WHERE i.name = "Dimitar Jetchev"
WITH DISTINCT t, c, c.funding AS companyFunding
RETURN t, c.name AS companyName
ORDER BY companyFunding DESC


MATCH (i:Founder {name: "Dimitar Jetchev"})<-[:FOUNDED_BY]-(c:Company)-[:IN_INDUSTRY]->(t:Industry)
WHERE i.name = "Dimitar Jetchev"
WITH DISTINCT t, c, c.funding AS companyFunding
RETURN t, c.name AS companyName
ORDER BY companyFunding DESC



MATCH (i:Founder {name: "Dimitar Jetchev"})<-[:FOUNDED_BY]-(c:Company)-[:IN_INDUSTRY]->(t:Industry)-[:IN_INDUSTRY]-(ci:Company)-[foundedby:FOUNDED_BY]-(f:Founder) return t
MATCH (i:Founder {name: "Dimitar Jetchev"})<-[:FOUNDED_BY]-(c:Company)-[:IN_INDUSTRY]->(t:Industry)-[:IN_INDUSTRY]-(ci:Company)-[:IN_INDUSTRY]-(ti:Industry) return ti