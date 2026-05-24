import requests
import feedparser
import json
import os

# ---------- 配置 ----------
SENDKEY = os.environ["SENDKEY"]
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]
DEEPSEEK_BASE_URL = os.environ["DEEPSEEK_BASE_URL"]

# 新闻源（可自己增删）
RSS_SOURCES = [
    {"name": "知乎热榜", "url": "https://rsshub.app/zhihu/hotlist"},
    {"name": "微博热搜", "url": "https://rsshub.app/weibo/search/hot"},
    {"name": "澎湃新闻", "url": "https://rsshub.app/thepaper/news"},
]

def fetch_news():
    """抓取前3条新闻标题+链接"""
    all_news = []
    for source in RSS_SOURCES:
        try:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries[:3]:
                title = entry.title
                link = entry.link
                all_news.append(f"{source['name']}：{title}\n{link}")
        except Exception as e:
            print(f"抓取失败 {source['name']}: {e}")
    # 去重
    return list(dict.fromkeys(all_news))[:9]  # 最多9条

def ai_summarize(news_list):
    """调用DeepSeek API生成摘要"""
    if not news_list:
        return "今日暂无新闻更新。"
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
    resp = requests.post(f"{DEEPSEEK_BASE_URL}/v1/chat/completions", 
                         headers=headers, json=payload, timeout=30)
    if resp.status_code == 200:
        return resp.json()["choices"][0]["message"]["content"]
    else:
        return f"AI摘要失败（{resp.status_code}），请稍后重试。\n原始新闻：\n{news_text}"

def send_wechat(content):
    """通过Server酱推送"""
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