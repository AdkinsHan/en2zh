# en2zh

Translates English markdown documents to Chinese with interleaved bilingual format.

## Why This Skill?

Reading English technical content is essential for Chinese-speaking developers, yet many find themselves stuck between two unsatisfying options: struggling through the original English text, or reading a standalone Chinese translation that loses the context of the source. **en2zh** was created to offer a third path.

- **Learn English while you read** — The interleaved format keeps the original text front and center. You read the English first, then glance at the Chinese translation only when needed. Over time, you naturally absorb vocabulary and sentence patterns without刻意studying.

- **Bilingual alternation fits Asian reading habits** — In East Asian publishing, parallel bilingual layouts (e.g. 中英對照 in Taiwan, 英中对照 in mainland China) have long been the norm for textbooks, news, and reference materials. Readers naturally scan the primary language and refer to the secondary one on demand. The blockquote-based interleaved format brings this familiar pattern to plain Markdown.

- **No more context-switching** — Unlike side-by-side or separate-file translations, interleaving keeps the original and translation in the same visual flow. You never lose your place or context when switching between languages.

- **Built for AI-assisted workflows** — This skill is designed for [Claude Code](https://docs.anthropic.com/en/docs/claude-code), automating the tedious parts (splitting large files, tracking progress, merging results) so you can focus on reading, not managing translation logistics.

## Features

- **Interleaved bilingual output**: Each English paragraph is immediately followed by its Chinese translation in blockquote (`>`) format
- **Batched processing**: Handles large files by splitting into manageable batches with progress tracking
- **Context compression**: Automatic checkpointing prevents context window overflow during long translations
- **Smart splitting**: Respects code blocks, tables, and heading boundaries — never splits inside protected blocks
- **Resume support**: Interrupted translations can be resumed from the last completed batch via `manifest.json`

## Output Format

```markdown
This is an English paragraph.

> 这是一个中文段落。

## English Heading

> ## 中文标题

- English list item

> - 中文列表项
```

## Scripts

### split_md.py

Split a markdown file into numbered batches with a manifest for progress tracking.

```bash
python scripts/split_md.py <input.md> [--batch-size 80] [--output-dir <dir>]
```

### update_manifest.py

Update a batch's translation status in the manifest.

```bash
python scripts/update_manifest.py <manifest.json> <batch_index> <status>
# status: pending | translating | translated | merged
```

### merge_md.py

Merge all translated batches back into a single markdown file.

```bash
python scripts/merge_md.py <manifest.json> [--output <output.md>]
```

## Workflow

1. **Split** — For files over ~100 lines, split into batches using `split_md.py`
2. **Translate** — Translate each batch, inserting Chinese blockquotes below each English block
3. **Merge** — Reassemble translated batches using `merge_md.py`
4. **Review** — Verify formatting and move the final file to the desired location

For small files (< 100 lines), skip splitting and translate directly in a single pass.

## Translation Rules

- Technical terms with widely-used English forms (API, SDK, MCP, LLM, etc.) are kept as-is
- Proper nouns (product names, company names, person names) are kept in original form
- Code blocks and inline code are not translated
- Images and embeds are not translated; only surrounding text is translated
- Tables are kept intact with a complete translated table appended after the original
- Frontmatter (YAML between `---`) is not translated

## How to Use

This project is a [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill. Once installed, Claude Code will automatically invoke it when you ask to translate markdown files.

### Installation

1. Clone this repository to your Claude Code skills directory:

```bash
git clone https://github.com/AdkinsHan/en2zh.git ~/.claude/skills/en2zh
```

2. The skill is now available. Claude Code will detect it via the `SKILL.md` file.

### Usage

In a Claude Code session, simply ask it to translate a markdown file:

```
Translate /path/to/my-article.md to Chinese
```

Or use the skill name directly:

```
/en2zh /path/to/my-article.md
```

Claude Code will handle the rest — splitting, translating, merging — and produce a `my-article_zh.md` file alongside the original.

### Manual Usage (Without Claude Code)

You can also use the scripts independently:

```bash
# 1. Split a large file into batches
python scripts/split_md.py article.md --batch-size 80

# 2. Translate each batch file manually
#    (edit each 001_batch.md, 002_batch.md, etc.)

# 3. Update manifest after translating each batch
python scripts/update_manifest.py article_batches/manifest.json 1 translated

# 4. Merge all translated batches
python scripts/merge_md.py article_batches/manifest.json
```

## Notes

- **Large files may fail due to context limits** — If the source markdown is too large, the translation may fail midway because the conversation context window runs out. This is expected. Simply run `/compact` to compress the context, then ask Claude Code to continue from where it left off (check `manifest.json` for progress). The batch-level checkpoint mechanism ensures no work is lost.

## License

See [LICENSE](LICENSE) for details.
