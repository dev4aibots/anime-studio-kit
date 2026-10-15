#!/usr/bin/env python3
"""fonts.py — download a Google Font for the graphics, so its typeface renders offline and the same every time.
  fonts.py add "Geist:wght@400;500;600;700;800" "Instrument Serif:ital@0;1" ["Inter:ital,wght@0,400;0,700"] …
  fonts.py list
Fetches the css2 API as a current Chrome (to get woff2), keeps the latin + latin-ext subsets, downloads each file once
(variable fonts share one file across weights) into AI_EDITOR_HOME/vendor/fonts/, and appends the @font-face blocks to
fonts.css there with local urls (link.py copies them into each graphic). Faces already in fonts.css are skipped, so it
is safe to re-run. Google Fonts are OFL or Apache licensed: free in videos, ads and products."""
import hashlib, os, re, sys, urllib.parse, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aie
FONTS = aie.FONTS
CSS = os.path.join(FONTS, "fonts.css")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
KEEP = ("latin", "latin-ext")


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30).read()


def add(families):
    os.makedirs(FONTS, exist_ok=True)
    q = "&".join("family=" + urllib.parse.quote(f, safe=":;@,") for f in families)
    css = get(f"https://fonts.googleapis.com/css2?{q}&display=block").decode()
    have = open(CSS).read() if os.path.exists(CSS) else ""
    out, n_new, n_files = [], 0, 0
    for subset, body in re.findall(r"/\*\s*([\w-]+)\s*\*/\s*@font-face\s*{([^}]*)}", css):
        if subset not in KEEP:
            continue
        fam = re.search(r"font-family:\s*'([^']+)'", body).group(1)
        style = re.search(r"font-style:\s*(\w+)", body).group(1)
        weight = re.search(r"font-weight:\s*([\d ]+);", body).group(1).strip()
        tag = f"/* {subset} {fam}|{style}|{weight} */"
        if tag in have:
            continue
        url = re.search(r"url\((https://[^)]+)\)", body).group(1)
        name = f"{fam.replace(' ', '')}-{style}-{subset}-{hashlib.sha1(url.encode()).hexdigest()[:8]}.woff2"
        dst = os.path.join(FONTS, name)
        if not os.path.exists(dst):
            open(dst, "wb").write(get(url)); n_files += 1
        body = body.replace(url, "./" + name)
        out.append(f"{tag}\n@font-face {{{body}}}")
        n_new += 1
    if out:
        with open(CSS, "a") as f:
            f.write("\n" + "\n".join(out) + "\n")
    print(f"{n_new} faces added ({n_files} files downloaded) → {CSS}")


def main():
    a = sys.argv[1:]
    if a and a[0] in ("-h", "--help"):
        print(__doc__.strip()); sys.exit(0)
    if not a or a[0] not in ("add", "list"):
        sys.exit(__doc__)
    if a[0] == "list":
        css = open(CSS).read() if os.path.exists(CSS) else ""
        fams = sorted(set(re.findall(r"font-family:\s*'([^']+)'", css)))
        print("\n".join(fams))
    else:
        add(a[1:])


if __name__ == "__main__":
    main()
