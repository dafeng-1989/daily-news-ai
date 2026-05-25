import requests
import os
import json

SENDKEY = os.environ["SENDKEY"]
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]
DEEPSEEK_BASE_URL = os.environ["DEEPSEEK_BASE_URL"]

def fetch_news():
    news_list = []
    
    # 测试1：微博热搜
    print("尝试微博热搜...")
    try:
        url = "https://weibo.com/ajax/side/hotSearch"
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        print(f"微博状态码: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            if "data" in data and "realtime" in data["data"]:
                for item in data["data"]["realtime"][:3]:
                    title = item.get("word", "")
                    news_list.append(f"微博热搜：{title}\nhttps://s.weibo.com/weibo?q={title}")
                print(f"微博抓取到 {len(data['data']['realtime'][:3])} 条")
            else:
                print("微博返回数据格式不对")
        else:
            print("微博非200")
    except Exception as e:
        print(f"微博异常: {type(e).__name__} - {str(e)}")
    
    # 测试2：知乎热榜
    print("尝试知乎热榜...")
    try:
        url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=3"
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        print(f"知乎状态码: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("data", []):
                title = item.get("target", {}).get("title", "")
                if title:
                    news_list.append(f"知乎热榜：{title}\nhttps://www.zhihu.com/question/{item.get('target',{}).get('id')}")
            print(f"知乎抓取到 {len(data.get('data', []))} 条")
        else:
            print("知乎非200")
    except Exception as e:
        print(f"知乎异常: {type(e).__name__} - {str(e)}")
    
    # 测试3：新浪新闻简单接口
    print("尝试新浪新闻...")
    try:
        url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&k=&num=3&page=1"
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        print(f"新浪状态码: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("result", {}).get("data", []):
                title = item.get("title", "")
                link = item.get("url", "")
                if title:
                    news_list.append(f"新浪新闻：{title}\n{link}")
            print(f"新浪抓取到 {len(data.get('result',{}).get('data',[]))} 条")
        else:
            print("新浪非200")
    except Exception as e:
        print(f"新浪异常: {type(e).__name__} - {str(e)}")
    
    # 去重
    unique = list(dict.fromkeys(news_list))
    print(f"总共抓取到 {len(news_list)} 条，去重后 {len(unique)} 条")
    return unique[:8]

def ai_summarize(news_list):
    if not news_list:
        return "今日没有抓到新闻。可能是网络问题。请稍后重试。"
    news_text = "\n\n".join(news_list)
    prompt = f"请用100字左右总结以下新闻要点：\n{news_text}"
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
    requests.post(url, data={"title": "🤖 AI早报", "desp": content})

if __name__ == "__main__":
    print("=== 开始抓取 ===")
    news = fetch_news()
    print(f"最终新闻条数: {len(news)}")
    summary = ai_summarize(news)
    send_wechat(summary)
    print("完成")
