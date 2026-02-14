"""
Requeue Tracxn crawl URLs with entry_point="tracxn".

Mode 1 (default): Drains the Tracxn crawl queue and re-publishes each message
as {"url": <url>, "entry_point": "tracxn"}.

Mode 2 (--from-db): Pushes TracxnRaw.tracxn_url from DB to the crawl queue
to repopulate (e.g. after queue was drained).

Usage:
  python manage.py requeue_tracxn_crawl_with_tracxn_entry_point [--limit N] [--dry-run]
  python manage.py requeue_tracxn_crawl_with_tracxn_entry_point --from-db [--limit N]
"""
import json
from django.core.management import BaseCommand
from django.conf import settings
import pika


def parse_crawl_body(body):
    """Return (url, entry_point) from queue message body."""
    if not body:
        return "", None
    raw = body.decode("utf-8") if isinstance(body, bytes) else body
    raw = (raw or "").strip()
    if not raw:
        return "", None
    if raw.startswith("{") and "url" in raw:
        try:
            data = json.loads(raw)
            return data.get("url", "") or "", data.get("entry_point")
        except (json.JSONDecodeError, TypeError):
            pass
    return raw, None


class Command(BaseCommand):
    help = "Requeue Tracxn crawl queue messages with entry_point='tracxn'"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Max messages to requeue (0 = no limit, drain all)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only log what would be done; do not ack or re-publish",
        )
        parser.add_argument(
            "--from-db",
            action="store_true",
            help="Push TracxnRaw URLs from DB to crawl queue (repopulate); no drain",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = options["limit"]
        from_db = options["from_db"]
        if from_db:
            self._refill_from_db(limit=limit, dry_run=dry_run)
            return
        if dry_run and limit <= 0:
            limit = 10
            print(f"Dry-run: defaulting --limit to {limit}")
        queue_name = getattr(
            settings, "RB_TRACXN_CRAWL_QUEUE", "crawl_tracxn_queue"
        )
        connection_string = getattr(settings, "RABBITMQ_URL", None)
        if not connection_string:
            print("RABBITMQ_URL not set")
            return

        # Connection for consuming (get + ack)
        params = pika.URLParameters(connection_string)
        conn = pika.BlockingConnection(params)
        channel = conn.channel()
        channel.queue_declare(queue=queue_name, durable=True)

        # Ensure manager can publish (separate channel)
        from rabbitmq.apps import RabbitMQManager

        RabbitMQManager.connect_to_rabbitmq()

        seen_urls = set()
        requeued = 0
        skipped = 0
        dropped = 0
        while True:
            if limit and requeued >= limit:
                break
            method_frame, _, body = channel.basic_get(queue=queue_name)
            if body is None:
                break
            url, old_ep = parse_crawl_body(body)
            if not url or "tracxn.com" not in url:
                if not dry_run:
                    channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                skipped += 1
                continue
            url = url.strip().rstrip("/")
            if url in seen_urls:
                if not dry_run:
                    channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                dropped += 1
                print(f"Dropped duplicate: {url[:90]}")
                continue
            seen_urls.add(url)
            if dry_run:
                print(
                    f"  [dry-run] would requeue entry_point={old_ep!r} -> tracxn: {url[:80]}"
                )
                channel.basic_nack(
                    delivery_tag=method_frame.delivery_tag, requeue=True
                )
                requeued += 1
                if limit and requeued >= limit:
                    break
                continue
            ok = RabbitMQManager.publish_tracxn_crawl(
                {"url": url, "entry_point": "tracxn"}
            )
            if not ok:
                print("Publish failed (channel unavailable), requeuing message")
                channel.basic_nack(
                    delivery_tag=method_frame.delivery_tag, requeue=True
                )
                break
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            requeued += 1
            if requeued % 100 == 0 and requeued > 0:
                print(f"  Requeued {requeued}")

        conn.close()
        print(
            f"Requeued {requeued}, dropped {dropped} duplicate(s), skipped {skipped}"
            + (" (dry-run)" if dry_run else "")
        )

    def _refill_from_db(self, limit=0, dry_run=False):
        from rabbitmq.apps import RabbitMQManager
        from databucket.models import TracxnRaw

        RabbitMQManager.connect_to_rabbitmq()
        qs = TracxnRaw.objects.all().order_by("-updated_at")
        if limit:
            qs = qs[:limit]
        pushed = 0
        for rec in qs:
            url = (getattr(rec, "tracxn_url", None) or "").strip().rstrip("/")
            if not url or "tracxn.com" not in url:
                continue
            if dry_run:
                print(f"  [dry-run] would push: {url[:80]}")
                pushed += 1
                continue
            ok = RabbitMQManager.publish_tracxn_crawl(
                {"url": url, "entry_point": "tracxn"}
            )
            if not ok:
                print("Publish failed (channel unavailable)")
                break
            pushed += 1
            if pushed % 100 == 0 and pushed > 0:
                print(f"  Pushed {pushed}")
        print(f"Pushed {pushed} Tracxn URL(s) from DB" + (" (dry-run)" if dry_run else ""))
