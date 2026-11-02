export function normalizeText(value) {
  return String(value).normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase().replace(/\s+/g, ' ').trim();
}

export function matchesItem(item, query, category) {
  if (category !== 'all' && item.category !== category) return false;
  const text = normalizeText(item.text);
  return normalizeText(query).split(' ').filter(Boolean).every(term => text.includes(term));
}
