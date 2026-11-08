# github-daily-picks

> 每天从 GitHub 挑三个**真正适合某个具体的人**的开源项目，用 API 核实真实数据，生成中文详情卡片。

大多数「每日 GitHub 推荐」的问题是：它推的是全世界的热门，不是你的工具。这个 skill 反过来——它只读一个人的画像（硬件、职业、预算、审美、明确讨厌的东西），据此筛选，并在每张卡上写清「为什么给你」「你的机器跑不跑得动」「有什么坑」。

## 它长什么样

产出是一张 HTML 卡片（浅色纸感背景、白卡、序号水印、砖红强调色），三个项目各占一卡，包含：

- 真实 Stars / 语言 / 协议 / 最近提交日期（全部来自 GitHub API 实时查询，不靠记忆）
- 定位标签、一段人话讲清它干什么
- **为什么给你**——结合画像里的具体处境写，这是整张卡的核心
- 上手成本、在你机器上的可行性（显存、磁盘余量、系统版本、A 卡兼容性）
- 2–3 条实话实说的坑
- 一句结论：值得装 / 观望 / 别碰

样式模板见 [`assets/card-template.html`](github-daily-picks/assets/card-template.html)，直接浏览器打开可预览。

## 第一次使用：它会先"读"你

不需要填问卷。第一次运行时，agent 会**遍历你和它的历史对话**，从真实聊天里提取六块信息——职业与收入、硬件环境、工具栈、审美偏好、明确回避、忌口——生成一份 `profile.md`，然后发给你确认：

```
我翻了下我们之前的聊天，把你读成这样（有错直接改）：
· 你是谁：…
· 你的机器：…
· 你在意 / 不在意：…
· 你明确不想要的：…
这几条是从你原话来的，稳定；下面两条是我推的，可能不准：…
```

设计上的三个讲究：

- **行为优先于表态**。你嘴上说"不在乎价格"，但每次都问最便宜的，画像就按行为写
- **推断项必须标注**。来自你原话的标「用户原话」，从行为反推的标「推断」，不让推断冒充事实
- **不写敏感信息**。不存身份证、住址、真实姓名、精确薪资、账号密码；收入只写量级

如果这个 agent 读不到历史对话（部分环境没有会话检索能力），会自动退回问卷模式，发 `references/profile-template.md` 让你填。你说「别分析我」，它也会立刻停手。

## 安装

**方式一：skills CLI**

```bash
npx skills@latest add <你的GitHub用户名>/github-daily-picks
```

**方式二：手动**

```bash
git clone https://github.com/<你的GitHub用户名>/github-daily-picks.git
cp -r github-daily-picks/github-daily-picks ~/.workbuddy/skills/
```

## 配置画像（关键一步）

没有画像，这个 skill 就退化成热门榜单。复制模板填一份：

```bash
cp ~/.workbuddy/skills/github-daily-picks/references/profile-template.md \
   ~/.workbuddy/skills/github-daily-picks/profile.md
```

必填的六块：身份与收入、硬件环境（**A 卡还是 N 卡要写清**）、工具栈、偏好与审美、明确回避、忌口备注。

写「明确回避」时越具体越好，比如「不接受必须买会员才能用的」比「喜欢免费软件」有用得多。

## 用法

直接说：

> 用 github-daily-picks 给我推今天三个项目

或者把它挂成定时任务，每天固定时间跑一次。定时任务的 prompt 建议这么写：

```
每天挑 3 个对「我」有用的开源项目，用 github-daily-picks 技能生成卡片。
先读 profile.md，跳过 <工作目录>/github-daily/已推荐记录.md 里推过的仓库。
找不到 3 个真正合格的就只推 1-2 个，并在摘要里直说，不要凑数。
```

## 依赖

- Python 3.8+（仅标准库，无第三方包）
- 能访问 `api.github.com`
- 可选：设置 `GITHUB_TOKEN` 环境变量，未登录时搜索接口限流 10 次/分钟、核心接口 60 次/小时，登录后升到 5000 次/小时

手动跑脚本：

```bash
# 按关键词搜候选，自动过滤 fork / 归档 / 超期未更新 / stars 不足
python github-daily-picks/scripts/search_repos.py \
  --query "video subtitle remover" --query "self hosted media" \
  --min-stars 300 --months 12

# 核准入围仓库的真实元数据
python github-daily-picks/scripts/repo_meta.py owner/repo other/repo
```

## 目录结构

```
github-daily-picks/
├── SKILL.md                        # 工作流、硬门槛、边界
├── assets/card-template.html       # 卡片模板
├── references/
│   ├── onboarding.md               # 首次上手：从历史对话生成画像
│   ├── card-spec.md                # 卡片字段、文风、反例
│   └── profile-template.md         # 画像模板（问卷兜底）
└── scripts/
    ├── search_repos.py             # 搜候选 + 硬门槛过滤
    └── repo_meta.py                # 核准真实元数据
```

## 隐私提醒

`profile.md` 是你的个人画像，包含硬件、收入量级等信息，已在 `.gitignore` 里排除。不要提交到公开仓库。

## License

MIT
