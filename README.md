<a href="https://peak.fo/?utm_source=github&utm_medium=readme&utm_campaign=packages&utm_content=botasaurus-turnstile">
  <img src="https://raw.githubusercontent.com/CircuitSavage/botasaurus-turnstile/main/assets/peak-banner.png" alt="Peak — solve Cloudflare Turnstile & the 5s challenge in ~1s" width="100%">
</a>

# botasaurus-turnstile

**botasaurus-turnstile** solves Cloudflare Turnstile on a [Botasaurus](https://github.com/omkarcloud/botasaurus) driver by injecting a Peak-solved token, so a protected form or navigation proceeds.

## Why

Botasaurus drives an anti-detect Chrome and ships a lot of Cloudflare handling, which is why people run it against protected sites. The interstitial often clears. The Turnstile *widget* on a datacenter IP is the part that doesn't — it renders, waits for a click or a token that never comes, and the run stalls.

This reads the sitekey from the DOM, gets a token from Peak, and injects it as the `cf-turnstile-response` value plus the widget's success callback. When the driver gets you to the page but the widget won't clear, drop in a Peak API key and it goes through.

## Powered by Peak

This package uses [Peak](https://peak.fo/?utm_source=github&utm_medium=readme&utm_campaign=packages&utm_content=botasaurus-turnstile) to solve Turnstile.
- Solve Cloudflare Turnstile & the 5s challenge in about a second
- $0.90 per 1,000 successful Turnstile solves, down to $0.35 at volume
- 1,000 free solves to start, no card.

→ [Get your free API key](https://peak.fo/?utm_source=github&utm_medium=readme&utm_campaign=packages&utm_content=botasaurus-turnstile) · [Docs](https://peak.fo/docs/turnstile?utm_source=github&utm_medium=readme&utm_campaign=packages&utm_content=botasaurus-turnstile) · [Pricing](https://peak.fo/pricing?utm_source=github&utm_medium=readme&utm_campaign=packages&utm_content=botasaurus-turnstile)

## Install

```bash
pip install botasaurus-turnstile botasaurus-driver
```

## Quickstart

```python
import os
from botasaurus.browser import browser, Driver
from botasaurus_turnstile import solve_turnstile

os.environ["PEAK_API_KEY"] = "pk_your_api_key"


@browser
def scrape(driver: Driver, data):
    driver.get("https://protected.example/login")

    # Reads the sitekey from the page, solves via Peak, injects the token.
    solve_turnstile(driver)

    # the form / navigation can now proceed


scrape()
```

Works the same with a standalone `botasaurus_driver.Driver()` — anything that exposes `run_js` and `current_url`.

## How it works

1. **Read the sitekey.** A `run_js` DOM scan finds the `data-sitekey` on the `.cf-turnstile` widget, or the sitekey set through a JS `render()` call.
2. **Solve via Peak.** `POST https://api.peak.fo/solve` with `task_type: "turnstiletask"`, the sitekey, and the driver's current URL. Pass `proxy=` to mint the token from your browser's egress IP.
3. **Inject the token.** `run_js` sets every `cf-turnstile-response` field, fires `input`/`change`, and calls the widget's `data-callback` so the form or navigation continues.

## API

```python
solve_turnstile(
    driver,               # a Botasaurus Driver
    api_key=None,         # defaults to env PEAK_API_KEY
    proxy=None,           # optional http://user:pass@ip:port, forwarded to Peak
    sitekey=None,         # override auto-detection (e.g. widget in a frame)
    url=None,             # defaults to driver.current_url
    task_type="turnstiletask",
    timeout=180.0,
) -> str                  # the injected token
```

`read_sitekey(driver)` and `inject_token(driver, token)` are exposed for finer control. Peak also supports `task_type="cloudflare5stask"` for the 5s interstitial.

The API key is read from `PEAK_API_KEY` by default; you can also pass it explicitly. Never hardcode a real key.

## Legitimate use

For automation, QA, and scraping public data you are allowed to access. Respect each target's Terms of Service and robots directives, and do not use this for credential-stuffing or other abuse.

## License

MIT — see [LICENSE](./LICENSE).
