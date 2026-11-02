/* Home page section tracking; menu behaviour lives in navigation.js. */
(() => {
  const navigation = document.querySelector('#primary-navigation');

  // Highlight the section currently at the top of the reading area.
  const sectionLinks = [...navigation.querySelectorAll('a[data-section]')];
  const sections = sectionLinks.map(link => document.getElementById(link.dataset.section));
  function updateNavigation() {
    let current = sections[0];
    for (const section of sections) {
      if (section.getBoundingClientRect().top <= window.innerHeight * 0.35) current = section;
    }
    for (const link of sectionLinks) {
      const active = link.dataset.section === current.id;
      link.classList.toggle('is-active', active);
      if (active) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    }
  }
  let pending = false;
  window.addEventListener('scroll', () => {
    if (pending) return;
    pending = true;
    window.requestAnimationFrame(() => {
      updateNavigation();
      pending = false;
    });
  }, { passive: true });
  window.addEventListener('resize', updateNavigation);
  updateNavigation();
})();
