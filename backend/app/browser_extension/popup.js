const connection = document.querySelector('#connection');
const pageCard = document.querySelector('#page');
const pageTitle = document.querySelector('#page-title');
const pageHost = document.querySelector('#page-host');
const queueCard = document.querySelector('#queue');
const queueTitle = document.querySelector('#queue-title');
const queueMeta = document.querySelector('#queue-meta');
const sendButton = document.querySelector('#send');
const nextButton = document.querySelector('#next');
const settingsButton = document.querySelector('#settings');
const resultBox = document.querySelector('#result');

let baseUrl = '';
let activeTab = null;
let nextQueueItem = null;

function showStatus(element, message, kind = 'neutral') {
  element.hidden = false;
  element.className = `status ${kind}`;
  element.textContent = message;
}

function normalizeBaseUrl(value) {
  const parsed = new URL(String(value || '').trim());
  if (!['http:', 'https:'].includes(parsed.protocol)) throw new Error('DGD muss über HTTP oder HTTPS erreichbar sein.');
  parsed.hash = '';
  parsed.search = '';
  return parsed.toString().replace(/\/$/, '');
}

async function getConfiguredBaseUrl() {
  const stored = await chrome.storage.local.get('dgdBaseUrl');
  return stored.dgdBaseUrl ? normalizeBaseUrl(stored.dgdBaseUrl) : '';
}

async function hasPermission(value) {
  const originPattern = `${new URL(value).origin}/*`;
  return chrome.permissions.contains({origins: [originPattern]});
}

async function checkConnection() {
  if (!baseUrl) {
    showStatus(connection, 'Noch keine DGD-Adresse eingestellt.', 'error');
    return false;
  }
  if (!(await hasPermission(baseUrl))) {
    showStatus(connection, 'Der Erweiterung fehlt noch die Freigabe für deine DGD-Adresse.', 'error');
    return false;
  }
  try {
    const response = await fetch(`${baseUrl}/api/prices/browser-connector/health`, {cache: 'no-store'});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const body = await response.json();
    if (body.protocol !== 'browser-extension-v1') throw new Error('Nicht unterstützte Connector-Version.');
    showStatus(connection, `Verbunden mit ${new URL(baseUrl).host}`, 'success');
    return true;
  } catch (error) {
    showStatus(connection, `DGD nicht erreichbar: ${error.message}`, 'error');
    return false;
  }
}

async function loadActiveTab() {
  const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
  if (!tab?.id || !tab.url || !/^https?:/i.test(tab.url)) {
    showStatus(resultBox, 'Bitte zuerst eine normale HTTP-/HTTPS-Produktseite öffnen.', 'error');
    return false;
  }
  activeTab = tab;
  const url = new URL(tab.url);
  pageTitle.textContent = tab.title || 'Produktseite';
  pageHost.textContent = url.host;
  pageCard.hidden = false;
  return true;
}

function queueItemLabel(item) {
  return [item?.brand_name, item?.fragrance_name, item?.retailer_name].filter(Boolean).join(' · ');
}

async function loadQueue(offerNextButton = false) {
  nextQueueItem = null;
  nextButton.hidden = true;
  try {
    const response = await fetch(
      `${baseUrl}/api/prices/browser-connector/queue?due_only=true&limit=1`,
      {cache: 'no-store'},
    );
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const body = await response.json();
    const due = Number(body.summary?.due || 0);
    const item = body.items?.[0] || null;

    queueCard.hidden = false;
    if (!due || !item) {
      queueCard.className = 'queue-card complete';
      queueTitle.textContent = 'Prüfrunde abgeschlossen';
      queueMeta.textContent = 'Aktuell ist keine Browser-Preisquelle fällig.';
      return;
    }

    nextQueueItem = item;
    queueCard.className = 'queue-card due';
    queueTitle.textContent = `${due} ${due === 1 ? 'Quelle ist' : 'Quellen sind'} fällig`;
    queueMeta.textContent = `Als Nächstes: ${queueItemLabel(item)}`;
    nextButton.hidden = !offerNextButton;
  } catch (error) {
    queueCard.hidden = false;
    queueCard.className = 'queue-card';
    queueTitle.textContent = 'Prüfliste nicht verfügbar';
    queueMeta.textContent = error.message || String(error);
  }
}

function extractPageEvidence() {
  const jsonLd = [];
  let jsonBytes = 0;
  document.querySelectorAll('script[type="application/ld+json"]').forEach(node => {
    if (jsonLd.length >= 40) return;
    const value = String(node.textContent || '').trim();
    if (!value || value.length > 250000) return;
    jsonBytes += value.length;
    if (jsonBytes <= 900000) jsonLd.push(value);
  });

  const meta = {};
  const relevant = /price|currency|availability|stock|product|title|sku|gtin|ean/i;
  document.querySelectorAll('meta[property],meta[name],meta[itemprop]').forEach(node => {
    if (Object.keys(meta).length >= 80) return;
    const key = node.getAttribute('property') || node.getAttribute('name') || node.getAttribute('itemprop');
    const value = node.getAttribute('content');
    if (!key || !value || !relevant.test(key)) return;
    meta[String(key).slice(0, 120)] = String(value).slice(0, 4000);
  });

  const canonicalNode = document.querySelector('link[rel="canonical"]');
  const canonicalUrl = canonicalNode?.href && /^https?:/i.test(canonicalNode.href)
    ? canonicalNode.href
    : null;

  return {
    url: location.href,
    canonical_url: canonicalUrl,
    title: document.title || null,
    json_ld: jsonLd,
    meta,
    visible_text: String(document.body?.innerText || '').slice(0, 400000),
  };
}

async function collectEvidence() {
  const results = await chrome.scripting.executeScript);
    }
    const price = new Intl.NumberFormat('de-DE', {style: 'currency', currency: 'EUR'}).format(body.price_eur);
    const availability = body.in_stock ? 'lieferbar' : 'nicht lieferbar';
    showStatus(resultBox, `${body.retailer}: ${price} · ${availability}. Erfolgreich in DGD gespeichert.`, 'success');
    await loadQueue(true);
  } catch (error) {
    showStatus(resultButton.disabled = true;
  sendButton.textContent = 'Produktseite wird gelesen …';
  try {
    const evidence = await collectEvidence();
    sendButton.textContent = 'Preis wird an DGD übertragen …';
    const response = await fetch(`${baseUrl}/api/prices/browser-connector/import`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-DGD-Connector': 'browser-extension-v1',
      },
      body: JSON.stringify(evidence),
    });
    let body = null;
    try {
      body = await response.json();
    } catch {
      body = {};
    }
    if (!response.ok) {
      const detail = typeof body.detail === 'string' ? body.detail : `HTTP ${response.status}`;
      throw new Error(detail);
    }
    const price = new Intl.NumberFormat('de-DE', {style: 'currency', currency: 'EUR'}).format(body.price_eur);
    const availability = body.in_stock ? 'lieferbar' : 'nicht lieferbar';
    showStatus(resultBox, `${body.retailer}: ${price} · ${availability}. Erfolgreich in DGD gespeichert.`, 'success');
    await loadQueue(true);
  } catch (error) {
    showStatus(result () => {
  try {
    baseUrl = await getConfiguredBaseUrl();
    const [connected, pageReady] = await Promise.all([checkConnection(), loadActiveTab()]);
    sendButton.disabled = !(connected && pageReady);
    if (connected) await loadQueue(false);
  } catch (error) {
    showStatus(connection, error.message || String(error), 'error');
  }
})();
