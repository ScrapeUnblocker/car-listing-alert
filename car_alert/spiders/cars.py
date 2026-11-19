"""Watch a car search on AutoScout24 and ping your phone when a new car is listed.

Run it locally with `scrapy crawl cars`, or on a timer in ScrapeUnblocker Spider Cloud.
Needs two environment variables: SCRAPEUNBLOCKER_KEY and NTFY_TOPIC.
"""

import hashlib
import json
import os
from urllib.parse import urlencode

import scrapy

API = "https://api.scrapeunblocker.com/getPageSource"
NTFY = "https://ntfy.sh"


class CarsSpider(scrapy.Spider):
    name = "cars"

    # What to watch: set your filters on autoscout24.com, sort by "Latest offers first", and paste
    # the address bar here. Or pass it when you run the spider:
    #   scrapy crawl cars -a search="https://www.autoscout24.com/lst/bmw/3-series?sort=age&desc=1&priceto=25000"
    search = "https://www.autoscout24.com/lst?atype=C&sort=age&desc=1&priceto=20000&kmto=100000&fregfrom=2018&cy=D"
    skip_words = ""  # comma-separated, e.g. "damaged,export,defect" - listings with these words are ignored

    async def start(self):
        # Memory lives in ntfy: every run posts the listings it saw to a second, silent topic,
        # and ntfy keeps the last 12 hours of it. No database, no files.
        topic = os.environ["NTFY_TOPIC"]
        yield scrapy.Request(f"{NTFY}/{topic}-seen/json?poll=1&since=12h", callback=self.fetch_search)

    def fetch_search(self, response):
        seen = set()
        for line in response.text.splitlines():
            seen.update(json.loads(line).get("message", "").split())

        # parsed_data=true: ScrapeUnblocker opens the page and hands back the listings as JSON.
        query = {"url": self.search, "parsed_data": "true"}
        yield scrapy.Request(
            f"{API}?{urlencode(query)}",
            method="POST",
            headers={"x-scrapeunblocker-key": os.environ["SCRAPEUNBLOCKER_KEY"]},
            callback=self.check_listings,
            cb_kwargs={"seen": seen},
        )

    def check_listings(self, response, seen):
        cars = response.json()["data"]["data"].get("items", [])
        if not cars:
            self.logger.warning("No listings found - open the search link in a browser and check it")
            return

        topic = os.environ["NTFY_TOPIC"]
        skip = [w.strip().lower() for w in self.skip_words.split(",") if w.strip()]
        ids = []
        for car in cars:
            car_id = hashlib.sha1(car["url"].encode()).hexdigest()[:12]
            ids.append(car_id)
            name = " ".join(x for x in (car.get("make"), car.get("model")) if x)
            facts = (car.get("first_registration"), car.get("mileage"), car.get("fuel"), car.get("city"))
            details = " · ".join(str(x) for x in facts if x)
            yield {"car": name, "price": price_text(car), "details": details, "url": car["url"]}

            # First run (nothing remembered yet): just remember what is there today.
            if not seen or car_id in seen:
                continue
            if any(w in f"{name} {car.get('title', '')}".lower() for w in skip):
                continue
            alert = {
                "topic": topic,
                "title": f"{name} · {price_text(car)}",
                "message": f"{car.get('title') or ''}\n{details}".strip(),
                "click": car["url"],
                "attach": car.get("image_url"),
                "tags": ["red_car"],
            }
            yield scrapy.Request(NTFY, method="POST", body=json.dumps(alert), callback=self.sent, dont_filter=True)

        if seen:
            print(f"Checked {len(ids)} cars, {sum(i not in seen for i in ids)} new.")
        else:
            print(f"Remembered {len(ids)} cars. New ones will go to your phone.")
            hello = {
                "topic": topic,
                "title": "Watching your car search",
                "message": f"{len(ids)} cars match right now. I'll ping you when a new one is listed.",
                "tags": ["eyes"],
            }
            yield scrapy.Request(NTFY, method="POST", body=json.dumps(hello), callback=self.sent, dont_filter=True)
        remember = {"topic": f"{topic}-seen", "message": " ".join(ids)}
        yield scrapy.Request(NTFY, method="POST", body=json.dumps(remember), callback=self.remembered, dont_filter=True)

    def sent(self, response):
        print("Sent to your phone:", response.json()["title"])

    def remembered(self, response):
        pass  # the memory topic is silent, nothing to show


def price_text(car):
    price = car.get("price_formatted") or car.get("price")
    if isinstance(price, dict):
        value = price.get("value")
        return f"{value:,} {price.get('currency', '')}".strip() if isinstance(value, (int, float)) else ""
    return str(price or "")
