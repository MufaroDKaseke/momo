/* Shared, progressively enhanced navigation. Links remain visible without JS. */
(() => {
  const toggle = document.querySelector('.menu-toggle');
  const navigation = document.querySelector('#primary-navigation');
  if (!toggle || !navigation) return;
  const mobile = window.matchMedia('(max-width: 639px)');
  function setMenu(open) {
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    navigation.hidden = mobile.matches && !open;
  }
  toggle.hidden = false;
  setMenu(false);
  mobile.addEventListener('change', () => setMenu(false));
  toggle.addEventListener('click', () => setMenu(toggle.getAttribute('aria-expanded') !== 'true'));
  navigation.addEventListener('click', event => {
    if (mobile.matches && event.target.closest('a')) setMenu(false);
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
      setMenu(false);
      toggle.focus();
    }
  });
  document.addEventListener('click', event => {
    if (mobile.matches && !event.target.closest('.site-header')) setMenu(false);
  });
})();
