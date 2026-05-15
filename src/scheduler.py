import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

import config
from processor import generate_and_post_financial_tweet

logger = logging.getLogger(__name__)


class Scheduler:
    """Manages cron-style tweet jobs for different market sessions and time zones."""

    def __init__(self):
        self.scheduler = BlockingScheduler()

    def us_jobs(self):
        self.scheduler.add_job(
            generate_and_post_financial_tweet,
            trigger=CronTrigger(day_of_week="mon-fri", hour=8, minute=30, timezone=config.us_tz),
            args=["us_pre_open"],
            name="US pre-open",
        )
        self.scheduler.add_job(
            generate_and_post_financial_tweet,
            trigger=CronTrigger(day_of_week="mon-fri", hour=16, minute=30, timezone=config.us_tz),
            args=["us_post_close"],
            name="US post-close",
        )

    def uk_jobs(self):
        self.scheduler.add_job(
            generate_and_post_financial_tweet,
            trigger=CronTrigger(day_of_week="mon-fri", hour=7, minute=0, timezone=config.uk_tz),
            args=["uk_pre_open"],
            name="UK pre-open",
        )
        self.scheduler.add_job(
            generate_and_post_financial_tweet,
            trigger=CronTrigger(day_of_week="mon-fri", hour=16, minute=30, timezone=config.uk_tz),
            args=["uk_close"],
            name="UK close",
        )

    def liquidity(self):
        self.scheduler.add_job(
            generate_and_post_financial_tweet,
            trigger=CronTrigger(day_of_week="mon-fri", hour=8, minute=30, timezone=config.uk_tz),
            args=["liquidity"],
            name="M2 liquidity",
        )
        self.scheduler.add_job(
            generate_and_post_financial_tweet,
            trigger=CronTrigger(day_of_week="mon-fri", hour=19, minute=0, timezone=config.uk_tz),
            args=["gold"],
            name="Gold",
        )

    def market_sentiment(self):
        self.scheduler.add_job(
            generate_and_post_financial_tweet,
            trigger=CronTrigger(day_of_week="mon-fri", hour=14, minute=0, timezone=config.uk_tz),
            args=["market_sentiment"],
            name="Market sentiment",
        )
        self.scheduler.add_job(
            generate_and_post_financial_tweet,
            trigger=CronTrigger(day_of_week="mon-fri", hour=12, minute=0, timezone=config.uk_tz),
            args=["nbis"],
            name="NBIS / big-tech buys",
        )

    def saturday_briefing(self):
        self.scheduler.add_job(
            generate_and_post_financial_tweet,
            trigger=CronTrigger(day_of_week="sat", hour=23, minute=40, second=10, timezone=config.uk_tz),
            args=["test_event"],
            name="Saturday briefing",
        )

    def sunday_briefing(self):
        self.scheduler.add_job(
            generate_and_post_financial_tweet,
            trigger=CronTrigger(day_of_week="sun", hour=10, minute=0, second=0, timezone=config.uk_tz),
            args=["sunday_briefing"],
            name="Sunday briefing",
        )

    def sunday_upcoming_earnings(self):
        self.scheduler.add_job(
            generate_and_post_financial_tweet,
            trigger=CronTrigger(day_of_week="sun", hour=13, minute=0, second=0, timezone=config.uk_tz),
            args=["sunday_earning"],
            name="Sunday earnings preview",
        )

    def start(self):
        logger.info("Scheduler started — waiting for jobs...")
        self.scheduler.start()
