#!/usr/bin/env python3
"""Build WageTheft.law into ./public.

Usage:  python3 build.py
Needs:  pip install markdown

Content lives in src/:
  src/site.json        firm details, intake link, phone, nav
  src/faq.json         questions used on the homepage and the FAQ page
  src/pages/*.html     hand-written pages (first line is a JSON header comment)
  src/articles/*.md    articles (front matter between --- lines)
  src/static/          CSS and other files copied as-is

Every article file with `status: published` is built and listed. Use
`status: draft` to keep a file out of the live site.
"""
import datetime as dt
import html
import json
import re
import shutil
from pathlib import Path

import markdown

ROOT = Path(__file__).parent
SRC = ROOT / "src"
OUT = ROOT / "public"

SITE = json.loads((SRC / "site.json").read_text())
FAQ = json.loads((SRC / "faq.json").read_text())
BASE = SITE["url"].rstrip("/")
ESC = html.escape



# Accessibility options: applied before first paint so saved settings don't flash.
A11Y_HEAD = """<script>try{var s=JSON.parse(localStorage.getItem('a11y')||'{}')||{},r=document.documentElement;for(var k in s){if(k==='size'){if(s.size&&s.size!==100)r.style.fontSize=s.size+'%'}else if(s[k])r.classList.add('a11y-'+k)}}catch(e){}</script>"""

GA_ID = SITE.get("ga_id", "")
GA_HEAD = (f"""<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());if(navigator.globalPrivacyControl){{gtag('set','allow_ad_personalization_signals',false);}}gtag('config','{GA_ID}');document.addEventListener('click',function(e){{var a=e.target.closest&&e.target.closest('a[href]');if(!a)return;var h=a.href||'';if(h.indexOf('lawbrokr.com')>-1||h.indexOf('cliogrow.com/intake')>-1){{gtag('event','generate_lead',{{method:'intake_form',link_url:h,link_text:(a.textContent||'').trim().slice(0,100),page_path:location.pathname}});}}else if(h.indexOf('tel:')===0){{gtag('event','phone_click',{{link_url:h,page_path:location.pathname}});}}}},true);</script>""" if GA_ID else "")


A11Y_ICON = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="currentColor">'
    '<circle cx="12" cy="4" r="2.2"/>'
    '<path d="M4 7.6c2.6.7 5.3 1 8 1s5.4-.3 8-1l.5 1.9c-2 .5-4.1.9-6.2 1.1v3.2l1.9 7.6-1.9.5L12.6 14h-1.2l-1.7 7.9-1.9-.5 1.9-7.6v-3.2c-2.1-.2-4.2-.6-6.2-1.1z"/>'
    "</svg>"
)

A11Y_WIDGET = f"""
<div class="a11y" id="a11y">
  <button class="a11y-toggle" type="button" aria-expanded="false" aria-controls="a11y-panel" aria-label="Accessibility options">{A11Y_ICON}</button>
  <div class="a11y-panel" id="a11y-panel" role="dialog" aria-labelledby="a11y-title" hidden>
    <div class="a11y-head">
      <p class="a11y-title" id="a11y-title">Accessibility options</p>
      <button class="a11y-close" type="button" aria-label="Close accessibility options">Close</button>
    </div>
    <div class="a11y-size">
      <span id="a11y-size-label">Text size</span>
      <div role="group" aria-labelledby="a11y-size-label">
        <button type="button" data-size="-1" aria-label="Make text smaller">A&minus;</button>
        <output id="a11y-size-val" aria-live="polite">100%</output>
        <button type="button" data-size="1" aria-label="Make text larger">A+</button>
      </div>
    </div>
    <button class="a11y-opt" type="button" data-opt="contrast" aria-pressed="false">High contrast</button>
    <button class="a11y-opt" type="button" data-opt="readable" aria-pressed="false">Readable font</button>
    <button class="a11y-opt" type="button" data-opt="spacing" aria-pressed="false">Extra spacing</button>
    <button class="a11y-opt" type="button" data-opt="links" aria-pressed="false">Highlight links</button>
    <button class="a11y-opt" type="button" data-opt="still" aria-pressed="false">Pause animations</button>
    <button class="a11y-reset" type="button">Reset all</button>
    <p class="a11y-link"><a href="/accessibility/">Accessibility statement</a></p>
  </div>
</div>
<script src="/a11y.js" defer></script>"""

# ---------- helpers ----------

def page_url(slug):
    return f"{BASE}/" if not slug else f"{BASE}/{slug}/"


def org_schema():
    s = SITE
    return {
        "@type": ["LegalService", "Attorney"],
        "@id": f"{BASE}/#firm",
        "name": s["name"],
        "alternateName": s["alt_names"],
        "legalName": s["firm"],
        "url": f"{BASE}/",
        "telephone": s["phone_e164"],
        "description": s["description"],
        "areaServed": {"@type": "State", "name": "California"},
        "knowsAbout": s["knows_about"],
        "address": [
            {
                "@type": "PostalAddress",
                "streetAddress": o["street"],
                "addressLocality": o["city"],
                "addressRegion": "CA",
                "postalCode": o["zip"],
                "addressCountry": "US",
            }
            for o in s["offices"]
        ],
        "employee": {"@id": f"{BASE}/about/#ryan"},
        "parentOrganization": {"@type": "LegalService", "@id": s["firm_id"], "name": s["firm_brand"], "legalName": s["firm"], "url": s["firm_url"]},
    }


def person_schema():
    return {
        "@type": "Person",
        "@id": f"{BASE}/about/#ryan",
        "name": "Ryan Stygar",
        "alternateName": "Attorney Ryan",
        "jobTitle": "Employment Attorney",
        "worksFor": {"@id": f"{BASE}/#firm"},
        "url": f"{BASE}/about/",
        "image": f"{BASE}/ryan-stygar.jpg",
        "sameAs": SITE["ryan_links"],
    }


def faq_schema(items):
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q["q"],
                "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", q["a"])},
            }
            for q in items
        ],
    }


def breadcrumb_schema(trail):
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": url}
            for i, (name, url) in enumerate(trail)
        ],
    }


def faq_html(items):
    out = ['<div class="faq">']
    for q in items:
        out.append(
            f'<details><summary>{ESC(q["q"])}</summary><div class="answer">{q["a"]}</div></details>'
        )
    out.append("</div>")
    return "\n".join(out)


def intake_button(label=None, cls="btn"):
    return f'<a class="{cls}" href="{SITE["intake_url"]}">{label or SITE["intake_label"]}</a>'


def wordmark_html():
    a, b, c = SITE["wordmark"]
    return f'{a}<span class="wm-mid">{b}</span>{c}'


def claim_cards_html(articles):
    published = {a["slug"] for a in articles}
    out = ['<ul class="claims">']
    for c in SITE["claims"]:
        if c["slug"] in published:
            more = f'<a class="more" href="/articles/{c["slug"]}/">Read the guide<span aria-hidden="true"> &rarr;</span></a>'
        else:
            more = f'<a class="more" href="{SITE["intake_url"]}">Get a free case review<span aria-hidden="true"> &rarr;</span></a>'
        out.append(
            f'<li class="panel"><span class="tag">{ESC(c["tag"])}</span><h3>{ESC(c["title"])}</h3><p>{ESC(c["text"])}</p>{more}</li>'
        )
    out.append("</ul>")
    return "\n".join(out)


# ---------- layout ----------

def nav_html(current):
    links = []
    for item in SITE["nav"]:
        cur = ' aria-current="page"' if item["slug"] == current else ""
        links.append(f'<a href="/{item["slug"]}/"{cur}>{item["label"]}</a>')
    links.append(intake_button(cls="btn btn-small"))
    return "\n".join(links)


def footer_html():
    s = SITE
    offices = "".join(
        f'<address><strong>{o["label"]}</strong><br>{o["street"]}<br>{o["city"]}, CA {o["zip"]}</address>'
        for o in s["offices"]
    )
    year = dt.date.today().year
    return f"""
<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div>
        <a class="wordmark" href="/">{wordmark_html()}</a>
        <p style="margin-top:14px">Wage theft cases for California workers, from the employment attorneys behind <a href="{s['suemyboss_url']}">SueMyBoss.Law</a>.</p>
        <p><a href="tel:{s['phone_e164']}">{s['phone_display']}</a></p>
      </div>
      <div>
        <h3>Offices</h3>
        {offices}
      </div>
      <div>
        <h3>Learn</h3>
        <ul>
          <li><a href="/articles/">Know your rights: wage guides</a></li>
          <li><a href="/class-actions/">Wage theft class actions</a></li>
          <li><a href="/how-it-works/">How it works</a></li>
          <li><a href="/faq/">FAQ</a></li>
          <li><a href="/about/">About Attorney Ryan</a></li>
          <li><a href="/legal/">Disclaimer and privacy</a></li>
          <li><a href="/accessibility/">Accessibility</a></li>
        </ul>
      </div>
    </div>
    <p class="other-sites">Our other sites: {" &middot; ".join(f'<a href="{u}">{n}</a>' for n, u in s["other_sites"])}</p>
    <div class="disclaimer">
      <p><strong>ATTORNEY ADVERTISING.</strong> The choice of a lawyer is an important decision which should not be made on ads alone. {s['trade_name_line']} The attorney responsible for this website is Ryan Stygar, {s['firm']}, {s['offices'][0]['street']}, {s['offices'][0]['city']}, CA {s['offices'][0]['zip']}.</p>
      <p>This website provides general information, not legal advice for your situation. Visiting this site, reading it, or contacting us does not create an attorney-client relationship. Prior results do not guarantee a similar outcome.</p>
      <p>&copy; {year} {s['firm']}. All rights reserved.</p>
    </div>
  </div>
</footer>
<div class="mobile-cta">{intake_button()}</div>"""


def render(*, slug, title, description, body, schema=None, og_type="website", current=None):
    url = page_url(slug)
    graph = [org_schema()]
    if schema:
        graph.extend(schema)
    ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, indent=1)
    full_title = title if slug == "" else f"{title} | {SITE['name']}"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{ESC(full_title)}</title>
<meta name="description" content="{ESC(description)}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{SITE['name']}">
<meta property="og:title" content="{ESC(title)}">
<meta property="og:description" content="{ESC(description)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}/og.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#141414">
{A11Y_HEAD}
{GA_HEAD}
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preload" href="/bangers.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/work-sans-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">
{ld}
</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap">
    <a class="wordmark" href="/" aria-label="{SITE['name']} home">{wordmark_html()}<small>A SueMyBoss.Law resource &middot; California</small></a>
    <button class="nav-toggle" aria-expanded="false" aria-controls="nav">Menu</button>
    <nav class="nav" id="nav" aria-label="Main">
{nav_html(current)}
    </nav>
  </div>
</header>
<main id="main">
{body}
</main>
{footer_html()}
{A11Y_WIDGET}
<script>
(function(){{var b=document.querySelector('.nav-toggle'),n=document.getElementById('nav');
b.addEventListener('click',function(){{var o=n.classList.toggle('open');b.setAttribute('aria-expanded',o);}});}})();
</script>
</body>
</html>
"""


# ---------- content ----------

def fill_tokens(text, articles):
    s = SITE
    reps = {
        "{{INTAKE_URL}}": s["intake_url"],
        "{{INTAKE_BUTTON}}": intake_button(),
        "{{INTAKE_BUTTON_LIGHT}}": intake_button(cls="btn btn-light"),
        "{{INTAKE_BUTTON_GHOST}}": intake_button(cls="btn btn-ghost"),
        "{{CLAIM_CARDS}}": claim_cards_html(articles),
        "{{PHONE_DISPLAY}}": s["phone_display"],
        "{{PHONE_E164}}": s["phone_e164"],
        "{{FAQ_HOME}}": faq_html([q for q in FAQ if q.get("home")]),
        "{{FAQ_ALL}}": faq_html(FAQ),
        "{{ARTICLE_LIST}}": article_list_html(articles),
        "{{ARTICLE_LIST_RECENT}}": article_list_html(articles[:3]),
        "{{BOOK_URL}}": s["book_url"],
        "{{SUEMYBOSS_URL}}": s["suemyboss_url"],
    }
    for k, v in reps.items():
        text = text.replace(k, v)
    return text


def parse_page(path):
    raw = path.read_text()
    m = re.match(r"<!--\s*(\{.*?\})\s*-->\s*", raw, re.S)
    if not m:
        raise SystemExit(f"{path}: missing JSON header comment")
    return json.loads(m.group(1)), raw[m.end():]


def parse_article(path):
    raw = path.read_text()
    m = re.match(r"---\n(.*?)\n---\n", raw, re.S)
    if not m:
        raise SystemExit(f"{path}: missing front matter")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    meta["slug"] = meta.get("slug") or path.stem
    meta["body_md"] = raw[m.end():]
    meta.setdefault("updated", meta["date"])
    meta.setdefault("status", "published")
    return meta


def fmt_date(iso):
    d = dt.date.fromisoformat(iso)
    return d.strftime("%B %-d, %Y")


def article_list_html(articles):
    if not articles:
        return "<p>New guides are on the way.</p>"
    items = []
    for a in articles:
        items.append(
            f'<li><a href="/articles/{a["slug"]}/"><time datetime="{a["date"]}">{fmt_date(a["date"])}</time>'
            f'<h3>{ESC(a["title"])}</h3><p>{ESC(a["description"])}</p></a></li>'
        )
    return '<ul class="article-list">' + "".join(items) + "</ul>"


def build_article(a):
    md = markdown.Markdown(extensions=["tables", "attr_list", "md_in_html", "toc"])
    body_html = fill_tokens(md.convert(a["body_md"]), [])
    url = f"{BASE}/articles/{a['slug']}/"
    updated_line = ""
    if a["updated"] != a["date"]:
        updated_line = f' &middot; Updated <time datetime="{a["updated"]}">{fmt_date(a["updated"])}</time>'
    body = f"""
<section class="page-hero"><div class="wrap">
  <h1>{ESC(a['title'])}</h1>
  <p>{ESC(a['description'])}</p>
  <p class="meta">By <a href="/about/">Ryan Stygar, Employment Attorney</a> &middot; <time datetime="{a['date']}">{fmt_date(a['date'])}</time>{updated_line}</p>
</div></section>
<article class="prose"><div class="wrap">
{body_html}
<div class="callout">
  <h3>Think you were shorted?</h3>
  <p>Tell us what happened. A free case review takes a few minutes, and we'll look at whether your coworkers were shorted the same way.</p>
  {intake_button()}
</div>
<p class="fine">This article is general information about California and federal law as of its date, not legal advice for your situation. Laws change, and the right move depends on your facts.</p>
</div></article>"""
    schema = [
        {
            "@type": "Article",
            "headline": a["title"],
            "description": a["description"],
            "datePublished": a["date"],
            "dateModified": a["updated"],
            "author": {"@id": f"{BASE}/about/#ryan"},
            "publisher": {"@id": f"{BASE}/#firm"},
            "mainEntityOfPage": url,
            "inLanguage": "en-US",
        },
        person_schema(),
        breadcrumb_schema([("Home", f"{BASE}/"), ("Guides", f"{BASE}/articles/"), (a["title"], url)]),
    ]
    return render(
        slug=f"articles/{a['slug']}",
        title=a["title"],
        description=a["description"],
        body=body,
        schema=schema,
        og_type="article",
        current="articles",
    )


def write(rel, content):
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    for f in (SRC / "static").iterdir():
        shutil.copy(f, OUT / f.name)

    articles = [parse_article(p) for p in sorted((SRC / "articles").glob("*.md"))]
    articles = [a for a in articles if a["status"] == "published"]
    articles.sort(key=lambda a: a["date"], reverse=True)

    sitemap = []
    today = dt.date.today().isoformat()

    for p in sorted((SRC / "pages").glob("*.html")):
        meta, body = parse_page(p)
        slug = meta["slug"]
        body = fill_tokens(body, articles)
        schema = []
        if meta.get("faq") == "all":
            schema.append(faq_schema(FAQ))
        elif meta.get("faq") == "home":
            schema.append(faq_schema([q for q in FAQ if q.get("home")]))
        if meta.get("person"):
            schema.append(person_schema())
        if slug:
            schema.append(breadcrumb_schema([("Home", f"{BASE}/"), (meta["title"], page_url(slug))]))
        out = render(
            slug=slug,
            title=meta["title"],
            description=meta["description"],
            body=body,
            schema=schema,
            current=slug.split("/")[0] if slug else None,
        )
        if slug == "404":
            write("404.html", out)
            continue
        write(f"{slug}/index.html" if slug else "index.html", out)
        sitemap.append((page_url(slug), meta.get("updated", today)))

    for a in articles:
        write(f"articles/{a['slug']}/index.html", build_article(a))
        sitemap.append((f"{BASE}/articles/{a['slug']}/", a["updated"]))

    urls = "\n".join(
        f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>" for u, d in sitemap
    )
    write(
        "sitemap.xml",
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n',
    )
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")

    # llms.txt: a plain-text map of the site for AI answer engines
    lines = [
        f"# {SITE['name']}",
        "",
        f"> {SITE['description']}",
        "",
        f"{SITE['name']} is operated by {SITE['firm']}, a California employment law firm. "
        "Attorney responsible: Ryan Stygar. Phone: " + SITE["phone_display"] + ".",
        "",
        "## Pages",
    ]
    for p in sorted((SRC / "pages").glob("*.html")):
        meta, _ = parse_page(p)
        if meta["slug"] == "404":
            continue
        lines.append(f"- [{meta['title']}]({page_url(meta['slug'])}): {meta['description']}")
    lines += ["", "## Guides"]
    for a in articles:
        lines.append(f"- [{a['title']}]({BASE}/articles/{a['slug']}/): {a['description']}")
    write("llms.txt", "\n".join(lines) + "\n")

    print(f"Built {len(sitemap)} pages into {OUT}")


if __name__ == "__main__":
    main()
