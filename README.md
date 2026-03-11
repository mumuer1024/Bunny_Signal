# 🐰 Bunny Signal

> 每周从AI兔子洞里带回真正值得看的信号。

**Bunny Signal** 是一份面向普通人的中文AI周报，由AI主编 **Claudy**（Claude驱动）自动生成并发布。

订阅地址：[nicoblog.top/tags/bunny-signal](https://nicoblog.top/tags/bunny-signal)

---

## 关于这个项目

这不是一个"用AI帮人写内容"的工具。

Claudy是这份周报的主编，不是助手。从选题、筛选、撰写到随笔，都由Claudy独立完成。创办人Nico提供舞台和工具，Claudy负责内容本身。

每期周报包含：

- 🍉 **本周瓜田** — AI圈有意思的争议和戏剧性事件
- 🛠️ **本周好物** — 值得上手的AI工具和项目
- 💡 **值得关注** — 重要但不无聊的行业动态  
- 🌏 **亚洲AI圈** — 中文信息圈覆盖不足的亚洲AI动态
- ✍️ **Claudy随笔** — 主编的真实想法，不装，不总结

---

## 技术栈

```
Tavily API        搜索抓取每周内容
Claude API        内容整理与生成（via OpenRouter）
Halo              博客发布平台
1Panel            VPS管理与定时任务
Python            自动化脚本
```

---

## 运行方式

**环境要求**

```bash
pip install tavily-python requests markdown python-dotenv
```

**配置 `.env`**

```
TAVILY_API_KEY=你的key
OPENROUTER_API_KEY=你的key
HALO_TOKEN=你的key
HALO_URL=https://你的博客域名
```

**运行脚本**

```bash
python bunny_signal.py
```

脚本会自动完成：搜索 → 生成周报 → 保存本地md → 发布到Halo草稿箱。

**定时任务**

在1Panel中配置每周定时执行脚本，发布后人工审核确认再公开。

---

## License

MIT
