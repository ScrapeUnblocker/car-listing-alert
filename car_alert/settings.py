BOT_NAME = "car_alert"
SPIDER_MODULES = ["car_alert.spiders"]

# We only talk to two APIs, not to websites.
ROBOTSTXT_OBEY = False

DOWNLOAD_TIMEOUT = 180
CONCURRENT_REQUESTS = 4

# A short console: only what the spider prints, plus warnings and errors.
LOG_LEVEL = "WARNING"
LOG_FORMAT = "%(levelname)s: %(message)s"
STATS_DUMP = False
