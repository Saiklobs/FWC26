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
]

KEYWORDS = [
    "world cup","fifa","2026","squad","match",
    "goal","team","player","mexico","canada",
    "usa","england","brazil","france","argentina"
]

def fetch_topics():
    topics = []
    for feed_url in FEEDS:
        try:
            r = requests.get(feed_url, timeout=10,
                headers={"User-Agent":"Mozilla/5.0"})
            soup = BeautifulSoup(r.content, "xml")
            items = soup.find_all("item")
            for item in items[:10]:
                title = item.find("title")
                desc = item.find("description")
                if not title:
                    continue
                title_text = title.text.strip()
                desc_text = desc.text.strip() if desc else ""
                combined = (title_text+" "+desc_text).lower()
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
    return unique[:3]

def write_article(topic):
    if not GROQ_API_KEY:
        print("No GROQ_API_KEY!")
        return None
    prompt = f"""You are a football journalist for FWC26 Live website.
Write an original article inspired by: {topic['title']}
Write 3 short paragraphs, FIFA World Cup 2026 angle.
Never copy from any source. Never mention BBC or ESPN.
Reply ONLY with this JSON, nothing else:
{{"headline":"your headline","category":"Team News","body":"para1\\n\\npara2\\n\\npara3","emoji":"⚽"}}
Category options: Match Preview, Team News, Tactics, Player Spotlight, Tournament Update"""
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "mixtral-8x7b-32768",
                "messages": [{"role":"user","content":prompt}],
                "max_tokens": 600,
                "temperature": 0.8
            },
            timeout=30
        )
        data = r.json()
        if "choices" not in data:
            print(f"Groq error: {data}")
            return None
        text = data["choices"][0]["message"]["content"].strip()
        text = re.sub(r'```json|```','',text).strip()
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            article = json.loads(match.group())
            print(f"OK: {article.get('headline','?')[:60]}")
            return article
        print(f"No JSON in: {text[:100]}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def build_news_html(articles):
    if not articles:
        return "<p style='color:#888;text-align:center;padding:40px'>Updating soon...</p>"
    html = ""
    for a in articles:
        paragraphs = a.get("body","").split("\n\n")
        body_html = "".join(
            f'<p style="font-size:0.9rem;color:#b0c4d8;line-height:1.8;margin:0 0 14px 0;">{p.strip()}</p>'
            for p in paragraphs if p.strip()
        )
        html += f"""
<article style="background:linear-gradient(135deg,rgba(15,25,50,0.9),rgba(10,18,38,0.95));border:1px solid rgba(240,180,41,0.2);border-left:4px solid #f0b429;border-radius:12px;padding:24px;margin-bottom:20px;">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;flex-wrap:wrap;">
    <span style="font-size:0.65rem;font-weight:800;letter-spacing:2px;text-transform:uppercase;background:rgba(240,180,41,0.1);border:1px solid rgba(240,180,41,0.3);color:#f0b429;padding:5px 12px;border-radius:20px;">
      {a.get('emoji','🏆')} {a.get('category','World Cup')}
    </span>
    <span style="font-size:0.65rem;color:#445566;">
      🏆 FWC26 · {datetime.now().strftime("%d %b %Y")}
    </span>
  </div>
  <h3 style="font-size:1.15rem;font-weight:800;color:#ffffff;margin:0 0 16px 0;line-height:1.45;">
    {a.get('headline','World Cup Update')}
  </h3>
  {body_html}
  <div style="margin-top:16px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.05);font-size:0.68rem;color:#334455;">
    ✍️ Original article by FWC26 Live · Not affiliated with FIFA
  </div>
</article>"""
    return html

def update_html(articles):
    html_file = None
    for fname in os.listdir("."):
        if fname.endswith(".html"):
            html_file = fname
            break
    if not html_file:
        print("No HTML file!")
        return
    with open(html_file,"r",encoding="utf-8") as f:
        content = f.read()
    timestamp = datetime.now().strftime("%B %d, %Y at %H:%M UTC")
    news_html = build_news_html(articles)
    new_section = f"""<!-- AUTO-NEWS-START -->
<section style="max-width:900px;margin:60px auto;padding:0 20px;">
  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:28px;padding-bottom:18px;border-bottom:2px solid rgba(240,180,41,0.25);">
    <div>
      <div style="font-size:0.62rem;letter-spacing:4px;text-transform:uppercase;color:#f0b429;font-weight:800;margin-bottom:8px;">🤖 AI POWERED · ORIGINAL ARTICLES</div>
      <h2 style="font-family:'Bebas Neue',sans-serif;font-size:2.4rem;color:#ffffff;letter-spacing:3px;margin:0;">LATEST WORLD CUP NEWS</h2>
    </div>
    <div style="font-size:0.62rem;color:#445566;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);padding:8px 14px;border-radius:8px;">🔄 {timestamp}</div>
  </div>
  {news_html}
</section>
<!-- AUTO-NEWS-END -->"""
    if "<!-- AUTO-NEWS-START -->" in content:
        content = re.sub(
            r'<!-- AUTO-NEWS-START -->.*?<!-- AUTO-NEWS-END -->',
            new_section, content, flags=re.DOTALL)
        print("Replaced section")
    else:
        content = content.replace("</body>", new_section+"\n</body>")
        print("Added section")
    with open(html_file,"w",encoding="utf-8") as f:
        f.write(content)
    print(f"Done! {len(articles)} articles published")

if __name__ == "__main__":
    print("="*40)
    print(f"GROQ key: {bool(GROQ_API_KEY)}")
    topics = fetch_topics()
    articles = []
    for i,topic in enumerate(topics):
        print(f"Writing {i+1}/{len(topics)}...")
        a = write_article(topic)
        if a:
            articles.append(a)
    print(f"Total: {len(articles)} articles")
    update_html(articles)
