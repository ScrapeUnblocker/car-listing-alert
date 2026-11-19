# Car listing alert

A tiny Scrapy spider that watches your car search on AutoScout24 and pings your phone when a new car is listed.

- You set the filters on the website (make, model, price, mileage, year, country) and paste the link. Nothing else to configure.
- Sends a push notification through [ntfy](https://ntfy.sh) - free, no account needed - with the price, the photo and the key details. Tap it and the listing opens.
- Pings you once per car: it remembers which listings it has already seen in a second, silent ntfy topic. No database, no files.
- Runs locally with `scrapy crawl cars`, or on a timer in [ScrapeUnblocker Spider Cloud](https://docs.scrapeunblocker.com/spider-cloud/overview?utm_source=github&utm_medium=integration&utm_campaign=car-listing-alert).

Listings come from [ScrapeUnblocker](https://scrapeunblocker.com/?utm_source=github&utm_medium=integration&utm_campaign=car-listing-alert) with [`parsed_data=true`](https://docs.scrapeunblocker.com/guides/parsed-data?utm_source=github&utm_medium=integration&utm_campaign=car-listing-alert): one API call opens the search page and returns every listing on it as JSON - make, model, price, mileage, year, city, link and photo.

## 1. What to watch

1. Open [autoscout24.com](https://www.autoscout24.com) and set your filters.
2. Sort by **Latest offers first** - new cars then always show up on the first page.
3. Copy the link from the address bar.

Paste it into `search` at the top of [`car_alert/spiders/cars.py`](car_alert/spiders/cars.py), or pass it when you run the spider:

```bash
scrapy crawl cars -a search="https://www.autoscout24.com/lst/bmw/3-series?sort=age&desc=1&priceto=25000&cy=D"
```

To ignore some listings, give a few words: `-a skip_words="damaged,export,defect"`.

On the first run it only remembers the cars that are listed today and sends you one "Watching your car search" message. From the second run on, every new car is a notification.

## 2. Two settings

| Variable | What it is |
| --- | --- |
| `SCRAPEUNBLOCKER_KEY` | Your API key from [app.scrapeunblocker.com](https://app.scrapeunblocker.com/dashboard/api-keys?utm_source=github&utm_medium=integration&utm_campaign=car-listing-alert). New accounts get 500 free requests. |
| `NTFY_TOPIC` | Any name you like, for example `cars-k3j9x2p7`. Install the ntfy app on your phone and subscribe to it. Topics on ntfy.sh are public, so pick a name nobody will guess. The spider also uses `<your topic>-seen` for its memory - don't subscribe to that one. |

## 3. Run it on your computer

```bash
pip install -r requirements.txt
export SCRAPEUNBLOCKER_KEY=your_key
export NTFY_TOPIC=cars-k3j9x2p7
scrapy crawl cars
```

A run takes a few seconds. Every listing is also printed as an item, so `scrapy crawl cars -O cars.json` saves the whole search.

## 4. Run it on a timer in Spider Cloud

1. In the dashboard open **Spider Cloud → New project**.
2. Where the code comes from: **Other git host**, and paste `https://github.com/ScrapeUnblocker/car-listing-alert` - it is public, so no token is needed. (Forked it and changed the code? Connect GitHub and pick your fork instead.)
3. Environment variables, one per line: `SCRAPEUNBLOCKER_KEY=...` and `NTFY_TOPIC=...`
4. **Deploy**, then run the `cars` spider with your link as the `search` argument.
5. Add a schedule with the same argument, for example every 30 minutes.

Running by hand works on the free Spider Cloud slot. Schedules need a paid slot - see [slots and the free plan](https://docs.scrapeunblocker.com/spider-cloud/projects?utm_source=github&utm_medium=integration&utm_campaign=car-listing-alert#slots-and-the-free-plan).

## How often?

Good cars go fast, but every 15-30 minutes is plenty. One search every 30 minutes is 48 calls a day, so the 500 free requests last about ten days. Every minute would burn through them in eight hours.

## License

MIT
