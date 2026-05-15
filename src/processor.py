from config import logger
from openai_prompter import Prompter
from tweet import Tweeter


def generate_and_post_financial_tweet(market_event: str):
    logger.info("Job started: %s", market_event)
    try:
        tweet = Prompter().generate_financial_tweet(section=market_event)
        Tweeter().post_tweet(tweet)
        logger.info("Job completed: %s", market_event)
    except Exception:
        logger.exception("Job failed: %s", market_event)
        raise  # let APScheduler record it as a missed execution
