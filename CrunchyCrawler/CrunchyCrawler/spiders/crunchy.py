import json
import os
import re
from scrapy.selector import Selector
from scrapy.http import HtmlResponse
from CrunchyCrawler.request import generateRequest
from CrunchyCrawler.rabbitmq.spiders import RabbitMQMixin
from CrunchyCrawler.parser.CrunchbaseDataParser import CrunchbaseDataParser
from CrunchyCrawler.parser.TracxnDataParser import TracxnDataParser
from CrunchyCrawler.cloudflare.handler import CloudflareHandler, is_cloudflare_challenge
from scrapy.linkextractors import LinkExtractor
from scrapy.utils.project import get_project_settings
from loguru import logger


class CrunchySpider(RabbitMQMixin):
    """
    Unified spider that handles both Crunchbase and Tracxn URLs.
    Routes to the appropriate parser based on URL domain.
    Includes Cloudflare challenge handling using FlareSolverr.
    """

    name = "crunchy"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize Cloudflare handler with FlareSolverr settings
        settings = get_project_settings()
        self.cloudflare_handler = CloudflareHandler(
            flaresolverr_url=settings.get(
                "FLARESOLVERR_URL", "http://localhost:8191/v1"
            ),
            solve_timeout=settings.get("CLOUDFLARE_SOLVE_TIMEOUT", 60000),
        )

    async def parse(self, response):
        """Route to appropriate parser based on URL domain."""
        url = response.url

        if "crunchbase.com" in url:
            async for item in self._parse_crunchbase(response):
                yield item
        elif "tracxn.com" in url:
            async for item in self._parse_tracxn(response):
                yield item
        else:
            logger.warning(f"Unknown URL pattern, skipping: {url}")
            # Still need to ack the message to avoid infinite loop
            item = {
                "source": "unknown",
                "url": url,
                "delivery_tag": response.meta.get("delivery_tag"),
                "queue": response.meta.get("queue"),
                "_response": response.status,
            }
            # Close page if available
            await self._close_page(response)
            yield item

    async def _close_page(self, response):
        """Safely close the Playwright page if available."""
        page = response.meta.get("playwright_page")
        if page:
            try:
                await page.close()
            except Exception as e:
                logger.debug(f"Error closing page: {e}")

    def _safe_dump_filename(self, name: str, url: str) -> str:
        """Build a safe filename from company name or URL slug."""
        if name and (name := str(name).strip()):
            slug = re.sub(r"[^\w\-]", "_", name).strip("_").lower()[:80]
            if slug:
                return slug
        if "crunchbase.com/organization/" in url:
            slug = url.split("organization/")[-1].split("?")[0].strip("/")
        elif "tracxn.com/d/companies/" in url:
            slug = url.split("d/companies/")[-1].split("/")[0].split("__")[0]
        else:
            slug = "unknown"
        return re.sub(r"[^\w\-]", "_", slug).strip("_").lower()[:80] or "unknown"

    def _dump_raw_if_enabled(self, response, item: dict):
        """If DUMP_RAW_SCRAPED_DATA is True, write Tracxn url + html + parsed_item (only when parsed name is present)."""
        settings = get_project_settings()
        if not settings.get("DUMP_RAW_SCRAPED_DATA", False):
            return
        if getattr(response, "status", 0) != 200:
            return
        if not (item.get("name") or "").strip():
            logger.debug(f"Skipping Tracxn dump: no parsed name: {response.url}")
            return
        dump_dir = settings.get("DUMP_RAW_SCRAPED_DIR", "./raw_scraped_dumps")
        name = item.get("name") or item.get("url", "")
        url = getattr(response, "url", item.get("tracxn_url") or "")
        base = self._safe_dump_filename(name, url)
        path = os.path.join(dump_dir, f"{base}_tracxy.json")
        os.makedirs(dump_dir, exist_ok=True)
        payload = {
            "url": url,
            "html": getattr(response, "text", "") or "",
            "source": "tracxn",
            "parsed_item": {
                k: v for k, v in item.items() if k not in ("delivery_tag", "queue")
            },
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            logger.info(f"Dumped Tracxn data to {path}")
        except Exception as e:
            logger.warning(f"Failed to dump Tracxn data to {path}: {e}")

    def _create_retry_item(self, response, reason: str) -> dict:
        """
        Create a retry item when Cloudflare solving fails.
        This item will be processed by the pipeline to potentially requeue.
        """
        return {
            "source": "retry",
            "url": response.url,
            "delivery_tag": response.meta.get("delivery_tag"),
            "queue": response.meta.get("queue"),
            "_response": response.status,
            "retry_reason": reason,
            "_retry": True,
        }

    async def _solve_cloudflare(self, response):
        """
        Attempt to solve Cloudflare challenge using FlareSolverr.

        Returns:
            Tuple of (success: bool, new_response: response or None)
        """
        logger.info(f"Cloudflare challenge detected for: {response.url}")

        # Use FlareSolverr to solve the challenge
        # FlareSolverr makes its own request and returns solved HTML
        result = await self.cloudflare_handler.solve(response.url)

        if result and result.get("response"):
            logger.info("FlareSolverr solved Cloudflare challenge successfully!")
            # Replace response body with FlareSolverr's solved HTML and set status=200
            # so the pipeline acks (it only acks when _response == 200)
            solved_html = result["response"]
            new_response = response.replace(
                body=solved_html.encode("utf-8"),
                status=200,
            )
            return True, new_response
        else:
            logger.warning(
                f"FlareSolverr failed to solve Cloudflare for: {response.url}"
            )
            return False, None

    async def _parse_crunchbase(self, response):
        """Parse Crunchbase company page with Cloudflare handling."""
        # Check for Cloudflare challenge
        if is_cloudflare_challenge(response):
            success, new_response = await self._solve_cloudflare(response)

            if success and new_response:
                response = new_response
            else:
                # Close page and requeue for retry
                await self._close_page(response)
                yield self._create_retry_item(response, "cloudflare_solve_failed")
                return

        # Close the Playwright page - we have the content we need
        await self._close_page(response)

        # Dump response to JSON before parsing (for test_crunchy_extractor)
        settings = get_project_settings()
        if settings.get("DUMP_RAW_SCRAPED_DATA", False):
            dump_dir = settings.get("DUMP_RAW_SCRAPED_DIR", "./raw_scraped_dumps")
            base = self._safe_dump_filename("", response.url)
            path = os.path.join(dump_dir, f"{base}_crunchbase.json")
            os.makedirs(dump_dir, exist_ok=True)
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "url": response.url,
                            "html": getattr(response, "text", "") or "",
                            "source": "crunchbase",
                        },
                        f,
                        ensure_ascii=False,
                        indent=2,
                    )
                logger.info(f"Dumped Crunchbase response to {path}")
            except Exception as e:
                logger.warning(f"Failed to dump Crunchbase response: {e}")

        # Parse the page content
        x = Selector(response)
        item = CrunchbaseDataParser.extract_item(x)

        # Add source tag for databucket routing (Crunchbase vs Tracxn queue)
        item["source"] = "crunchbase"
        item["crunchbase_url"] = response.url
        delivery_tag = response.meta.get("delivery_tag")
        item["delivery_tag"] = delivery_tag
        item["queue"] = response.meta.get("queue")
        queue = response.meta.get("queue")
        item["_response"] = response.status

        logger.info(f"Crunchbase scrapped item ----> {item}")

        # Extract similar companies link
        # TODO: fix this later
        similarCompanies = None  # CrunchbaseDataParser.extractSimilarCompanies(x)
        if similarCompanies:
            similarCompanies = response.urljoin(similarCompanies)
            logger.info(f"Getting similarCompanies-------> {similarCompanies}")
            yield generateRequest(
                similarCompanies,
                delivery_tag,
                callback=self.parseSimilarCompanies,
                previousResult=item,
                queue=queue,
            )
        else:
            yield item

    async def _parse_tracxn(self, response):
        """Parse Tracxn company page."""
        x = Selector(response)
        item = TracxnDataParser.extract_item(x)

        # Add source tag for databucket routing (Crunchbase vs Tracxn queue)
        item["source"] = "tracxn"
        item["tracxn_url"] = response.url
        item["delivery_tag"] = response.meta.get("delivery_tag")
        item["queue"] = response.meta.get("queue")
        item["_response"] = response.status

        self._dump_raw_if_enabled(response, dict(item))

        # Close the page
        await self._close_page(response)

        logger.info(f"Tracxn scrapped item ----> {item}")
        yield item

    async def parseSimilarCompanies(self, response):
        """Parse similar companies from Crunchbase similarity page."""
        # Check for Cloudflare on similar companies page too
        if is_cloudflare_challenge(response):
            success, new_response = await self._solve_cloudflare(response)

            if success and new_response:
                response = new_response
            else:
                await self._close_page(response)
                yield self._create_retry_item(
                    response, "similar_companies_cloudflare_failed"
                )
                return

        # Close the Playwright page
        await self._close_page(response)

        link_ext = LinkExtractor(
            restrict_xpaths="//org-similarity-card", allow=r"\b\/organization\b"
        )
        links = link_ext.extract_links(response)
        item = {}
        item["similar_companies"] = []
        previous_results = response.meta.get("previousResult", {})
        logger.info(f"Similar company links --> {links}")
        for link in links:
            item["similar_companies"].append(link.url)
        current_results = dict(item)
        combined_results = {**previous_results, **current_results}

        yield combined_results
