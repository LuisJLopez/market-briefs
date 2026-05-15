import os
import pytz
import logging
from logging.handlers import RotatingFileHandler


# ---------- CREDENTIALS (loaded from environment) ----------
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
X_API_KEY = os.environ["X_API_KEY"]
X_API_SECRET = os.environ["X_API_SECRET"]
X_ACCESS_TOKEN = os.environ["X_ACCESS_TOKEN"]
X_ACCESS_TOKEN_SECRET = os.environ["X_ACCESS_TOKEN_SECRET"]

# ---------- MODEL CONFIGURATION ----------
# Default: gpt-4o (faster and cheaper than gpt-4, with better instruction following)
# Override via env var to e.g. gpt-4.1, gpt-4o-mini, etc.
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")


# ---------- TIMEZONE CONFIGURATION ----------
us_tz = pytz.timezone('America/New_York')
uk_tz = pytz.timezone('Europe/London')
hk_tz = pytz.timezone('Asia/Hong_Kong')
sg_tz = pytz.timezone('Asia/Singapore')
jp_tz = pytz.timezone('Asia/Tokyo')
sh_tz = pytz.timezone('Asia/Shanghai')


# ---------- LOGGING SETUP ----------
_log_dir = os.environ.get('LOG_DIR', 'logs')
os.makedirs(_log_dir, exist_ok=True)
_log_path = os.path.join(_log_dir, 'tweet_bot.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        RotatingFileHandler(_log_path, maxBytes=5 * 1024 * 1024, backupCount=3),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger()
