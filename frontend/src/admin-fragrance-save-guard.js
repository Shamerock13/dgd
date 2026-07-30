const originalFetch = window.fetch.bind(window);

const EDITABLE_FRAGRANCE_FIELDS = new Set([
  'name', 'brand_id', 'year', 'gender', 'concentration', 'perfumer',
  'price_eur', 'image_url', 'image_source_name', 'image_source_url',
  'image_usage_note', 'image_status', 'description', 'top_notes',
  'heart_notes', 'base_notes', 'accords', 'longevity', 'projection',
  'sweetness', 'freshness',
]);

function isFragranceUpdate(input, init) {
  const method = String(init?.method || 'GET').toUpperCase();
  const url = typeof input === 'string' ? input : input?.url || '';
  return method === 'PUT' && /^\/api\/fragrances\/[0-9a-f-]+$/i.test(url);
}

function sanitizeFragranceBody(body) {
  if (typeof body !== 'string') return body;
  let parsed;
  try {
    parsed = JSON.parse(body);
  } catch {
    return body;
  }
  if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') return body;
  return JSON.stringify(Object.fromEntries(
    Object.entries(parsed).filter(([key]) => EDITABLE_FRAGRANCE_FIELDS.has(key)),
  ));
}

window.fetch = (input, init = {}) => {
  if (!isFragranceUpdate(input, init)) return originalFetch(input, init);
  return originalFetch(input, {...init, body: sanitizeFragranceBody(init.body)});
};
