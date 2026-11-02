# Momo Website (momo.co.zw)

Static HTML, CSS and vanilla JavaScript. No package installation or build step is required.

Run a local HTTP server from the repository root (JavaScript modules require HTTP):

```sh
python -m http.server 4173 --bind 127.0.0.1
```

Open `http://127.0.0.1:4173/`. The blog and builds are at `/blog/` and `/builds/`; both dated post URLs are preserved.

Validation:

```sh
python scripts/check_site.py
node --test tests/interactions.test.mjs
```

`css/home.css` provides the shared design tokens and components plus the home layout; `css/pages.css` adds the blog, post, builds and 404 layouts. `js/navigation.js` handles the shared mobile menu, `js/home.js` tracks home sections, and `js/pages.js` handles search, filtering, reading progress, code copy and sharing. Content is rendered in the HTML, so it remains available without JavaScript.
