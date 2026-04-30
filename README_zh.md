# en2zh

将英文 Markdown 文档翻译为中文，采用交错双语格式。

## 为什么要开发这个技能？

阅读英文技术内容对中文开发者来说不可或缺，但许多人面临两个不太理想的选择：硬啃英文原文，或者读一份脱离原文语境的独立中文翻译。**en2zh** 提供了第三条路。

- **边读边学英语** — 交错格式让原文始终在眼前。你先读英文，只在需要时才瞟一眼中文翻译。久而久之，无需刻意学习就能自然积累词汇和句式。

- **双语交替符合亚洲阅读习惯** — 在东亚出版界，中英对照排版（如台湾的中英對照、大陆的英中对照）早已是教材、新闻和参考书的常见形式。读者习惯于扫读主要语言、按需参考辅助语言。基于引用块的交错格式将这一熟悉的模式带入了纯 Markdown 环境。

- **告别语境切换** — 与左右对照或分文件翻译不同，交错格式让原文和译文处于同一视觉流中，切换语言时不会丢失阅读位置或上下文。

- **为 AI 辅助工作流而生** — 本技能专为 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 设计，自动处理繁琐环节（拆分大文件、跟踪进度、合并结果），让你专注于阅读本身。

### 为什么不用传统翻译软件？

机器翻译工具（Google 翻译、DeepL 等）产出虽然能用，但总是带着一股"机翻味"。LLM 驱动的翻译能理解上下文、消解多义词歧义，生成自然流畅的中文，同时尊重原文的语气——技术文档读起来像技术文档，博客文章读起来像博客文章，差别一读便知。

### 适合哪些人？

- **RSS 订阅者** — 订阅了英文 RSS 源但阅读吃力？用 [Obsidian Web Clipper](https://obsidian.md) 将文章保存为 Markdown，再用 en2zh 翻译即可。
- **文档阅读者** — 日常阅读英文文档（API 参考、SDK 指南、RFC 等），希望有双语对照帮助快速理解。
- **语言学习者** — 希望通过双语对照阅读来提升阅读能力，在语境中自然积累词汇，而非死记硬背。
- **笔记爱好者** — 使用 Obsidian、Logseq 等工具剪藏网页文章，希望知识库中保留双语笔记。

## 功能特性

- **交错双语输出**：每个英文段落后紧跟其对应的中文翻译，使用引用格式（`>`）
- **分批处理**：将大文件拆分为可管理的批次，支持进度跟踪
- **上下文压缩**：自动检查点机制防止长翻译过程中的上下文窗口溢出
- **智能拆分**：尊重代码块、表格和标题边界，不会在受保护块内部拆分
- **断点续传**：通过 `manifest.json` 可从中断处恢复翻译

## 输出格式

```markdown
This is an English paragraph.

> 这是一个中文段落。

## English Heading

> ## 中文标题

- English list item

> - 中文列表项
```

## 脚本

### split_md.py

将 Markdown 文件拆分为编号批次，生成 manifest 用于进度跟踪。

```bash
python scripts/split_md.py <input.md> [--batch-size 80] [--output-dir <dir>]
```

### update_manifest.py

更新 manifest 中批次的翻译状态。

```bash
python scripts/update_manifest.py <manifest.json> <batch_index> <status>
# status: pending | translating | translated | merged
```

### merge_md.py

将所有已翻译的批次合并为单个 Markdown 文件。

```bash
python scripts/merge_md.py <manifest.json> [--output <output.md>]
```

## 工作流程

1. **拆分** — 超过约 100 行的文件，使用 `split_md.py` 拆分为批次
2. **翻译** — 逐批翻译，在每个英文块下方插入中文引用
3. **合并** — 使用 `merge_md.py` 将翻译后的批次重新组装
4. **审阅** — 验证格式并将最终文件移动到目标位置

小文件（< 100 行）可跳过拆分，直接一次性翻译。

## 翻译规则

- 广泛使用的英文技术术语（API、SDK、MCP、LLM 等）保持原文
- 专有名词（产品名、公司名、人名）保持原文
- 代码块和行内代码不翻译
- 图片和嵌入内容不翻译，仅翻译周围文字
- 表格保留原文，在其后附加完整的中文翻译表格
- Frontmatter（`---` 之间的 YAML）不翻译

## 如何使用

本项目是一个 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 技能（skill）。安装后，当您要求翻译 Markdown 文件时，Claude Code 会自动调用它。

### 安装

1. 将此仓库克隆到 Claude Code 的技能目录下：

```bash
git clone https://github.com/AdkinsHan/en2zh.git ~/.claude/skills/en2zh
```

2. 技能即已就绪。Claude Code 会通过 `SKILL.md` 文件自动检测到它。

### 使用

在 Claude Code 会话中，直接要求翻译一个 Markdown 文件即可：

```
Translate /path/to/my-article.md to Chinese
```

或直接使用技能名称：

```
/en2zh /path/to/my-article.md
```

Claude Code 会自动处理拆分、翻译、合并等步骤，并在原文旁边生成 `my-article_zh.md` 文件。

### 手动使用（不依赖 Claude Code）

你也可以独立使用这些脚本：

```bash
# 1. 将大文件拆分为批次
python scripts/split_md.py article.md --batch-size 80

# 2. 手动翻译每个批次文件
#    （编辑 001_batch.md、002_batch.md 等）

# 3. 翻译完每个批次后更新 manifest
python scripts/update_manifest.py article_batches/manifest.json 1 translated

# 4. 合并所有已翻译的批次
python scripts/merge_md.py article_batches/manifest.json
```

## 注意事项

- **大文件可能因上下文不足而失败** — 如果源 Markdown 文件过大，翻译可能会在中途因对话上下文窗口耗尽而中断。这是正常现象。只需执行 `/compact` 压缩上下文，然后让 Claude Code 从中断处继续即可（通过 `manifest.json` 查看进度）。批级别的检查点机制确保不会丢失已完成的工作。

## 许可证

详见 [LICENSE](LICENSE)。
