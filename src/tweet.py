import config
import tweepy

logger = config.logger


class Tweeter:

    def __init__(self):
        self.client = self._authenticate_x()

    def _authenticate_x(self) -> tweepy.Client:
        logger.info("Authenticating with X (Twitter) API v2")
        client = tweepy.Client(
            consumer_key=config.X_API_KEY,
            consumer_secret=config.X_API_SECRET,
            access_token=config.X_ACCESS_TOKEN,
            access_token_secret=config.X_ACCESS_TOKEN_SECRET,
        )
        try:
            me = client.get_me()
            logger.info("X authentication successful: @%s", me.data.username)
        except Exception as e:
            logger.error("X authentication failed: %s", str(e))
            raise
        return client

    def post_tweet(self, tweet: str):
        logger.info("Posting tweet: %s", tweet)
        try:
            response = self.client.create_tweet(text=tweet)
            logger.info("Tweet posted successfully. ID: %s", response.data['id'])
            return response
        except Exception as e:
            logger.error("Failed to post tweet: %s", str(e))
            raise
