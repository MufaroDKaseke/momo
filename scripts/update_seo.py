"""Render static SEO metadata from content/seo.json. Run after generating images."""
from pathlib import Path
from html import escape
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'content/seo.json').read_text(encoding='utf-8'))
ORIGIN = CONFIG['origin']
NAME = CONFIG['name']
PERSON_ID = ORIGIN + '/#person'
WEBSITE_ID = ORIGIN + '/#website'


def image_object(page):
    return {
        '@type': 'ImageObject', 'url': ORIGIN + page['image'],
        'contentUrl': ORIGIN + page['image'], 'width': 1200, 'height': 630,
        'caption': page['imageAlt'],
    }


def schema(page, source):
    url = ORIGIN + page['path']
    person = {
        '@type': 'Person', '@id': PERSON_ID, 'name': NAME,
        'alternateName': ['Momo', 'Mufaro Kaseke'], 'url': ORIGIN + '/',
        'image': ORIGIN + CONFIG['portrait'], 'jobTitle': CONFIG['jobTitle'],
        'description': 'Cloud & DevOps engineer based in Zimbabwe, building reliable AWS infrastructure and AI-powered products.',
        'sameAs': CONFIG['socialProfiles'],
    }
    website = {
        '@type': 'WebSite', '@id': WEBSITE_ID, 'url': ORIGIN + '/',
        'name': CONFIG['siteName'], 'alternateName': ['Mufaro D Kaseke', 'Momo Portfolio'],
        'inLanguage': 'en', 'publisher': {'@id': PERSON_ID},
    }
    kind = page['kind']
    web = {
        '@type': 'ProfilePage' if kind == 'profile' else 'CollectionPage' if kind in ('blog', 'builds') else 'WebPage',
        '@id': url, 'url': url, 'name': page['title'], 'description': page['description'],
        'inLanguage': 'en', 'isPartOf': {'@id': WEBSITE_ID},
        'primaryImageOfPage': image_object(page),
        'dateModified': CONFIG['modified'],
    }
    graph = [person, website, web]
    if kind == 'profile':
        web['mainEntity'] = {'@id': PERSON_ID}
    else:
        crumbs = [{'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': ORIGIN + '/'}]
        crumbs.append({'@type': 'ListItem', 'position': 2, 'name': 'Builds' if kind == 'builds' else 'Blog', 'item': ORIGIN + ('/builds/' if kind == 'builds' else '/blog/')})
        if kind == 'article':
            crumbs.append({'@type': 'ListItem', 'position': 3, 'name': page['headline'], 'item': url})
        breadcrumb_id = url + '#breadcrumbs'
        graph.append({'@type': 'BreadcrumbList', '@id': breadcrumb_id, 'itemListElement': crumbs})
        web['breadcrumb'] = {'@id': breadcrumb_id}
    if kind == 'blog':
        blog_id = url + '#blog'
        web['mainEntity'] = {'@id': blog_id}
        graph.append({
            '@type': 'Blog', '@id': blog_id, 'name': 'Momo Blog', 'url': url,
            'author': {'@id': PERSON_ID}, 'isPartOf': {'@id': WEBSITE_ID},
            'blogPost': [
                {'@type': 'BlogPosting', '@id': ORIGIN + item['path'] + '#article',
                 'headline': item['headline'], 'url': ORIGIN + item['path'],
                 'datePublished': item['published'], 'author': {'@id': PERSON_ID},
                 'image': image_object(item)}
                for item in CONFIG['pages'] if item['kind'] == 'article'
            ],
        })
    elif kind == 'builds':
        # Preserve the existing six-build catalog rather than maintaining a second list.
        old = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', source, re.S)[1])
        if '@graph' in old:
            listing = next(node for node in old['@graph'] if node.get('@type') == 'ItemList')
        else:
            listing = old['mainEntity']
        listing['@id'] = url + '#builds'
        web['mainEntity'] = {'@id': listing['@id']}
        graph.append(listing)
    elif kind == 'article':
        article_id = url + '#article'
        web['mainEntity'] = {'@id': article_id}
        graph.append({
            '@type': 'BlogPosting', '@id': article_id, 'url': url,
            'headline': page['headline'], 'description': page['description'],
            'datePublished': page['published'], 'dateModified': CONFIG['modified'],
            'mainEntityOfPage': {'@id': url}, 'isPartOf': {'@id': ORIGIN + '/blog/#blog'},
            'image': image_object(page), 'author': {'@id': PERSON_ID},
            'publisher': {'@id': PERSON_ID}, 'inLanguage': 'en', 'keywords': page['keywords'],
        })
    return {'@context': 'https://schema.org', '@graph': graph}


def meta(attribute, key, value):
    return f'  <meta {attribute}="{key}" content="{escape(str(value), quote=True)}">'


def head_metadata(page, source):
    url = ORIGIN + page['path']
    tags = [
        f'  <title>{escape(page["title"])}</title>',
        meta('name', 'description', page['description']),
        meta('name', 'author', NAME),
        meta('name', 'application-name', CONFIG['siteName']),
        f'  <link rel="canonical" href="{url}">',
        '  <link rel="icon" type="image/svg+xml" href="/img/cat-logo.svg">',
        '  <link rel="icon" type="image/png" sizes="96x96" href="/img/favicon-96.png">',
        '  <link rel="icon" type="image/png" sizes="48x48" href="/img/favicon-48.png">',
        '  <link rel="apple-touch-icon" sizes="180x180" href="/img/apple-touch-icon.png">',
        meta('property', 'og:title', page['title']),
        meta('property', 'og:description', page['description']),
        meta('property', 'og:type', 'article' if page['kind'] == 'article' else 'website'),
        meta('property', 'og:url', url),
        meta('property', 'og:site_name', CONFIG['siteName']),
        meta('property', 'og:locale', 'en_US'),
        meta('property', 'og:image', ORIGIN + page['image']),
        meta('property', 'og:image:secure_url', ORIGIN + page['image']),
        meta('property', 'og:image:type', 'image/png'),
        meta('property', 'og:image:width', 1200),
        meta('property', 'og:image:height', 630),
        meta('property', 'og:image:alt', page['imageAlt']),
        meta('name', 'twitter:card', 'summary_large_image'),
        meta('name', 'twitter:creator', '@KasekeMufaro'),
        meta('name', 'twitter:title', page['title']),
        meta('name', 'twitter:description', page['description']),
        meta('name', 'twitter:image', ORIGIN + page['image']),
        meta('name', 'twitter:image:alt', page['imageAlt']),
        meta('name', 'robots', 'noindex, follow' if page.get('noindex') else 'index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1'),
    ]
    if page['kind'] == 'article':
        tags += [meta('property', 'article:published_time', page['published']),
                 meta('property', 'article:modified_time', CONFIG['modified'])]
    if not page.get('noindex'):
        data = json.dumps(schema(page, source), ensure_ascii=False, indent=2).replace('</', '<\\/')
        tags.append('  <script type="application/ld+json">\n' + data + '\n  </script>')
    return '\n'.join(tags)


def update(page):
    file = ROOT / page['file']
    source = file.read_text(encoding='utf-8-sig')
    head_match = re.search(r'<head>(.*?)</head>', source, re.S)
    head = head_match[1]
    head = re.sub(r'\s*<title>.*?</title>', '', head, flags=re.S)
    head = re.sub(r'\s*<script\b[^>]*type="application/ld\+json"[^>]*>.*?</script>', '', head, flags=re.S)
    def keep_meta(match):
        value = match[0]
        if re.search(r'(?:name|property)="(?:description|author|application-name|robots|og:[^"]+|twitter:[^"]+|article:[^"]+)"', value):
            return ''
        return value
    head = re.sub(r'\s*<meta\b[^>]*>', keep_meta, head)
    head = re.sub(r'\s*<link\b[^>]*rel="(?:canonical|icon|apple-touch-icon)"[^>]*>', '', head)
    head = head.rstrip() + '\n' + head_metadata(page, source) + '\n'
    source = source[:head_match.start(1)] + head + source[head_match.end(1):]
    # Unify visible names without changing the historical alias in the graph.
    body_start = source.index('</head>') + len('</head>')
    source = source[:body_start] + source[body_start:].replace('Mufaro Kaseke', NAME)
    file.write_text(source, encoding='utf-8')


def main():
    for page in CONFIG['pages']:
        update(page)
    update({
        'file': '404.html', 'path': '/404.html', 'kind': 'page', 'noindex': True,
        'title': 'Page not found | ' + NAME,
        'description': 'This page could not be found. Return to Momo’s portfolio, blog or builds.',
        'image': CONFIG['pages'][0]['image'], 'imageAlt': CONFIG['pages'][0]['imageAlt'],
    })
    # The old unlinked example is kept accessible, but is not a real article.
    legacy = ROOT / 'blog/post.html'
    source = legacy.read_text(encoding='utf-8-sig')
    source = re.sub(r'<title>.*?</title>', '<title>Post template | Momo</title>', source, count=1, flags=re.S)
    source = re.sub(r'\s*<meta name="robots"[^>]*>', '', source)
    source = source.replace('</head>', '  <meta name="robots" content="noindex, follow">\n</head>', 1)
    legacy.write_text(source, encoding='utf-8')
    (ROOT / 'robots.txt').write_text('User-agent: *\nAllow: /\n\nSitemap: ' + ORIGIN + '/sitemap.xml\n', encoding='utf-8')
    ET.register_namespace('', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    ET.register_namespace('image', 'http://www.google.com/schemas/sitemap-image/1.1')
    namespace = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    image_ns = 'http://www.google.com/schemas/sitemap-image/1.1'
    sitemap = ET.Element(f'{{{namespace}}}urlset')
    for page in CONFIG['pages']:
        url = ET.SubElement(sitemap, f'{{{namespace}}}url')
        ET.SubElement(url, f'{{{namespace}}}loc').text = ORIGIN + page['path']
        ET.SubElement(url, f'{{{namespace}}}lastmod').text = CONFIG['modified']
        cover = ET.SubElement(url, f'{{{image_ns}}}image')
        ET.SubElement(cover, f'{{{image_ns}}}loc').text = ORIGIN + page['image']
    ET.indent(sitemap, space='  ')
    ET.ElementTree(sitemap).write(ROOT / 'sitemap.xml', encoding='utf-8', xml_declaration=True)
    print('Updated static SEO metadata, author identity, robots.txt, legacy noindex and image sitemap.')


if __name__ == '__main__':
    main()
