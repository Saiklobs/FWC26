import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup

FEEDS = [
    "https://feeds.bbci.co.uk/sport/football/rss.xml",
    "https://www.goal.com/feeds/en/news",
    "https://www.espn.com/espn/rss/soccer/news",
]

KEYWORDS = [
    "world cup", "fifa", "2026", "worldcup",
    "squad", "match", "goal", "group",
    "team", "player", "stadium", "mexico",
    "canada", "usa", "messi", "ronaldo",
    "tactics", "lineup", "qualifier"
]

def fetch_articles():
    articles = []
    for feed_url in FEEDS:
        try:
            r = requests.get(feed_url, timeout=10,
                headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(r.content, "xml")
            items = soup.findAll("item")
            for item in items[:10]:
                title = item.find("title")
                desc = item.find("description")
                link = item.find("link")
                pub = item.find("pubDate")
                if not title:
                    continue
                title_text = title.text.strip()
                desc_text = desc.text.strip() if desc else ""
                combined = (title_text + " " + desc_text).lower()
                if any(k in combined for k in KEYWORDS):
                    articles.append({
                        "title": title_text,
                        "desc": desc_text[:200] + "..." if len(desc_text) > 200 else desc_text,
                        "link": link.text.strip() if link else "#",
                        "date": pub.text.strip() if pub else datetime.now().strftime("%B %d, %Y"),
                        "source": feed_url.split("/")[2]
                    })
        except Exception as e:
            print(f"Error: {e}")
    seen = set()
    unique = []
    for a in articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)
    return unique[:12]

def build_news_html(articles):
    if not articles:
        return "<p style='color:#888;text-align:center;padding:40px'>No news right now. Check back soon.</p>"
    html = ""
    for a in articles:
        html += f"""
        <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:20px;margin-bottom:16px;">
          <div style="font-size:0.7rem;color:#f0b429;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">
            ⚽ {a['source']} · {a['date']}
          </div>
          <h3 style="font-size:1rem;color:#ffffff;margin:0 0 10px 0;line-height:1.4;">
            <a href="{a['link']}" target="_blank" rel="noopener" style="color:inherit;text-decoration:none;">
              {a['title']}
            </a>
          </h3>
          <p style="font-size:0.85rem;color:#8899bb;margin:0;line-height:1.6;">
            {a['desc']}
          </p>
          <a href="{a['link']}" target="_blank" rel="noopener"
            style="display:inline-block;margin-top:12px;font-size:0.75rem;color:#f0b429;font-weight:700;letter-spacing:1px;">
            READ MORE →
          </a>
        </div>"""
    return html

def update_html(articles):
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()
    timestamp = datetime.now().strftime("%B %d, %Y at %H:%M UTC")
    news_html = build_news_html(articles)
    new_section = f"""<!-- AUTO-NEWS-START -->
    <section style="max-width:900px;margin:40px auto;padding:0 20px;">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-bottom:24px;">
        <h2 style="font-family:'Bebas Neue',sans-serif;font-size:2rem;color:#f0b429;letter-spacing:3px;margin:0;">
          ⚡ LATEST WORLD CUP NEWS
        </h2>
        <span style="font-size:0.7rem;color:#556677;letter-spacing:1px;">
          🔄 Updated: {timestamp}
        </span>
      </div>
      {news_html}
    </section>
    <!-- AUTO-NEWS-END -->"""
    if "<!-- AUTO-NEWS-START -->" in content:
        content = re.sub(
            r'<!-- AUTO-NEWS-START -->.*?<!-- AUTO-NEWS-END -->',
            new_section,
            content,
            flags=re.DOTALL
        )
    else:
        content = content.replace("</body>", new_section + "\n</body>")
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Done! Added {len(articles)} articles")

if __name__ == "__main__":
    print("🔍 Fetching World Cup news...")
    articles = fetch_articles()
    print(f"📰 Found {len(articles)} articles")
    update_html(articles)
