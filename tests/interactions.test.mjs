import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { matchesItem } from '../js/filter.mjs';

const records = [
  { category: 'tutorials', text: 'Git It Together: Git & GitHub for beginners' },
  { category: 'career', text: 'The 2024 tech job market and AI' },
  { category: 'web', text: 'A café portfolio using Spotify API and TypeScript' },
];

test('category and all search terms are combined', () => {
  assert.deepEqual(records.filter(item => matchesItem(item, 'git beginners', 'tutorials')), [records[0]]);
  assert.deepEqual(records.filter(item => matchesItem(item, 'git', 'career')), []);
  assert.deepEqual(records.filter(item => matchesItem(item, 'git python', 'all')), []);
  assert.deepEqual(records.filter(item => matchesItem(item, '', 'all')), records);
  assert.deepEqual(records.filter(item => matchesItem(item, '', 'career')), [records[1]]);
});

test('search handles case, repeated whitespace and diacritics as literal text', () => {
  assert(matchesItem(records[2], '  CAFE   SpOtIfY  ', 'all'));
  assert(!matchesItem(records[0], '<script>', 'all'));
  assert(!matchesItem(records[0], '.*', 'all'));
});

function navigationFixture(isMobile) {
  const events = new Map();
  const attributes = new Map();
  const toggle = { hidden: true, focused: false,
    setAttribute: (key, value) => attributes.set(key, value),
    getAttribute: key => attributes.get(key),
    addEventListener: (key, value) => events.set(`toggle:${key}`, value),
    focus() { this.focused = true; },
  };
  const navigation = { hidden: false, addEventListener: (key, value) => events.set(`nav:${key}`, value) };
  const mobile = { matches: isMobile, addEventListener: (key, value) => events.set(`media:${key}`, value) };
  const context = {
    window: { matchMedia: () => mobile },
    document: {
      querySelector: selector => selector === '.menu-toggle' ? toggle : navigation,
      addEventListener: (key, value) => events.set(`document:${key}`, value),
    },
  };
  vm.runInNewContext(fs.readFileSync(new URL('../js/navigation.js', import.meta.url), 'utf8'), context);
  return { toggle, navigation, mobile, events, attributes };
}

test('mobile menu opens, closes with Escape, and returns focus to its button', () => {
  const menu = navigationFixture(true);
  assert.equal(menu.toggle.hidden, false);
  assert.equal(menu.navigation.hidden, true);
  menu.events.get('toggle:click')();
  assert.equal(menu.navigation.hidden, false);
  assert.equal(menu.attributes.get('aria-expanded'), 'true');
  menu.events.get('document:keydown')({ key: 'Escape' });
  assert.equal(menu.navigation.hidden, true);
  assert.equal(menu.attributes.get('aria-expanded'), 'false');
  assert.equal(menu.toggle.focused, true);
});

test('desktop navigation stays visible and mobile navigation closes on link activation', () => {
  const menu = navigationFixture(false);
  assert.equal(menu.navigation.hidden, false);
  menu.mobile.matches = true;
  menu.events.get('media:change')();
  assert.equal(menu.navigation.hidden, true);
  menu.events.get('toggle:click')();
  menu.events.get('nav:click')({ target: { closest: selector => selector === 'a' } });
  assert.equal(menu.navigation.hidden, true);
  menu.mobile.matches = false;
  menu.events.get('media:change')();
  assert.equal(menu.navigation.hidden, false);
});

function effectsFixture({ reduced = false, saved = null, storageBlocked = false } = {}) {
  const events = new Map();
  const attributes = new Map();
  const classes = new Set();
  const label = { textContent: '' };
  const use = { setAttribute: (key, value) => attributes.set(`icon:${key}`, value) };
  const button = { hidden: true, disabled: false,
    setAttribute: (key, value) => attributes.set(key, value),
    querySelector: selector => selector === 'use' ? use : label,
    addEventListener: (key, handler) => events.set(`button:${key}`, handler),
  };
  const queuedCard = { classList: { add: name => classes.add(`card:${name}`) } };
  const preference = { matches: reduced, addEventListener: (key, handler) => events.set(`media:${key}`, handler) };
  const root = { dataset: {}, classList: { add: name => classes.add(name) } };
  const storage = {
    getItem: () => { if (storageBlocked) throw new Error('Storage blocked'); return saved; },
    setItem: (_key, value) => { if (storageBlocked) throw new Error('Storage blocked'); saved = value; },
  };
  const document = {
    documentElement: root, hidden: false,
    querySelectorAll: selector => selector === '[data-motion-toggle]' ? [button] : selector === '.reveal-ready' ? [queuedCard] : [],
    addEventListener: (key, handler) => events.set(`document:${key}`, handler),
  };
  vm.runInNewContext(fs.readFileSync(new URL('../js/effects.js', import.meta.url), 'utf8'), {
    document, window: { matchMedia: () => preference }, localStorage: storage,
  });
  return { root, button, preference, events, attributes, label, classes, document, saved: () => saved };
}

test('pausing motion persists across pages and reveals waiting cards', () => {
  const motion = effectsFixture();
  assert.equal(motion.root.dataset.motion, 'running');
  assert.equal(motion.button.hidden, false);
  motion.events.get('button:click')();
  assert.equal(motion.root.dataset.motion, 'paused');
  assert.equal(motion.label.textContent, 'Resume animations');
  assert.equal(motion.attributes.get('aria-pressed'), 'true');
  assert(motion.classes.has('card:is-visible'));
  const nextPage = effectsFixture({ saved: motion.saved() });
  assert.equal(nextPage.root.dataset.motion, 'paused');
  nextPage.events.get('button:click')();
  assert.equal(nextPage.root.dataset.motion, 'running');
  assert.equal(nextPage.saved(), 'running');
});

test('device reduced motion takes precedence and follows preference changes', () => {
  const motion = effectsFixture({ reduced: true, saved: 'running' });
  assert.equal(motion.root.dataset.motion, 'paused');
  assert.equal(motion.button.disabled, true);
  assert.equal(motion.label.textContent, 'Reduced motion');
  motion.preference.matches = false;
  motion.events.get('media:change')();
  assert.equal(motion.root.dataset.motion, 'running');
  assert.equal(motion.button.disabled, false);
});

test('blocked local storage still allows pausing; background tabs suspend motion', () => {
  const motion = effectsFixture({ storageBlocked: true });
  motion.events.get('button:click')();
  assert.equal(motion.root.dataset.motion, 'paused');
  motion.document.hidden = true;
  motion.events.get('document:visibilitychange')();
  assert.equal(motion.root.dataset.pageHidden, 'true');
  motion.document.hidden = false;
  motion.events.get('document:visibilitychange')();
  assert.equal(motion.root.dataset.pageHidden, 'false');
});
