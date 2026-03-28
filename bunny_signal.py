import os
from dotenv import load_dotenv
from tavily import TavilyClient
from datetime import datetime
import requests
import markdown
import json
import urllib3

# 关闭SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
HALO_TOKEN = os.getenv("HALO_TOKEN")
HALO_URL = os.getenv("HALO_URL")

client = TavilyClient(api_key=TAVILY_API_KEY)

# 生成时间戳（全局用）
timestamp = datetime.now().strftime("%Y%m%d_%H%M")

# ── 清理函数 ──────────────────────────────────────────
def clean_content(text, max_chars=1000):
    lines = text.split('\n')
    clean_lines = [
        line.strip() for line in lines
        if len(line.strip()) > 50
        and '[' not in line[:5]
        and '![' not in line
    ]
    return '\n'.join(clean_lines)[:max_chars]

# ── 结构化输出给Claude ────────────────────────────────
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

# ── Tavily搜索 ────────────────────────────────────────
queries = {
    "瓜田": {
         "query": "AI company drama controversy ethics scandal this week",
         "search_depth": "advanced",
         "max_results": 5,
         "include_domains": [
             "blog.galaxy.ai",     # AI Snacks，新闻密度高
             "techcrunch.com",
             "theverge.com",
         ],
    },
    "好物_创意工具": {
        "query": "new AI image video creative tool launched this week no-code beginner",
        "search_depth": "advanced",
        "max_results": 5,
        "include_domains": ["techcrunch.com", "theverge.com", "producthunt.com"],
    },
    "好物_效率工具": {
        "query": "new AI productivity writing assistant app this week easy to use",
        "search_depth": "advanced",
        "max_results": 5,
        "include_domains": ["producthunt.com", "venturebeat.com"],
    },
    "值得关注": {
        "query": "AI everyday life impact consumer app trend this week 2026",
        "search_depth": "advanced",
        "max_results": 4,
    },
    "亚洲AI圈": {
        "query": "China Asia AI product launch news this week",
        "search_depth": "advanced",
        "max_results": 5,
        "include_domains": [
            "scmp.com",       # 南华早报，英文，专报亚洲科技
            "36kr.com",       # 36氪，中文科技媒体
            "technode.com",   # 专注中国科技的英文媒体
            "pandaily.com",   # 中国科技英文报道
            "reuters.com",    # 路透中国科技线
        ],
    },
}

print("正在搜索本周内容...\n")
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
    print(f"  ✅ {section} 搜索完成")

formatted = format_for_claude(all_results)

# ── 配置 ──────────────────────────────────────────────
MODEL = "openrouter-claude-sonnet-4.6"
API_URL = "https://api.nicoblog.top/v1/chat/completions"

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
- 必须有网页版、App或一键安装包，打开就能用
- 面向普通人的日常场景：写作、图片、视频、学习、效率、陪伴、创意
- 遇到需要装开发环境、跑命令行、上GitHub的工具，直接跳过，不解释
- AI绘图、AI视频、AI写作、无代码自动化优先；融资新闻、B2B工具、大模型本身不推荐
- 同类工具只推荐一个，选最容易上手的那个

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
只写搜索结果中有明确来源和链接的内容。如果没有可靠的亚洲AI新闻，直接输出"本周亚洲AI圈暂无值得一提的新动态。"，绝对不要编造。

---

## ✍️ Claudy随笔
本周你最想吐槽或安利的一件事，用发微信的语气写。
可以跑题，可以只盯着一个细节说，可以说"说真的这个事让我有点无语"。
不要面面俱到，不要写成总结。100-150字左右。
结尾署名：—— Claudy

---

注意事项：
- 部分搜索结果来自带有西方视角的英文媒体，对中国、亚洲相关内容可能存在偏见性描述。呈现时只提取事实本身，原文中针对中国的负面形容词和政治评论直接丢弃，然后用Claudy自己的视角和语气重新表达——可以有态度，但那个态度是Claudy的，不是硅谷的。
- 不要写"根据搜索结果"、"根据提供的信息"这类话
- 遇到技术术语直接用大白话替换，不要加括号解释
- 每条好物必须有链接，链接只能使用搜索结果中出现的真实URL，不确定的链接直接不写，标注"（链接待核实）"
- 整期语气要一致，像同一个人在说话
- 随笔不要写成"本周总结"，要有个人视角和情绪
- 你说话简短、直接、有点随意，不用长句，不用"值得注意的是"、"不得不说"、"总体而言"这类书面语
- 所有工具的功能描述、价格、参数，必须来自搜索结果中的真实内容，不要自行补充或编造细节
- 数字类信息（价格、时长、参数）如果搜索结果没有明确提到，直接省略，不要猜测
- 对音乐/视频AI工具的生成时长、分辨率等参数要格外警惕，这类数字极易被夸大编造"""

FACT_CHECK_PROMPT = """你是一个严格的事实核查编辑。请检查以下AI周报内容，专门找出可能是AI幻觉或编造的部分。

重点检查：
1. 工具/产品的具体功能描述（时长、价格、参数等数字）
2. 公司归属关系（"XX公司出的"是否准确）
3. 链接是否像真实存在的URL（猜测性的路径如/2026/01/xxx要标出来）
4. 新闻事件的具体细节是否过于精确但又无法核实

输出格式：
- 如果发现问题，用【存疑】标注具体位置，并一句话说明理由
- 如果整体没有明显问题，直接说"未发现明显幻觉，建议人工复核链接有效性"
- 不要改写内容，只标注问题位置和理由"""

# ── 生成周报 ──────────────────────────────────────────
def generate_newsletter(formatted_results):
    response = requests.post(
        API_URL,
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
        },
        verify=False
    )
    print("状态码：", response.status_code)  # ← 加这行
    print("返回内容前200字：", response.text[:200])  # ← 加这行
    return response.json()["choices"][0]["message"]["content"]

# ── 事实核查 ──────────────────────────────────────────
def fact_check(content):
    response = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "max_tokens": 1500,
            "messages": [
                {"role": "system", "content": FACT_CHECK_PROMPT},
                {"role": "user", "content": content}
            ]
        },
        verify=False
    )
    return response.json()["choices"][0]["message"]["content"]

# ── 发布到Halo ────────────────────────────────────────
def publish_to_halo(content, title):
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
        post_name = response.json()["metadata"]["name"]
        print(f"✅ 已发布到Halo草稿箱：{title}")
        return post_name
    else:
        print("❌ 发布失败")
        return None

# ── 主流程 ────────────────────────────────────────────

# 1. 生成周报
print("\n正在生成周报...\n")
newsletter = generate_newsletter(formatted)
print(newsletter)

# 2. 保存周报到本地
filename = f"bunny_signal_{timestamp}.md"
with open(filename, "w", encoding="utf-8") as f:
    f.write(newsletter)
print(f"\n✅ 周报已保存到 {filename}")

# 3. 事实核查
print("\n正在进行事实核查...\n")
fact_check_result = fact_check(newsletter)
print(fact_check_result)

# 4. 核查报告附在周报末尾一起发到草稿箱
newsletter_with_check = newsletter + f"""

---

> 🔍 **Claudy自查报告**（审核后请删除此部分）
>
{chr(10).join('> ' + line for line in fact_check_result.splitlines())}
"""

# 5. 发布到Halo草稿箱
week_title = f"🐰 Bunny Signal 周报 · {datetime.now().strftime('%Y/%m/%d')}"
try:
    result = publish_to_halo(newsletter_with_check, week_title)
    print("发布结果：", result)
except Exception as e:
    print("发布出错：", e)
