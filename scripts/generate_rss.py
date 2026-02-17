import re
import random
import datetime as dt
from pathlib import Path
import fitz  # PyMuPDF

PDF_DIR = Path("pdfs")
OUT_DIR = Path("site")
RSS_PATH = OUT_DIR / "rss.xml"

MAX_SENTENCES = 4
MIN_SENTENCES = 2

CHANNEL_TITLE = "Daily PDF Quote"
CHANNEL_DESC = "Short quotes selected automatically from PDFs."
# Replace later with your GitHub Pages URL once enabled; RSS still works without it.
CHANNEL_LINK = "https://example.com"

def clean_text(t: str) -> str:
    t = t.replace("\u00ad", "")
    t = re.sub(r"\s+", " ", t).strip()
    return t

def extract_text(pdf_path: Path, max_pages=12) -> str:
    doc = fitz.open(pdf_path)
    pages = min(len(doc), max_pages)
    chunks = []
    for i in range(pages):
        text = doc.load_page(i).get_text("text")
        if text:
            chunks.append(text)
    return clean_text("\n".join(chunks))

def split_sentences(text: str):
    s = re.split(r'(?<=[.!?])\s+', text)
    return [x.strip() for x in s if x.strip()]

def pick_quote(sentences):
    # Prefer sentences that look like prose (not URLs/numbers-heavy)
    candidates = []
    for i, sent in enumerate(sentences):
        if len(sent) < 40 or len(sent) > 220:
            continue
        if "http" in sent.lower() or "www." in sent.lower():
            continue
        if re.search(r"\d{3,}", sent):
            continue
        candidates.append(i)

    if not candidates:
        candidates = list(range(min(len(sentences), 50)))

    start_idx = random.choice(candidates)
    for n in range(MAX_SENTENCES, MIN_SENTENCES - 1, -1):
        chunk = " ".join(sentences[start_idx:start_idx+n]).strip()
        if 180 <= len(chunk) <= 650:
            return chunk

    return sentences[start_idx][:650]

def xml_escape(s: str) -> str:
    return (s.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;"))

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if not pdfs:
        raise SystemExit("No PDFs found in pdfs/")

    # Deterministic "daily rotation"
    today = dt.date.today().toordinal()
    pdf = pdfs[today % len(pdfs)]

    text = extract_text(pdf)
    sentences = split_sentences(text)
    quote = pick_quote(sentences) if sentences else "No suitable quote found today."

    now = dt.datetime.utcnow()
    pubdate = now.strftime("%a, %d %b %Y %H:%M:%S GMT")

    # Link to the PDF in your GitHub repo (works even before Pages is enabled)
    # TODO: replace <your-username> and <your-repo>
    pdf_link = f"https://github.com/Levantinejames/bahaiRSS/blob/main/pdfs/{pdf.name}"

    description_html = f"<p>{xml_escape(quote)}</p><p><em>Source:</em> {xml_escape(pdf.name)}</p>"

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>{xml_escape(CHANNEL_TITLE)}</title>
  <link>{xml_escape(CHANNEL_LINK)}</link>
  <description>{xml_escape(CHANNEL_DESC)}</description>
  <lastBuildDate>{xml_escape(pubdate)}</lastBuildDate>
  <item>
    <title>{xml_escape('Quote from ' + pdf.stem)}</title>
    <link>{xml_escape(pdf_link)}</link>
    <guid isPermaLink="false">{xml_escape(pdf.name + '-' + now.isoformat())}</guid>
    <pubDate>{xml_escape(pubdate)}</pubDate>
    <description><![CDATA[{description_html}]]></description>
  </item>
</channel>
</rss>
"""
    RSS_PATH.write_text(rss, encoding="utf-8")
    print(f"Wrote {RSS_PATH}")

if __name__ == "__main__":
    main()
