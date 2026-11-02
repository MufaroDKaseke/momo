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
