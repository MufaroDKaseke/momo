/* Motion enhances the static site; it never gates content or navigation. */
(() => {
  const root = document.documentElement;
  const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
  const buttons = [...document.querySelectorAll('[data-motion-toggle]')];
  let userPaused = false;
  try { userPaused = localStorage.getItem('momo-motion') === 'paused'; } catch { /* Storage is optional. */ }
  let observer;

  function revealEverything() {
    observer?.disconnect();
    for (const target of document.querySelectorAll('.reveal-ready')) target.classList.add('is-visible');
  }

  function syncMotion() {
    const paused = preference.matches || userPaused;
    root.dataset.motion = paused ? 'paused' : 'running';
    for (const button of buttons) {
      button.hidden = false;
      button.disabled = preference.matches;
      button.setAttribute('aria-pressed', String(paused));
      const label = preference.matches ? 'Reduced motion' : paused ? 'Resume animations' : 'Pause animations';
      button.querySelector('[data-motion-label]').textContent = label;
      button.querySelector('use').setAttribute('href', `/img/social-icons.svg#${paused ? 'play' : 'pause'}`);
    }
    if (paused) revealEverything();
  }

  for (const button of buttons) button.addEventListener('click', () => {
    userPaused = !userPaused;
    try { localStorage.setItem('momo-motion', userPaused ? 'paused' : 'running'); } catch { /* Keep the setting for this page. */ }
    syncMotion();
  });
  preference.addEventListener('change', syncMotion);
  root.classList.add('motion-ready');
  syncMotion();
  function syncVisibility() { root.dataset.pageHidden = String(document.hidden); }
  document.addEventListener('visibilitychange', syncVisibility);
  syncVisibility();

  if (root.dataset.motion !== 'running' || typeof IntersectionObserver !== 'function') return;
  const targets = [...document.querySelectorAll('.project-card, .skill-card, .credentials-card, .post-card, .archive-card, .build-card, .featured-post, .featured-build, .author-card, .contact')];
  try {
    observer = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      }
    }, { threshold: .08, rootMargin: '0px 0px -20px 0px' });
    targets.forEach((target, index) => {
      // Keep the first viewport immediately visible, including primary content.
      if (target.getBoundingClientRect().top < window.innerHeight) return;
      target.style.setProperty('--reveal-delay', `${(index % 3) * 55}ms`);
      target.classList.add('reveal-ready');
      observer.observe(target);
    });
  } catch {
    revealEverything();
  }
})();
