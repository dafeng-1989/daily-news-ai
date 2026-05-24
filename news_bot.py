import requests
import os
import json

SENDKEY = os.environ["SENDKEY"]
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]
DEEPSEEK_BASE_URL = os.environ["DEEPSEEK_BASE_URL"]

def fetch_news():
    """从国内公开 API 获取热榜"""
    news_list = []
    
    # 1. 微博热搜（不需要 cookie）
    try:
        url = "https://weibo.com/ajax/side/hotSearch"
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        data = resp.json()
        if "data" in data and "realtime" in data["data"]:
            for item in data["data"]["realtime"][:5]:
                title = item.get("word", "")
                news_list.append(f"微博热搜：{title}\nhttps://s.weibo.com/weibo?q={title}")
    except Exception as e:
        print(f"微博失败: {e}")
    
    # 2. 知乎热榜（公开接口）
    try:
        url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=5"
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        data = resp.json()
        for item in data.get("data", []):
            title = item.get("target", {}).get("title", "")
            if title:
                news_list.append(f"知乎热榜：{title}\nhttps://www.zhihu.com/question/{item.get('target',{}).get('id')}")
    except Exception as e:
        print(f"知乎失败: {e}")
    
    # 3. 百度热搜（备用）
    try:
        url = "https://top.baidu.com/board?tab=realtime"
        # 百度需要解析HTML，这里简化，改用另一个API
        resp = requests.get("https://api.qingyunke.com/hot?type=baidu", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("data", [])[:3]:
                title = item.get("title", "")
                news_list.append(f"百度热搜：{title}\nhttps://www.baidu.com/s?wd={title}")
    except Exception as e:
        print(f"百度失败: {e}")
    
    # 去重
    return list(dict.fromkeys(news_list))[:8]

def ai_summarize(news_list):
    if not news_list:
        return "今日没有抓到新闻，可能是接口临时失效。"
    news_text = "\n\n".join(news_list)
    prompt = f"请用100字左右总结以下新闻要点，简洁适合早读，最后一句鼓励：\n{news_text}"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "stream": False}
    try:
        resp = requests.post(f"{DEEPSEEK_BASE_URL}/v1/chat/completions", headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        else:
            return f"AI失败({resp.status_code})，原始新闻：\n{news_text}"
    except Exception as e:
        return f"AI异常：{e}\n{news_text}"

def send_wechat(content):
    url = f"https://sctapi.ftqq.com/{SENDKEY}.send"
    requests.post(url, data={"title": "🤖 你的AI早报", "desp": content})

if __name__ == "__main__":
    print("抓取国内热榜...")
    news = fetch_news()
    print(f"抓到 {len(news)} 条")
    summary = ai_summarize(news)
    send_wechat(summary)
    print("完成")
