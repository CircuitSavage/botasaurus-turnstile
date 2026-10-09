"""Solve Cloudflare Turnstile on a live Botasaurus driver via the Peak API.

Botasaurus drives an anti-detect Chrome and is a common pick against
Cloudflare. When the Turnstile widget still stalls, this reads the sitekey,
gets a token from Peak, and injects it so the form or navigation proceeds.

Works with the Botasaurus ``Driver`` (uses ``run_js`` and ``current_url``).
Botasaurus itself is an optional import.
"""

from __future__ import annotations

import json
import os
from typing import Optional

from .peak import DEFAULT_API_URL, TASK_TURNSTILE, PeakClient, PeakError

_READ_SITEKEY_JS = r"""
var el = document.querySelector('[data-sitekey]');
if (el) { return el.getAttribute('data-sitekey'); }
var m = (document.documentElement.outerHTML || '').match(
    /(?:sitekey|render)\s*[:=]\s*["']((?:0x|1x)[^"']+)["']/i);
return m ? m[1] : null;
"""

# Injects a solved token: sets every cf-turnstile-response field, fires
# input/change so listeners react, and calls the widget's success callback.
# The token is embedded as a JSON literal in inject_token.
_INJECT_TOKEN_BODY = r"""
var fields = document.querySelectorAll(
    'input[name="cf-turnstile-response"], textarea[name="cf-turnstile-response"], ' +
    'input#cf-turnstile-response, [name="cf-turnstile-response"]');
if (!fields.length) {
    var holder = document.querySelector('.cf-turnstile') || document.body;
    var inp = document.createElement('input');
    inp.type = 'hidden';
    inp.name = 'cf-turnstile-response';
    holder.appendChild(inp);
    fields = [inp];
}
fields.forEach(function (f) {
    f.value = token;
    f.dispatchEvent(new Event('input', { bubbles: true }));
    f.dispatchEvent(new Event('change', { bubbles: true }));
});
var called = false;
document.querySelectorAll('[data-callback]').forEach(function (w) {
    var name = w.getAttribute('data-callback');
    if (name && typeof window[name] === 'function') {
        window[name](token);
        called = true;
    }
});
return called;
"""


def read_sitekey(driver) -> Optional[str]:
    """Return the Turnstile sitekey on the current page, or None."""
    sitekey = driver.run_js(_READ_SITEKEY_JS)
    if sitekey:
        return str(sitekey).strip()
    return None


def inject_token(driver, token: str) -> None:
    """Inject a solved token into the page's Turnstile widget."""
    driver.run_js("var token = " + json.dumps(token) + ";\n" + _INJECT_TOKEN_BODY)


def _current_url(driver) -> Optional[str]:
    try:
        url = getattr(driver, "current_url", None)
        if url:
            return url
    except Exception:
        pass
    try:
        return driver.run_js("return window.location.href")
    except Exception:
        return None


def solve_turnstile(
    driver,
    api_key: Optional[str] = None,
    proxy: Optional[str] = None,
    sitekey: Optional[str] = None,
    url: Optional[str] = None,
    task_type: str = TASK_TURNSTILE,
    api_url: Optional[str] = None,
    timeout: float = 180.0,
) -> str:
    """Solve the Turnstile challenge on ``driver``'s current page.

    Reads the sitekey from the DOM (unless ``sitekey`` is given), asks Peak
    for a token, injects it, and returns the token. ``api_key`` defaults to
    the ``PEAK_API_KEY`` environment variable; ``url`` defaults to the
    driver's current URL. Pass ``proxy`` to mint the token from the browser's
    egress IP; omit it and Peak solves without one.

    Raises :class:`~botasaurus_turnstile.peak.PeakError` on failure.
    """
    api_key = api_key or os.environ.get("PEAK_API_KEY")

    if sitekey is None:
        sitekey = read_sitekey(driver)
    if not sitekey:
        raise PeakError(
            "No Turnstile sitekey found on the page. Pass sitekey= "
            "explicitly if the widget renders in a frame or after load."
        )

    if url is None:
        url = _current_url(driver)

    client = PeakClient(
        api_key, api_url=api_url or DEFAULT_API_URL, proxy=proxy, timeout=timeout
    )
    token = client.solve(sitekey, url, proxy=proxy, task_type=task_type)
    inject_token(driver, token)
    return token
