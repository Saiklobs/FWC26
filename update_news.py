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
    "https://www.espn.com/espn/rss/soccer/news",
    "https://www.goal.com/en-in/feeds/news",
    
    
]

KEYWORDS = [
    "world cup", "fifa", "2026", "worldcup", "squad",
    "match", "goal", "group", "team", "player",
    "stadium", "mexico", "canada", "usa", "messi",
    "ronaldo", "tactics", "lineup", "qualifier", "england",
    "brazil", "france", "argentina", "germany", "spain",
    "tunisia", "joueurs", "world cup 2026", "live score",
    "match schedule", "group standings", "starting xi",
    "who plays next", "كأس العالم 2026", "جدول المباريات", "نتائج مباشرة"
    , "مجموعات كأس العالم", "موعد المباراة", "coupe du monde 2026",
    "calendrier des matchs", "résultats en direct",
    "classement des groupes", "prochain match" , 
    "piala dunia 2026", "jadwal pertandingan", 
    "skor langsung", "klasemen grup", 
    "pertandingan berikutnya", "чемпионат мира 2026", "расписание матчей", "результаты матчей", "турнирная таблица", "кто играет дальше" , "ワールドカップ2026", "試合日程", "ライブスコア", "グループ順位", "次の試合" ,
    
]
def fetch_topics():
    topics = []
    for feed_url in FEEDS:
        try:
            r = requests.get(feed_url, timeout=10,
                headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(r.content, "xml")
            items = soup.find_all("item")
            for item in items[:10]:
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
            print(f"Feed error: {e}")
    seen = set()
    unique = []
    for t in topics:
        if t["title"] not in seen:
            seen.add(t["title"])
            unique.append(t)
    print(f"Found {len(unique)} topics")
    return unique[:5]

def write_article(topic):
    if not GROQ_API_KEY:
        print("No GROQ_API_KEY found!")
        return None

    prompt = f"""You are a professional football journalist for FWC26 Live, a FIFA World Cup 2026 news website.

Write a complete original article inspired by this topic:
Topic: {topic['title']}
Context: {topic['desc']}

Rules:
- Write your OWN original headline (not a copy)
- Write 3 paragraphs of original journalism (about 180 words total)
- Focus on FIFA World Cup 2026 angle
- Professional exciting tone
- Never mention BBC, ESPN or any other news source
- This is your own original reporting

Respond ONLY with valid JSON, no extra text, no markdown:
{{"headline": "original headline here", "category": "Match Preview", "body": "paragraph 1 here\\n\\nparagraph 2 here\\n\\nparagraph 3 here", "emoji": "⚽"}}

Category must be one of: Match Preview, Team News, Tactics, Player Spotlight, Tournament Update"""

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
                "max_tokens": 700,
                "temperature": 0.85
            },
            timeout=30
        )
        data = r.json()
        if "choices" not in data:
            print(f"Groq response error: {data}")
            return None
        text = data["choices"][0]["message"]["content"].strip()
        text = re.sub(r'```json|```', '', text).strip()
        # Find JSON object
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            article = json.loads(match.group())
            print(f"✅ Written: {article.get('headline','?')[:50]}")
            return article
        else:
            print(f"No JSON found in: {text[:100]}")
            return None
    except Exception as e:
        print(f"Groq error: {e}")
        return None

def build_news_html(articles):
    if not articles:
        return "<p style='color:#888;text-align:center;padding:40px'>No AI articles generated yet. Check back soon.</p>"

    html = ""
    for a in articles:
        paragraphs = a.get("body", "").split("\n\n")
        body_html = "".join(
            f'<p style="font-size:0.9rem;color:#b0c4d8;line-height:1.8;margin:0 0 14px 0;">{p.strip()}</p>'
            for p in paragraphs if p.strip()
        )
        category = a.get("category", "World Cup News")
        emoji = a.get("emoji", "⚽")
        headline = a.get("headline", "World Cup Update")

        html += f"""
        <article style="background:linear-gradient(135deg,rgba(15,25,50,0.9),rgba(10,18,38,0.95));border:1px solid rgba(240,180,41,0.2);border-left:4px solid #f0b429;border-radius:12px;padding:24px 24px 20px 24px;margin-bottom:20px;">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;flex-wrap:wrap;">
            <span style="font-size:0.65rem;font-weight:800;letter-spacing:2px;text-transform:uppercase;background:rgba(240,180,41,0.1);border:1px solid rgba(240,180,41,0.3);color:#f0b429;padding:5px 12px;border-radius:20px;">
              {emoji} {category}
            </span>
            <span style="font-size:0.65rem;color:#445566;letter-spacing:1px;">
              🤖 FWC26 AI · {datetime.now().strftime("%d %b %Y")}
            </span>
          </div>
          <h3 style="font-size:1.15rem;font-weight:800;color:#ffffff;margin:0 0 16px 0;line-height:1.45;letter-spacing:0.3px;">
            {headline}
          </h3>
          {body_html}
          <div style="margin-top:16px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.05);font-size:0.68rem;color:#334455;letter-spacing:1px;">
            ✍️ Original article by FWC26 Live · Not affiliated with FIFA
          </div>
        </article>"""
    return html

def update_html(articles):
    html_file = None
    for fname in os.listdir("."):
        if fname.endswith(".html"):
            html_file = fname
            print(f"Found HTML file: {fname}")
            break

    if not html_file:
        print("❌ No HTML file found!")
        return

    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()

    timestamp = datetime.now().strftime("%B %d, %Y at %H:%M UTC")
    news_html = build_news_html(articles)

    new_section = f"""<!-- AUTO-NEWS-START -->
<section style="max-width:900px;margin:60px auto;padding:0 20px;">
  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:28px;padding-bottom:18px;border-bottom:2px solid rgba(240,180,41,0.25);">
    <div>
      <div style="font-size:0.62rem;letter-spacing:4px;text-transform:uppercase;color:#f0b429;font-weight:800;margin-bottom:8px;">
        🤖 AI POWERED · ORIGINAL ARTICLES
      </div>
      <h2 style="font-family:'Bebas Neue',sans-serif;font-size:2.4rem;color:#ffffff;letter-spacing:3px;margin:0;line-height:1;">
        LATEST WORLD CUP NEWS
      </h2>
    </div>
    <div style="text-align:right;">
      <div style="font-size:0.62rem;color:#445566;letter-spacing:1px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);padding:8px 14px;border-radius:8px;">
        🔄 {timestamp}
      </div>
    </div>
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
        print("✅ Replaced existing news section")
    else:
        content = content.replace("</body>", new_section + "\n</body>")
        print("✅ Added new news section before </body>")

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"🎉 Done! Published {len(articles)} AI-written articles to {html_file}")

if __name__ == "__main__":
    print("=" * 50)
    print("FWC26 Live — AI News Generator")
    print("=" * 50)
    print(f"GROQ_API_KEY present: {bool(GROQ_API_KEY)}")

    topics = fetch_topics()
    if not topics:
        print("No topics found, exiting")
        exit(0)

    articles = []
    for i, topic in enumerate(topics):
        print(f"\n✍️  Writing article {i+1}/{len(topics)}...")
        article = write_article(topic)
        if article:
            articles.append(article)

    print(f"\n📰 Successfully wrote {len(articles)} articles")
    update_html(articles)
