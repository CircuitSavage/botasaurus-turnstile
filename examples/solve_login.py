import os

from botasaurus.browser import browser, Driver
from botasaurus_turnstile import solve_turnstile

# Get a free key at https://peak.fo
os.environ.setdefault("PEAK_API_KEY", "pk_your_api_key")


@browser
def scrape(driver: Driver, data):
    driver.get("https://protected.example/login")
    token = solve_turnstile(driver)
    print("solved, token length:", len(token))


if __name__ == "__main__":
    scrape()
