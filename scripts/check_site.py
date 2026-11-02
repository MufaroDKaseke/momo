"""Validate the static site without external dependencies. Run: python scripts/check_site.py"""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ROUTES = {
    '/': 'index.html',
    '/blog/': 'blog/index.html',
    '/builds/': 'builds/index.html',
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
    for svg in ('cat-logo.svg', 'cat-astronaut.svg', 'cat-peek.svg', 'cat-sleep.svg', 'paw.svg', 'git-branches.svg', 'builds-map.svg'):
        ET.parse(ROOT / 'img' / svg)
    sitemap = ET.parse(ROOT / 'sitemap.xml')
    locations = {node.text for node in sitemap.findall('.//{*}loc')}
    for route in list(ROUTES)[:5]:
        assert 'https://momo.co.zw' + route in locations, f'{route}: missing from sitemap'
    assert pages['/blog/2025/4/intro_to_git_and_github_101.html'].title.startswith('Git It Together:'), 'Git post title regression'
    print(f'PASS: {len(pages)} pages, {link_count} links, local assets and anchors, image dimensions, ARIA references, unique titles, structured data, SVGs and sitemap.')


if __name__ == '__main__':
    main()
