from __future__ import annotations

import asyncio
import ipaddress
import socket
from urllib.parse import urlparse

from playwright.async_api import (
    Browser,
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)

_browser_lock = asyncio.Lock()
_render_slots = asyncio.Semaphore(2)
_playwright: Playwright | None = None
_browser: Browser | None = None

_BLOCK_MARKERS = (
    "verify you are human",
    "captcha",
    "access denied",
    "unusual traffic",
    "attention required",
    "datadome",
    "perimeterx",
    "incapsula",
    "cloudflare ray id",
)

_CONSENT_SELECTORS = (
    "#onetrust-accept-btn-handler",
    "[data-testid='uc-accept-all-button']",
    "button:has-text('Alle akzeptieren')",
    "button:has-text('Alles akzeptieren')",
    "button:has-text('Akzeptieren')",
    "button:has-text('Accept all')",
)


def _normalized_host(value: str | None) -> str:
    return (urlparse(value or "").hostname or "").casefold().removeprefix("www.")


def _host_matches(host: str, retailer_host: str) -> bool:
    normalized = host.casefold().removeprefix("www.")
    return normalized == retailer_host or normalized.endswith(f".{retailer_host}")


def _validate_public_navigation(url: str, retailer_host: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Chromium erhielt kein gültiges Händlerziel")
    if not _host_matches(parsed.hostname, retailer_host):
        raise ValueError("Chromium wurde auf eine fremde Domain weitergeleitet")

    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, parsed.port or 443)}
    except OSError as exc:
        raise ValueError("Händler-Domain konnte nicht aufgelöst werden") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise ValueError("Interne oder private Netzwerkziele sind nicht erlaubt")


async def _get_browser() -> Browser:
    global _playwright, _browser
    if _browser and _browser.is_connected():
        return _browser

    async with _browser_lock:
        if _browser and _browser.is_connected():
            return _browser
        if _playwright is None:
            _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage", "--no-sandbox"],
        )
        return _browser


async def _accept_consent(page: Page) -> None:
    for selector in _CONSENT_SELECTORS:
        try:
            button = page.locator(selector).first
            if await button.is_visible(timeout=600):
                await button.click(timeout=2000)
                await page.wait_for_timeout(400)
                return
        except Exception:
            continue


async def _wait_for_product_data(page: Page) -> None:
    try:
        await page.wait_for_function(
            """() => {
                const jsonLd = [...document.querySelectorAll('script[type="application/ld+json"]')]
                    .some(node => /Product|Offer|priceCurrency/i.test(node.textContent || ''));
                const visiblePrice = /\d+[,.]\d{2}\s*€/.test(document.body?.innerText || '');
                return jsonLd || visiblePrice;
            }""",
            timeout=12000,
        )
    except PlaywrightTimeoutError:
        pass

    try:
        await page.wait_for_load_state("networkidle", timeout=6000)
    except PlaywrightTimeoutError:
        pass
    await page.wait_for_timeout(1200)


async def render_product_html(product_url: str, base_url: str) -> str:
    retailer_host = _normalized_host(base_url)
    if not retailer_host:
        raise ValueError("Beim Händler fehlt eine gültige Basis-URL")
    _validate_public_navigation(base_url, retailer_host)
    _validate_public_navigation(product_url, retailer_host)

    async with _render_slots:
        browser = await _get_browser()
        context = await browser.new_context(
            locale="de-DE",
            timezone_id="Europe/Berlin",
            viewport={"width": 1440, "height": 1000},
            color_scheme="light",
            extra_http_headers={"Accept-Language": "de-DE,de;q=0.9,en;q=0.7"},
        )
        page = await context.new_page()
        page.set_default_timeout(15000)
        page.set_default_navigation_timeout(45000)
        try:
            try:
                await page.goto(base_url, wait_until="domcontentloaded")
                await _accept_consent(page)
            except PlaywrightTimeoutError:
                pass

            response = await page.goto(product_url, wait_until="domcontentloaded")
            if response is None:
                raise ValueError("Chromium erhielt keine Antwort von der Händlerseite")
            if response.status == 403:
                raise ValueError("Die Händlerseite blockiert auch den Chromium-Renderer mit HTTP 403")
            if response.status == 429:
                raise ValueError("Die Händlerseite begrenzt Chromium vorübergehend mit HTTP 429")
            if response.status >= 400:
                raise ValueError(f"Die Händlerseite antwortet in Chromium mit HTTP {response.status}")

            _validate_public_navigation(page.url, retailer_host)
            await _accept_consent(page)
            await _wait_for_product_data(page)

            html = await page.content()
            try:
                body_text = await page.locator("body").inner_text(timeout=5000)
            except Exception:
                body_text = ""
            challenge_sample = f"{await page.title()}\n{body_text[:200000]}\n{html[:100000]}".casefold()
            if any(marker in challenge_sample for marker in _BLOCK_MARKERS):
                raise ValueError(
                    "Der Händler zeigt Chromium eine Schutz- oder CAPTCHA-Seite. "
                    "DGD umgeht diese Prüfung nicht."
                )
            return html[:5_000_000]
        except PlaywrightTimeoutError as exc:
            raise ValueError("Die Händlerseite wurde in Chromium nicht rechtzeitig fertig geladen") from exc
        finally:
            await context.close()
