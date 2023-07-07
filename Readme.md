
# Crunchy 

This is Crunchy my experiment over some fancy technologies for learning purpose. Crunchy is scrapper for crunchbase.com. 

## Background story
I usually surf a lot on crunchbase for looking into which companies are doing what and follow progress. But it wasn't very convenient experience because of Bloatware ui.  Web isn't that good any more.web should be Simple. Just like geo hotz's blog. so I got an idea to create clone frontend for crunchbase. but that comes with chaos. I wrap up my slives. and created a simple scrapper for crunchbase pushed data over kafka and made queue out of rabbitmq. and here it is crunchy a simple scrapper for rabbitmq


## Pending Work
* tor
* proxy servers

I wasn't able to add proxy. since crunchbase uses cloudflare for security. Tried Couple of free proxy list and tor but cloudflare blocks all of these so i am left with isp's dhcp. lol i disconnect and reconnect to get new ip and using multiple isps this way it works and i get lots of new company list on my preference. If someone is interested please give good suggestion to use tor with crunchbase. since tor browser works without a problem with crunchbase. i say it is possible. but needs some digging.

## Structure

| Component              |      Tech          |
| :-------------------- | :-----------------------: |
| Frontend  | NextJS |
| Design System  | Tailwind ( All time fav ) |
| Backend  | Django |
| Database | MongoDB |
| Scrapper |  Scrapy with playwright  |
| Data Pipeline |  Kafka  |
| Queue |  Rabbitmq  |
| Deployment |  docker-compose  |

### Configurations
Entire code base is configurable using .env. if you want to port crunchy for other websites. just change spider and it will work out of the box. architecture is super flexible

### Caution!
Crunchy doesn't respect robot.txt instead scheduler handles all the blocking mechanism. Please respect website owners !

