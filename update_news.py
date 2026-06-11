import requests
import re
import os
import json
from datetime import datetime
from bs4 import BeautifulSoup

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

FEEDS = [
    "https://feeds.bbci.co.uk/sport/football/rss.xml",
    "https://www.espn.com/espn/rss/soccer/news",
    "https://www.goal.com/feeds/en/news",
]

KEYWORDS = [
    "world cup", "fifa", "2026", "worldcup",
    "squad", "match", "goal", "group",
    "team", "player", "stadium", "mexico",
    "canada", "usa", "messi", "ronaldo",
    "tactics", "lineup", "qualifier"
]

def fetch_topics():
    topics = []
    for feed_url in FEEDS:
        try:
            r = requests.get(feed_url, timeout=10,
                headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(r.content, "xml")
            items = soup.find_all("item")
            for item in items[:8]:
                title = item.find("title")
                desc = item.find("description")
                if not title:
                    continue
                title_text = title.text.strip()
                desc_text = desc.text.strip() if desc else ""
                combined = (title_text + " " + desc_text).lower()
                if any(k in combined for k in KEYWORDS):
                    topics.append({
                        "title": title_text,
                        "desc": desc_text[:300] if desc_text else ""
                    })
        except Exception as e:
            print(f"Error fetching feed: {e}")
    seen = set()
    unique = []
    for t in topics:
        if t["title"] not in seen:
            seen.add(t["title"])
            unique.append(t)
    return unique[:6]

def write_article(topic):
    prompt = f"""You are a professional football journalist for FWC26 Live, a FIFA World Cup 2026 news website.

Write a complete, original, engaging football news article about this topic:
Title inspiration: {topic['title']}
Context: {topic['desc']}

Requirements:
- Write a catchy original headline (different from the inspiration)
- Write 3-4 paragraphs of original content (150-200 words total)
- Focus on FIFA World Cup 2026 angle
- Professional sports journalism tone
- 100% original — do not copy any source
- End with an exciting closing sentence

Respond in this exact JSON format:
{{
  "headline": "Your original headline here",
  "category": "One of: Match Preview / Team News / Tactics / Player Spotlight / Tournament Update",
  "body": "Full article text here with paragraphs separated by \\n\\n",
  "emoji": "One relevant emoji"
}}"""

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 600,
                "temperature": 0.8
            },
            timeout=30
        )
        data = r.json()
        text = data["choices"][0]["message"]["content"].strip()
        text = re.sub(r'```json|```', '', text).strip()
        article = json.loads(text)
        return article
    except Exception as e:
        print(f"Groq error: {e}")
        return None

def build_news_html(articles):
    if not articles:
        return "<p style='color:#888;text-align:center;padding:40px'>No news right now. Check back soon.</p>"
    
    html = ""
    for a in articles:
        # Format paragraphs
        paragraphs = a["body"].split("\n\n")
        body_html = "".join(
            f'<p style="font-size:0.88rem;color:#b0c4d8;line-height:1.75;margin:0 0 12px 0;">{p.strip()}</p>'
            for p in paragraphs if p.strip()
        )
        html += f"""
        <article style="background:linear-gradient(135deg,rgba(255,255,255,0.04),rgba(255,255,255,0.02));border:1px solid rgba(240,180,41,0.15);border-radius:16px;padding:24px;margin-bottom:20px;position:relative;overflow:hidden;">
          <div style="position:absolute;top:0;left:0;width:4px;height:100%;background:linear-gradient(180deg,#f0b429,#c8920e);border-radius:4px 0 0 4px;"></div>
          <div style="margin-left:12px;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap;">
              <span style="font-size:0.65rem;font-weight:800;letter-spacing:2px;text-transform:uppercase;background:rgba(240,180,41,0.12);border:1px solid rgba(240,180,41,0.25);color:#f0b429;padding:4px 10px;border-radius:20px;">
                {a['emoji']} {a['category']}
              </span>
              <span style="font-size:0.65rem;color:#556677;letter-spacing:1px;">
                🤖 AI Generated · {datetime.now().strftime("%B %d, %Y")}
              </span>
            </div>
            <h3 style="font-size:1.1rem;font-weight:800;color:#ffffff;margin:0 0 14px 0;line-height:1.4;">
              {a['headline']}
            </h3>
            {body_html}
            <div style="margin-top:14px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.06);font-size:0.7rem;color:#445566;letter-spacing:1px;">
              ✍️ Original article by FWC26 Live AI · Not affiliated with FIFA
            </div>
          </div>
        </article>"""
    return html

def update_html(articles_data):
    html_file = None
    for fname in os.listdir("."):
        if fname.endswith(".html"):
            html_file = fname
            print(f"Found: {fname}")
            break

    if not html_file:
        print("No HTML file found!")
        return

    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()

    timestamp = datetime.now().strftime("%B %d, %Y at %H:%M UTC")
    news_html = build_news_html(articles_data)

    new_section = f"""<!-- AUTO-NEWS-START -->
    <section style="max-width:900px;margin:60px auto;padding:0 20px;">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:28px;padding-bottom:16px;border-bottom:1px solid rgba(240,180,41,0.2);">
        <div>
          <div style="font-size:0.65rem;letter-spacing:3px;text-transform:uppercase;color:#f0b429;font-weight:800;margin-bottom:6px;">
            🤖 AI POWERED
          </div>
          <h2 style="font-family:'Bebas Neue',sans-serif;font-size:2.2rem;color:#ffffff;letter-spacing:3px;margin:0;">
            LATEST WORLD CUP NEWS
          </h2>
        </div>
        <span style="font-size:0.68rem;color:#445566;letter-spacing:1px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);padding:6px 12px;border-radius:8px;">
          🔄 {timestamp}
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

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Done! Published {len(articles_data)} AI articles")

if __name__ == "__main__":
    print("🔍 Fetching topics...")
    topics = fetch_topics()
    print(f"📰 Found {len(topics)} topics — writing AI articles...")
    
    articles = []
    for i, topic in enumerate(topics[:5]):
        print(f"✍️ Writing article {i+1}/{min(len(topics),5)}...")
        article = write_article(topic)
        if article:
            articles.append(article)
    
    print(f"✅ Written {len(articles)} original articles")
    update_html(articles)
