"""Validate the static site without external dependencies. Run: python scripts/check_site.py"""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import struct
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ROUTES = {
    '/': 'index.html',
    '/blog/': 'blog/index.html',
    '/builds/': 'builds/index.html',
    '/blog/2026/11/decoys_and_traps_built_for_robots.html': 'blog/2026/11/decoys_and_traps_built_for_robots.html',
    '/blog/2025/4/intro_to_git_and_github_101.html': 'blog/2025/4/intro_to_git_and_github_101.html',
    '/blog/2024/5/tech_job_market_who_survives.html': 'blog/2024/5/tech_job_market_who_survives.html',
    '/404.html': '404.html',
}


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.ids = []
        self.links = []
        self.assets = []
        self.references = []
        self.images = []
        self.svg_references = []
        self.metadata = {}
        self.headings = []
        self.canonical = None
        self.og_url = None
        self.title = ''
        self.in_title = False
        self.jsonld = []
        self.in_jsonld = False
        self.json_text = ''
        self.feed(path.read_text(encoding='utf-8-sig'))

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.append(a['id'])
        if tag in ('h1', 'h2', 'h3'):
            self.headings.append(tag)
        if tag == 'a':
            self.links.append(a.get('href', ''))
            if a.get('target') == '_blank':
                assert 'noopener' in a.get('rel', ''), f'{self.path}: unsafe new tab'
        if tag == 'link':
            if a.get('rel') == 'canonical':
                self.canonical = a['href']
            if a.get('rel') in ('stylesheet', 'icon'):
                self.assets.append(a['href'])
        if tag == 'meta' and a.get('property') == 'og:url':
            self.og_url = a['content']
        if tag == 'meta':
            key = a.get('name') or a.get('property')
            if key:
                self.metadata.setdefault(key, []).append(a.get('content', ''))
        if tag == 'script':
            self.in_jsonld = a.get('type') == 'application/ld+json'
            if a.get('src'):
                self.assets.append(a['src'])
        if tag == 'img':
            self.images.append(a)
            self.assets.append(a['src'])
            for src in a.get('srcset', '').split(','):
                if src.strip():
                    self.assets.append(src.strip().split()[0])
        if tag == 'use' and a.get('href', '').startswith('/'):
            self.assets.append(a['href'])
            self.svg_references.append(a['href'])
        if tag == 'title':
            self.in_title = True
        for ref in ('aria-controls', 'aria-labelledby', 'aria-describedby'):
            self.references.extend(a.get(ref, '').split())

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.in_jsonld:
            self.json_text += data

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        if tag == 'script' and self.in_jsonld:
            self.jsonld.append(json.loads(self.json_text))
            self.in_jsonld = False
            self.json_text = ''


def resolve_local(page_path, url):
    path = unquote(urlsplit(url).path)
    target = (ROOT / path.lstrip('/')) if path.startswith('/') else page_path.parent / path
    if not path:
        target = page_path
    if target.is_dir():
        target /= 'index.html'
    return target.resolve()


def main():
    pages = {route: Page(ROOT / path) for route, path in ROUTES.items()}
    by_path = {page.path.resolve(): page for page in pages.values()}
    titles = [page.title for page in pages.values()]
    assert len(titles) == len(set(titles)), 'Duplicate browser titles'
    link_count = 0
    for route, page in pages.items():
        assert page.headings.count('h1') == 1, f'{route}: expected one H1'
        duplicates = [id for id, count in Counter(page.ids).items() if count > 1]
        assert not duplicates, f'{route}: duplicate IDs {duplicates}'
        assert page.canonical == 'https://momo.co.zw' + route, f'{route}: canonical'
        assert page.og_url == page.canonical, f'{route}: Open Graph URL'
        assert page.jsonld or route == '/404.html', f'{route}: missing structured data'
        for ref in page.references:
            assert ref in page.ids, f'{route}: missing ARIA target {ref}'
        for image in page.images:
            assert 'alt' in image, f'{route}: missing image alternative'
            assert int(image.get('width', 0)) > 0 and int(image.get('height', 0)) > 0, f'{route}: image dimensions'
        for asset in page.assets:
            if urlsplit(asset).scheme or urlsplit(asset).netloc:
                continue
            assert resolve_local(page.path, asset).is_file(), f'{route}: missing asset {asset}'
        for reference in page.svg_references:
            target = resolve_local(page.path, reference)
            symbols = {element.attrib.get('id') for element in ET.parse(target).iter()}
            assert urlsplit(reference).fragment in symbols, f'{route}: missing SVG symbol {reference}'
        for href in page.links:
            assert href and href != '#', f'{route}: placeholder link'
            link_count += 1
            parsed = urlsplit(href)
            if parsed.scheme or parsed.netloc:
                continue
            target = resolve_local(page.path, href)
            assert target.is_file(), f'{route}: broken link {href}'
            if parsed.fragment:
                target_page = by_path.get(target) or Page(target)
                assert unquote(parsed.fragment) in target_page.ids, f'{route}: broken anchor {href}'
    for svg in (ROOT / 'img').glob('*.svg'):
        ET.parse(svg)
    sitemap = ET.parse(ROOT / 'sitemap.xml')
    locations = {node.text for node in sitemap.findall('.//{*}loc')}
    for route in [route for route in ROUTES if route != '/404.html']:
        assert 'https://momo.co.zw' + route in locations, f'{route}: missing from sitemap'
    config = json.loads((ROOT / 'content/seo.json').read_text(encoding='utf-8'))
    origin = config['origin']
    person_id = origin + '/#person'
    for expected in config['pages']:
        page = pages[expected['path']]
        url = origin + expected['path']
        image_url = origin + expected['image']
        assert page.title == expected['title'], f'{url}: stale title'
        expected_meta = {
            'description': expected['description'], 'author': config['name'],
            'og:title': expected['title'], 'og:description': expected['description'],
            'og:image': image_url, 'og:image:secure_url': image_url,
            'og:image:type': 'image/png', 'og:image:width': '1200', 'og:image:height': '630',
            'og:image:alt': expected['imageAlt'], 'og:site_name': config['siteName'],
            'twitter:card': 'summary_large_image', 'twitter:title': expected['title'],
            'twitter:description': expected['description'], 'twitter:image': image_url,
            'twitter:image:alt': expected['imageAlt'],
        }
        for key, value in expected_meta.items():
            assert page.metadata.get(key) == [value], f'{url}: missing, duplicate or stale {key}'
        assert 'noindex' not in page.metadata['robots'][0], f'{url}: accidentally excluded from indexing'
        raster = ROOT / expected['image'].lstrip('/')
        image = raster.read_bytes()
        assert image[:8] == b'\x89PNG\r\n\x1a\n', f'{url}: share image is not PNG'
        assert struct.unpack('>II', image[16:24]) == (1200, 630), f'{url}: incorrect share image dimensions'
        assert len(image) < 500_000, f'{url}: unoptimized share image'
        graph = page.jsonld[0]['@graph']
        person = next(node for node in graph if node.get('@id') == person_id)
        assert person['name'] == config['name'], f'{url}: inconsistent author identity'
        assert person['image'] == origin + config['portrait'], f'{url}: Person requires the real portrait'
        assert 'worksFor' not in person, f'{url}: stale current employer'
        assert any(node.get('@type') == 'WebSite' for node in graph), f'{url}: missing site identity'
        if expected['kind'] == 'article':
            article = next(node for node in graph if node.get('@id') == url + '#article')
            assert article['headline'] == expected['headline'], f'{url}: original headline changed'
            assert article['datePublished'] == expected['published'], f'{url}: publication date changed'
            assert article['author']['@id'] == person_id, f'{url}: disconnected author'
            assert article['image']['url'] == image_url, f'{url}: stale article image'
            assert any(node.get('@type') == 'BreadcrumbList' for node in graph), f'{url}: missing breadcrumbs'
    for name, size in [('favicon-48.png', 48), ('favicon-96.png', 96), ('apple-touch-icon.png', 180)]:
        image = (ROOT / 'img' / name).read_bytes()
        assert struct.unpack('>II', image[16:24]) == (size, size), f'{name}: incorrect dimensions'
    legacy = Page(ROOT / 'blog/post.html')
    assert legacy.metadata['robots'] == ['noindex, follow'], 'Legacy example must not be indexed'
    assert pages['/404.html'].metadata['robots'] == ['noindex, follow'], '404 must not be indexed'
    robots = (ROOT / 'robots.txt').read_text(encoding='utf-8')
    assert 'Sitemap: ' + origin + '/sitemap.xml' in robots, 'Sitemap not declared in robots.txt'
    assert 'Disallow:' not in robots, 'Unexpected crawl restrictions'
    sitemap_urls = sitemap.findall('./{*}url')
    assert {node.find('{*}loc').text for node in sitemap_urls} == {origin + page['path'] for page in config['pages']}, 'Sitemap includes non-content pages'
    for node in sitemap_urls:
        assert node.find('{http://www.google.com/schemas/sitemap-image/1.1}image/{http://www.google.com/schemas/sitemap-image/1.1}loc') is not None, 'Missing sitemap image'
    print(f'PASS: {len(pages)} pages, {link_count} links, assets/anchors, metadata, {len(config["pages"])} raster share images, favicons, author graphs, SVGs, indexing controls and image sitemap.')


if __name__ == '__main__':
    main()
