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

`css/home.css` provides the shared design tokens and components plus the home layout; `css/pages.css` adds the blog, post, builds and 404 layouts. `css/effects.css` adds cat animations and social icons. `js/navigation.js` handles the shared mobile menu, `js/home.js` tracks home sections, and `js/pages.js` handles search, filtering, reading progress, code copy and sharing. `js/effects.js` handles progressive scroll reveals and the shared animation pause control. It respects reduced-motion preferences and stores the user's pause preference locally. Content and social icons remain available without JavaScript.

SEO copy and page/image assignments are maintained in `content/seo.json`. Render updated metadata into the static HTML with:

```sh
python scripts/update_seo.py
python scripts/check_site.py
```

The five 1200 × 630 social cards live in `img/seo/`, with portable outlined SVG exports in `img/seo/sources/`. Their editable layout is in `scripts/generate_seo_images.mjs`; it reuses the existing portrait and cat SVGs. To regenerate artwork and raster favicons, install the optional pinned SVG renderer and run:

```sh
npm ci --prefix tools/seo
node scripts/generate_seo_images.mjs
```

Font files and their SIL Open Font License notices are included in `tools/seo/fonts/`. Image generation runs offline after installing the renderer. These tools are not runtime dependencies, and no Node build is needed to publish the site.

`robots.txt` allows crawling and declares the image sitemap. The unused `blog/post.html` example and the 404 page carry `noindex`; actual blog publication dates remain unchanged. After a public deployment, recrawl requests and indexing reports can be managed in Google Search Console. Search engines and social platforms control when cached previews refresh.
