import './catalog-main.jsx';
import './catalog-live-prices.js';
import './catalog-performance.jsx';

function syncPublicNavigation() {
  const nav = document.querySelector('.catalog-header nav');
  if (!nav || nav.dataset.publicNavigation === 'true') return;
  nav.dataset.publicNavigation = 'true';
  nav.innerHTML = '<a class="active" href="/">Duftkatalog</a><a href="/admin.html">Admin Center</a>';
}

syncPublicNavigation();
const observer = new MutationObserver(syncPublicNavigation);
observer.observe(document.documentElement, {childList: true, subtree: true});
