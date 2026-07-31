const form = document.querySelector('#settings-form');
const input = document.querySelector('#dgd-url');
const statusBox = document.querySelector('#status');
const submitButton = form.querySelector('button[type="submit"]');

function showStatus(message, kind) {
  statusBox.hidden = false;
  statusBox.className = `status ${kind}`;
  statusBox.textContent = message;
}

function normalizeBaseUrl(value) {
  const parsed = new URL(String(value || '').trim());
  if (!['http:', 'https:'].includes(parsed.protocol)) throw new Error('DGD muss über HTTP oder HTTPS erreichbar sein.');
  parsed.hash = '';
  parsed.search = '';
  return parsed.toString().replace(/\/$/, '');
}

function originPattern(baseUrl) {
  return `${new URL(baseUrl).origin}/*`;
}

async function testConnection(baseUrl) {
  const response = await fetch(`${baseUrl}/api/prices/browser-connector/health`, {cache: 'no-store'});
  if (!response.ok) throw new Error(`DGD antwortet mit HTTP ${response.status}.`);
  const body = await response.json();
  if (body.protocol !== 'browser-extension-v1') throw new Error('Diese DGD-Version unterstützt den Browser-Connector noch nicht.');
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  submitButton.disabled = true;
  statusBox.hidden = true;
  try {
    const baseUrl = normalizeBaseUrl(input.value);
    const stored = await chrome.storage.local.get('dgdBaseUrl');
    const oldBaseUrl = stored.dgdBaseUrl ? normalizeBaseUrl(stored.dgdBaseUrl) : '';
    const permission = await chrome.permissions.request({origins: [originPattern(baseUrl)]});
    if (!permission) throw new Error('Die Browserberechtigung für diese DGD-Adresse wurde nicht erteilt.');

    await testConnection(baseUrl);
    await chrome.storage.local.set({dgdBaseUrl: baseUrl});

    if (oldBaseUrl && oldBaseUrl !== baseUrl) {
      try {
        await chrome.permissions.remove({origins: [originPattern(oldBaseUrl)]});
      } catch {}
    }
    input.value = baseUrl;
    showStatus(`Verbunden. DGD ist unter ${new URL(baseUrl).host} erreichbar.`, 'success');
  } catch (error) {
    showStatus(error.message || String(error), 'error');
  } finally {
    submitButton.disabled = false;
  }
});

(async () => {
  const stored = await chrome.storage.local.get('dgdBaseUrl');
  if (stored.dgdBaseUrl) input.value = stored.dgdBaseUrl;
})();
