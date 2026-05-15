from config import logger
from openai_prompter import Prompter
from tweet import Tweeter


def generate_and_post_financial_tweet(market_event: str):
    logger.info("Processing market event: %s", market_event)

    tweet = Prompter().generate_financial_tweet(section=market_event)
    logger.info("Generated tweet: %s", tweet)

    Tweeter().post_tweet(tweet)
    logger.info("Tweet posted for market event: %s", market_event)
