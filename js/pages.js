import { matchesItem } from './filter.mjs';

// Search and category buttons work together without fetching or hiding content from crawlers.
for (const catalog of document.querySelectorAll('[data-catalog]')) {
  const controls = catalog.querySelector('[data-controls]');
  const input = catalog.querySelector('input[type="search"]');
  const buttons = [...catalog.querySelectorAll('[data-filter]')];
  const items = [...catalog.querySelectorAll('[data-item]')];
  const count = catalog.querySelector('[data-result-count]');
  const empty = catalog.querySelector('[data-empty]');
  const reset = catalog.querySelector('[data-reset]');
  const groups = [...catalog.querySelectorAll('[data-result-group]')];
  const records = items.map(element => ({
    element, category: element.dataset.category,
    text: `${element.dataset.search || ''} ${element.textContent}`
  }));
  let category = 'all';
  const noun = catalog.dataset.catalog;

  function filter() {
    let visible = 0;
    for (const record of records) {
      record.element.hidden = !matchesItem(record, input.value, category);
      if (!record.element.hidden) visible++;
    }
    for (const button of buttons) button.setAttribute('aria-pressed', String(button.dataset.filter === category));
    for (const group of groups) group.hidden = ![...group.querySelectorAll('[data-item]')].some(item => !item.hidden);
    const filtered = input.value.trim() !== '' || category !== 'all';
    count.textContent = filtered ? `${visible} ${noun}${visible === 1 ? '' : 's'} found` : '';
    empty.hidden = visible !== 0;
  }
  controls.hidden = false;
  input.addEventListener('input', filter);
  for (const button of buttons) button.addEventListener('click', () => {
    category = button.dataset.filter;
    filter();
  });
  reset.addEventListener('click', () => {
    input.value = '';
    category = 'all';
    filter();
    input.focus();
  });
  filter();
}

async function copyText(text) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return;
    }
  } catch {
    // Some browsers disable the Clipboard API even on HTTPS; try the local fallback.
  }
  const previousFocus = document.activeElement;
  const field = document.createElement('textarea');
  field.value = text;
  field.className = 'clipboard-fallback';
  field.setAttribute('readonly', '');
  document.body.append(field);
  field.select();
  let copied;
  try {
    copied = document.execCommand('copy');
  } finally {
    field.remove();
    previousFocus?.focus({ preventScroll: true });
  }
  if (!copied) throw new Error('Clipboard unavailable');
}

const copyTimers = new WeakMap();
const status = document.querySelector('[data-interaction-status]');
for (const button of document.querySelectorAll('[data-copy-code], [data-copy-link]')) {
  button.hidden = false;
  const originalLabel = button.getAttribute('aria-label') || button.textContent.trim();
  button.addEventListener('click', async () => {
    const isCode = button.hasAttribute('data-copy-code');
    const text = isCode
      ? button.closest('.code-block').querySelector('code').textContent
      : document.querySelector('link[rel="canonical"]').href;
    try {
      await copyText(text);
      clearTimeout(copyTimers.get(button));
      button.dataset.copied = 'true';
      button.setAttribute('aria-label', isCode ? 'Code copied' : 'Link copied');
      const label = button.querySelector('[data-copy-label]');
      if (label) label.textContent = 'Copied!';
      if (status) status.textContent = isCode ? 'Code copied to clipboard.' : 'Post link copied to clipboard.';
      copyTimers.set(button, setTimeout(() => {
        delete button.dataset.copied;
        button.setAttribute('aria-label', originalLabel);
        if (label) label.textContent = isCode ? 'Copy code' : 'Copy link';
      }, 2000));
    } catch {
      if (status) status.textContent = isCode
        ? 'Copy unavailable. Select the code and copy it manually.'
        : 'Copy unavailable. Copy the post address from your browser.';
    }
  });
}

const article = document.querySelector('.article-body');
if (article) {
  const progress = document.querySelector('.reading-progress');
  const contents = document.querySelector('.table-of-contents');
  const mobile = window.matchMedia('(max-width: 639px)');
  const links = [...contents.querySelectorAll('a')];
  const sections = links.map(link => document.getElementById(link.hash.slice(1)));
  function syncContents() { contents.open = !mobile.matches; }
  syncContents();
  mobile.addEventListener('change', syncContents);
  function updateReading() {
    const bounds = article.getBoundingClientRect();
    const distance = Math.max(1, bounds.height - window.innerHeight);
    progress.value = Math.max(0, Math.min(1, -bounds.top / distance));
    let active = sections[0];
    for (const section of sections) {
      if (section.getBoundingClientRect().top <= window.innerHeight * .3) active = section;
    }
    for (const link of links) {
      const current = link.hash === `#${active.id}`;
      if (current) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    }
  }
  let pending = false;
  window.addEventListener('scroll', () => {
    if (pending) return;
    pending = true;
    requestAnimationFrame(() => { updateReading(); pending = false; });
  }, { passive: true });
  window.addEventListener('resize', updateReading);
  updateReading();
}
