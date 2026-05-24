import requests
import feedparser
import os

# ---------- 配置 ----------
SENDKEY = os.environ["SENDKEY"]
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]
DEEPSEEK_BASE_URL = os.environ["DEEPSEEK_BASE_URL"]

# 国际可访问的 RSS 源（在美国服务器上测试可用）
RSS_SOURCES = [
    {"name": "BBC中文网", "url": "http://feeds.bbci.co.uk/zhongwen/simp/rss.xml"},
    {"name": "路透社中文", "url": "http://cn.reuters.com/rssFeed/topNews"},
    {"name": "德国之声中文", "url": "https://rss.dw.com/rdf/rss-zh-chs"},
    {"name": "纽约时报中文", "url": "https://cn.nytimes.com/rss/"},
]

def fetch_news():
    all_news = []
    for source in RSS_SOURCES:
        try:
            feed = feedparser.parse(source["url"])
            if feed.entries:
                for entry in feed.entries[:2]:  # 每个源取前2条
                    title = entry.title
                    link = entry.link
                    all_news.append(f"{source['name']}：{title}\n{link}")
            else:
                print(f"无条目: {source['name']}")
        except Exception as e:
            print(f"抓取失败 {source['name']}: {e}")
    # 去重，最多取前8条
    unique = list(dict.fromkeys(all_news))
    return unique[:8]

def ai_summarize(news_list):
    if not news_list:
        # 如果没有新闻，返回一个默认消息
        return "今日没有抓到新闻，可能是源站临时不可用。稍后会自动重试。"
    news_text = "\n\n".join(news_list)
    prompt = f"""请用100字左右总结以下新闻的要点，语言简洁、适合早晨快速阅读，最后加一句鼓励的话。

新闻列表：
{news_text}
"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }
    try:
        resp = requests.post(f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
                             headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        else:
            return f"AI摘要失败（{resp.status_code}），原始新闻：\n{news_text}"
    except Exception as e:
        return f"AI摘要异常：{str(e)}\n原始新闻：\n{news_text}"

def send_wechat(content):
    url = f"https://sctapi.ftqq.com/{SENDKEY}.send"
    data = {
        "title": "🤖 你的AI早报",
        "desp": content
    }
    requests.post(url, data=data)

if __name__ == "__main__":
    print("抓取新闻中...")
    raw_news = fetch_news()
    print(f"抓取到 {len(raw_news)} 条新闻")
    print("AI生成摘要中...")
    summary = ai_summarize(raw_news)
    print("推送到微信...")
    send_wechat(summary)
    print("完成！")
