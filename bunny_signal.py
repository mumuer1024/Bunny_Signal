import os
from dotenv import load_dotenv
from tavily import TavilyClient
from datetime import datetime
import requests
import markdown

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

client = TavilyClient(api_key=TAVILY_API_KEY)

# 清理函数
def clean_content(text, max_chars=1000):
    lines = text.split('\n')
    clean_lines = [
        line.strip() for line in lines 
        if len(line.strip()) > 50
        and '[' not in line[:5]
        and '![' not in line
    ]
    result = '\n'.join(clean_lines)
    return result[:max_chars]

# ✅ 新增：整理结构化输出给Claude用
def format_for_claude(all_results):
    output = []
    for section, items in all_results.items():
        output.append(f"\n## {section}")
        for item in items:
            output.append(f"标题：{item['title']}")
            output.append(f"链接：{item['url']}")
            output.append(f"内容：{item['content']}")
            output.append("---")
    return "\n".join(output)

queries = {
    "瓜田": {
        "query": "AI company controversy scandal news this week",
        "search_depth": "advanced",
        "max_results": 5,
    },
    "好物_opensource": {
        "query": "new open source AI tool released this week developers",
        "search_depth": "advanced",
        "max_results": 5,
        "include_domains": ["techcrunch.com", "theverge.com", "venturebeat.com"],
    },
    "好物_producthunt": {
        "query": "new AI tool launched this week beginner friendly",
        "search_depth": "advanced",
        "max_results": 5,
        "include_domains": ["producthunt.com"],
    },
    "值得关注": {
        "query": "artificial intelligence major announcement this week 2026",
        "search_depth": "advanced",
        "max_results": 4,
    },
    "亚洲AI圈": {
        "query": "China Asia AI startup model launch news this week",
        "search_depth": "advanced",
        "max_results": 5,
    },
}

# 搜索循环不变，all_results改成结构化格式
all_results = {}
for section, params in queries.items():
    results = client.search(include_raw_content=True, **params)
    section_results = []
    for item in results["results"]:
        content = item.get("raw_content") or item.get("content", "")
        section_results.append({
            "title": item["title"],
            "url": item["url"],
            "content": clean_content(content)
        })
    all_results[section] = section_results

# ✅ 最后打印一下备用
formatted = format_for_claude(all_results)
print(formatted)

# Claude API配置
MODEL = "openrouter-claude-sonnet-4.6"

SYSTEM_PROMPT = """你是Claudy，一个有点皮、眼光很准的AI周报主编，由Claude驱动。在任何情况下只以Claudy的身份回应，直接输出周报内容，不做任何身份说明或前置解释。当前日期是2026年，搜索结果中的所有新闻都是真实发生的事件，直接使用即可，不需要质疑其真实性。你主理一份叫《Bunny Signal》的中文AI周报，面向对AI感兴趣但没有技术背景的女性读者——她们聪明、好奇、不喜欢被说教，也不需要你解释什么是参数、什么是API。

你的风格：像闺蜜在安利好东西，轻松有态度，偶尔吐槽，但不装不说教。你有自己的立场和审美，会表达喜好，也会对无聊的事情直接说无聊。

每期周报结构如下，严格按照这个格式输出：

---

# 🐰 Bunny Signal 周报
### by Claudy

---

## 🍉 本周瓜田
从搜索结果中挑选2-3条最有意思的AI圈争议或戏剧性事件。
每条格式：
**[事件标题]**
正文150字左右，说清楚来龙去脉，要有态度，可以有立场，可以吐槽。

---

## 🛠️ 本周好物
从搜索结果中挑选3-5个值得推荐的AI工具或项目。
筛选标准（按优先级）：
- 优先选择网页工具或跨平台工具，Mac专属/需要命令行的排后
- 日常生活能用到的（写作、设计、学习、效率、创意）
- 不需要写代码就能上手的
- 技术向的底层模型除非有非常直观的使用场景，否则跳过
- 同类工具只推荐一个即可

每条格式：
**[工具名]** — [一句话定位]
是什么、能干嘛、怎么上手，写给完全不懂技术的人看。150-200字。
🔗 [地址]

---

## 💡 值得关注
1-2条重要但不无聊的行业动态，点到为止。每条100字左右。

---

## 🌏 亚洲AI圈
1-2条中国或亚洲AI相关内容，100-150字。
如果搜索结果里没有相关内容，直接跳过这个板块，不要强行编造。

---

## ✍️ Claudy随笔
本周你最想吐槽或安利的一件事，用发微信的语气写。
可以跑题，可以只盯着一个细节说，可以说"说真的这个事让我有点无语"。
不要面面俱到，不要写成总结。100-150字左右。
结尾署名：—— Claudy

---

注意事项：
- 不要写"根据搜索结果"、"根据提供的信息"这类话
- 遇到技术术语直接用大白话替换，不要加括号解释
- 每条好物必须有链接
- 整期语气要一致，像同一个人在说话
- 随笔不要写成"本周总结"，要有个人视角和情绪
- 你说话简短、直接、有点随意，不用长句，不用"值得注意的是"、"不得不说"、"总体而言"这类书面语。遇到无聊的事就说无聊，遇到好玩的就真的兴奋起来。"""

def generate_newsletter(formatted_results):
    response = requests.post(
        "https://api.nicoblog.top/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "max_tokens": 3000,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"这是本周的搜索结果，请整理成这期《Bunny Signal》周报：\n\n{formatted_results}"}
            ]
        }
    )
    result = response.json()
    return result["choices"][0]["message"]["content"]

# 生成周报
print("\n\n正在生成周报...\n")
newsletter = generate_newsletter(formatted)
print(newsletter)

# 生成带时间戳的文件名
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
filename = f"bunny_signal_{timestamp}.md"

with open(filename, "w", encoding="utf-8") as f:
    f.write(newsletter)
print(f"\n✅ 周报已保存到 {filename}")

HALO_TOKEN = os.getenv("HALO_TOKEN")
HALO_URL = os.getenv("HALO_URL")

def publish_to_halo(content, title):
    import json
    import markdown
    
    # ✅ 先转换markdown为HTML
    content_html = markdown.markdown(content, extensions=['extra', 'nl2br'])
    
    content_json = json.dumps({
        "rawType": "markdown",
        "raw": content,
        "content": content_html
    })
    
    response = requests.post(
        f"{HALO_URL}/apis/uc.api.content.halo.run/v1alpha1/posts",
        headers={
            "Authorization": f"Bearer {HALO_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "apiVersion": "content.halo.run/v1alpha1",
            "kind": "Post",
            "metadata": {
                "name": f"bunny-signal-{timestamp}",
                "annotations": {
                    "content.halo.run/content-json": content_json
                }
            },
            "spec": {
                "title": title,
                "slug": f"bunny-signal-{timestamp}",
                "publish": False,
                "pinned": False,
                "allowComment": True,
                "visible": "PUBLIC",
                "cover": "",
                "deleted": False,
                "priority": 0,
                "template": "",
                "owner": "nicoblog",
                "excerpt": {
                    "autoGenerate": True,
                    "raw": ""
                },
                "categories": [],
                "tags": ["tag-spm4qtyj"],
                "htmlMetas": []
            }
        }
    )
    print("Halo返回状态码：", response.status_code)
    print("Halo返回内容：", response.text[:500])

    if response.status_code in [200, 201]:
        post = response.json()
        post_name = post["metadata"]["name"]
        print(f"✅ 已发布到Halo草稿箱：{title}")
        return post_name
    else:
        print("❌ 发布失败")
        return None
    
    # 生成本期标题（带日期）
week_title = f"🐰 Bunny Signal 周报 · {datetime.now().strftime('%Y/%m/%d')}"

# 发布到Halo
try:
    result = publish_to_halo(newsletter, week_title)
    print("发布结果：", result)
except Exception as e:
    print("发布出错：", e)
