---
name: entzh
description: Translates English markdown documents to Chinese with interleaved bilingual format. Use when the user asks to translate markdown files, notes, or documents from English to Chinese, or when the user mentions entzh, English-to-Chinese translation, or bilingual markdown formatting. Handles large files via batched processing with automatic context compression after each step to prevent context window overflow.
---

# Entzh — English to Chinese Markdown Translator

## Overview

Translate English markdown into interleaved bilingual format: each English paragraph followed by its Chinese translation in blockquote (`>`) format. Handles large files via batched processing with progress tracking.

## Output Format

Every English text block is immediately followed by its Chinese translation in markdown blockquote:

```markdown
This is an English paragraph.

> 这是一个中文段落。

## English Heading

> ## 中文标题

- English list item

> - 中文列表项
```

**Rules:**
- ⚠️ **STRICT INTERLEAVING**: Each English paragraph/heading/list item must be **immediately** followed by its Chinese translation. NEVER group multiple Chinese translations together after a block of English.
- Chinese text uses `>` blockquote on every line of multi-line paragraphs
- Headings, list items, code block descriptions, table headers — all get translated
- **Tables are NOT translated with `>` blockquote** — instead, keep the original table intact and append a complete translated table after it (same column structure, translated cell content)
- Code blocks (` ``` `) and inline code are NOT translated; keep them as-is
- Images, embeds, and SVG are NOT translated and need no Chinese block at all — not even for alt text (see **Skip Rules** below). Only the surrounding text is translated.
- If the source text already contains `>` blockquotes, the Chinese translation uses `>>` (nested blockquote) to distinguish from translation blockquotes
- Frontmatter (YAML between `---`) is NOT translated
- Blank lines between English and Chinese blocks are preserved

## Skip Rules (no translation, keep as-is)

The following content is **skipped**: copy it into the output byte-for-byte, add no Chinese blockquote, and do not translate any text inside it.

1. **Image links** — image references are not translated, including their alt text, title, filename, and URL:
   - Markdown images and embeds: `![alt](url)`, `![[image.png]]`
   - HTML images: `<img src="..." alt="...">`
   - Bare image URLs on their own line (e.g. `https://example.com/pic.png`)
2. **SVG** — inline `<svg>...</svg>` markup (including its `<title>`, `<desc>`, and `<text>` contents), linked `.svg` assets, and SVG URLs. Preserve the markup exactly; never rewrite or annotate it.
3. **Source that is already Chinese** — skip translation in these cases:
   - A block whose prose is already Chinese: keep it unchanged, no duplicate Chinese blockquote.
   - A file whose body is predominantly Chinese: produce no `_zh.md` output for it at all, and report it as skipped.
   - Mixed blocks: translate only the English sentences; leave the existing Chinese text untouched.

If a skipped element sits between two English paragraphs, it must not interrupt interleaving — the paragraph before and the paragraph after are each translated normally.

## Translation Quality Guidelines

- **Technical terms**: Keep widely-used English technical terms as-is (API, SDK, MCP, LLM, vector store, embedding, etc.) when Chinese translations are uncommon or ambiguous. You may append a brief Chinese explanation on first occurrence: "向量存储（vector store）"
- **Proper nouns**: Keep product names, company names, person names in original form (Mem0, Letta, Mercury, Claude, etc.). Never transliterate.
- **Tone and style**: Match the source tone — formal for academic/technical writing, conversational for blog posts, precise for documentation
- **Sentence structure**: Prefer natural Chinese phrasing over word-by-word translation. Reorder clauses if needed for fluency
- **Ambiguity**: When an English word has multiple meanings, choose based on the surrounding context, not the most common dictionary definition

## Output File Naming

Translated files should be saved alongside the original with `_zh` appended before the extension:

- Original: `my-article.md` → Translated: `my-article_zh.md`
- Original: `2026-04-20 19-36-The shape of Vision.md` → Translated: `2026-04-20 19-36-The shape of Vision_zh.md`

The translated file goes in the same directory as the original.

## Workflow

Copy this checklist and track progress:

```
Entzh Progress:
- [ ] Step 1: Split markdown into batches
- [ ] Step 2: Translate batch by batch
- [ ] Step 3: Merge translated batches
- [ ] Step 4: Final review and move to vault
```

**⚠️ Context Management**: This skill handles large files that can consume significant context. After completing each major step, perform a **context compression checkpoint** (detailed below each step). This ensures the conversation never runs out of context window, while preserving all essential information in external files for later retrieval.

### Step 1: Split markdown into batches

For files over ~100 lines, split into manageable batches:

```bash
python /Users/han/.claude/skills/entzh/scripts/split_md.py <input.md> --batch-size 80
```

This creates `<input>_batches/` with:
- `000_frontmatter.md` — YAML frontmatter (if present)
- `001_batch.md`, `002_batch.md`, ... — numbered batch files
- `manifest.json` — progress tracking metadata

For small files (< 100 lines of body text, excluding frontmatter), skip splitting and translate directly in a single pass:
1. Read the source file
2. Produce the interleaved bilingual output (strict one-by-one interleave)
3. Write the output to `<original_name>_zh.md` in the same directory as the source file. **You must construct the absolute output path** by taking the source file's directory and appending the new filename. For example, if the source file is `/Users/han/.openclaw/workspace/docs/notes/article.md`, the output path is `/Users/han/.openclaw/workspace/docs/notes/article_zh.md`. Always pass both `file_path` (absolute path) and `content` (the full translated text) to the Write tool.

#### Context Compression After Step 1

After splitting is complete, write a `workflow_state.md` file in the batch directory to capture all essential state. Then explicitly release the splitting details from context — you only need the summary going forward.

**Create `<batch_dir>/workflow_state.md`:**

```markdown
# Entzh Workflow State

## Source
- File: <original_filename>
- Path: <absolute_path_to_source>
- Has frontmatter: yes/no

## Batch Directory
- Path: <absolute_path_to_batch_dir>
- Manifest: <absolute_path_to_manifest.json>
- Total batches: N
- Batch size: 80 (or custom)

## Current Step
- Completed: Step 1 (Split)
- Next: Step 2 (Translate)

## Key Paths
- Frontmatter: <batch_dir>/000_frontmatter.md (if exists)
- Batches: <batch_dir>/001_batch.md through <batch_dir>/NNN_batch.md
```

**After writing**: State — "Step 1 compression checkpoint saved. Splitting details released from context. All essential paths are in `workflow_state.md`."

### Step 2: Translate batch by batch

For each batch file, read it and produce the interleaved bilingual output.

**Translation process for each batch:**

1. **Check for translation context**: If `translation_context.md` exists in the batch directory, read it first to restore terminology, style decisions, and consistency notes from previous batches.
2. Read the batch file content
3. Translate **one paragraph at a time**, immediately inserting its Chinese translation below it before moving to the next paragraph. The output must be strictly interleaved: English paragraph → blank line → Chinese blockquote → blank line → next English paragraph → …
4. Write the translated content back to the same batch file (overwrite). **You must use the absolute path** of the batch file (e.g., `<batch_dir>/001_batch.md`) and pass both `file_path` (absolute path) and `content` (the full translated batch text) to the Write tool. The batch directory path comes from the split step output.
5. Update the manifest:
6. **Context checkpoint**: If the current batch index is a multiple of 5 (i.e., batch 5, 10, 15, …), perform a context compression checkpoint (see below).

**⚠️ CRITICAL RULE — Interleave paragraph by paragraph, NEVER batch-translate:**

- **DO**: After translating ONE English paragraph/heading/list item, insert its `> ` blockquote translation immediately below it, then move to the next.
- **DON'T**: Translate multiple paragraphs first and then append all Chinese translations together.
- **DON'T**: Treat an entire section or group of paragraphs as a single "semantic block".
- **DON'T**: Output a block of English followed by a block of Chinese — this is the #1 mistake to avoid.

**Wrong (all Chinese at the end):**
```markdown
First paragraph.

Second paragraph.

> 第一段。

> 第二段。
```

**Right (interleaved one-by-one):**
```markdown
First paragraph.

> 第一段。

Second paragraph.

> 第二段。
```

```bash
python /Users/han/.claude/skills/entzh/scripts/update_manifest.py <manifest.json> <batch_index> translated
```

**Important:** Process ONE batch at a time. After translating each batch, update the manifest before moving to the next. This ensures progress is saved even if interrupted.

**Blockquote formatting examples:**

Single-line paragraph:
```markdown
English paragraph text.

> 英文段落文本。
```

Multi-line paragraph:
```markdown
First line of English paragraph.
Second line of English paragraph.

> 英文段落的第一行。
> 英文段落的第二行。
```

Heading:
```markdown
## Introduction

> ## 介绍
```

List items (translate each item individually):
```markdown
- First item

> - 第一项

- Second item

> - 第二项
```

Code blocks — keep untranslated, only translate surrounding text:
```markdown
Run the following command:

> 运行以下命令：

```bash
npm install
```
```

Images and embeds — keep untranslated (alt text included), no Chinese block, only translate surrounding text:
```markdown
Here is the architecture diagram:

> 这是架构图：

![[architecture.png]]

The diagram above shows...

> 上图展示了...
```

Inline formatting — preserve bold, italic, links, etc. in translation:
```markdown
This is a **bold** and *italic* example with a [link](url).

> 这是一个**加粗**和*斜体*的示例，带有[链接](url)。
```

Nested blockquotes — when source text already uses `>`, use `>>` for the translation:
```markdown
> Original quoted text

>> 原始引用文本

> Another quoted paragraph

>> 另一个引用段落
```

Tables — keep the original table intact, then append a complete translated table after it. Do NOT use `>` blockquote for tables (it breaks rendering). Do NOT translate the table row-by-row — translate the entire table as a whole and append it:
```markdown
| Name  | Role  | Status |
|-------|-------|--------|
| Alice | Admin | Active |
| Bob   | User  | Inactive |

| 姓名  | 角色  | 状态   |
|-------|-------|--------|
| 爱丽丝 | 管理员 | 活跃   |
| 鲍勃   | 用户   | 未激活 |
```

Key table rules:
- The translated table uses the same column structure (same number of `|` separators)
- Separator rows (`|---|`) are kept as-is in the translated table
- Translate header cells and data cells, keep alignment syntax (`:`) if present
- Do NOT split a table across batches — the entire table must stay together

### Context Compression Checkpoint (every 5 batches)

When the batch index is a multiple of 5 (5, 10, 15, …), the conversation context will have accumulated a lot of translated content. To prevent running out of context window, perform a **context compression checkpoint**:

1. **Create/update `translation_context.md`** in the batch directory. **You must use the absolute path** of the batch directory (the same directory that contains `manifest.json`) to construct the file path, e.g., `<batch_dir>/translation_context.md`. Pass both `file_path` (absolute path) and `content` to the Write tool. Write a concise summary that captures everything needed to maintain translation consistency for the remaining batches. The file should contain:

```markdown
# Translation Context

## Terminology Glossary
| English | Chinese | Notes |
|---------|---------|-------|
| term1 | 译名1 | 首次出现在 batch N |
| term2 | 译名2 | 保持原文不译 |

## Style Decisions
- [Document any style choices made, e.g.: "使用'模型'而非'模型'来翻译 model"]
- [Tone decisions, formality level, etc.]

## Consistency Notes
- [Any recurring phrases and how they were translated]
- [Patterns observed, e.g.: "All headings use noun phrases"]

## Already Translated Content Summary
- Batch 1-5: [1-2 sentence summary of what was covered, key topics/sections]
```

2. **Signal context release**: After writing the context file, explicitly state: "Context checkpoint saved to `translation_context.md`. Previous batch details can be released from context — rely on the context file for consistency going forward."

3. **Resume with context**: For batch 6 onward, always read `translation_context.md` first before translating. Update it again at batch 10, 15, etc. Each update should:
   - Extend the terminology glossary with new terms from the most recent 5 batches
   - Update the "Already Translated Content Summary" to cover all completed batches
   - Remove any resolved consistency notes (no longer relevant)

**Why this matters**: Without compression, after ~10 batches the conversation context fills up with the full text of all previous translations, causing degraded quality or truncation. The checkpoint file acts as "external memory" that is compact (~50-100 lines) yet preserves all the information needed for consistent translation.

#### Context Compression After Step 2 (All Batches Done)

After all batches are translated, update both `translation_context.md` and `workflow_state.md` to capture the complete translation state, then release all batch-level details from context.

**Update `<batch_dir>/translation_context.md`** — add a final section summarizing the full document:

```markdown
## Full Document Summary
- All N batches translated
- Document covers: [1-2 sentence summary of the entire document's topic and scope]
- Key terminology established across all batches: [list any critical terms]
```

**Update `<batch_dir>/workflow_state.md`:**

```markdown
# Entzh Workflow State

## Source
- File: <original_filename>
- Path: <absolute_path_to_source>
- Has frontmatter: yes/no

## Batch Directory
- Path: <absolute_path_to_batch_dir>
- Manifest: <absolute_path_to_manifest.json>
- Total batches: N (all translated)

## Current Step
- Completed: Step 2 (Translate)
- Next: Step 3 (Merge)

## Translation Context
- Path: <batch_dir>/translation_context.md
- Summary: All N batches translated. Terminology and style consistency preserved in translation_context.md.
```

**After writing**: State — "Step 2 compression checkpoint saved. All batch translation details released from context. Consistency info preserved in `translation_context.md`. Workflow state in `workflow_state.md`."

### Step 3: Merge translated batches

After all batches are translated:

```bash
python /Users/han/.claude/skills/entzh/scripts/merge_md.py <manifest.json>
```

This produces `<source>_zh.md` in the batch directory. Verify the output file before proceeding.

#### Context Compression After Step 3

After merging, update `workflow_state.md` to reflect the merge result. The merged file is now the single source of truth — all batch-level details can be released.

**Update `<batch_dir>/workflow_state.md`:**

```markdown
# Entzh Workflow State

## Source
- File: <original_filename>
- Path: <absolute_path_to_source>

## Merged Output
- Path: <absolute_path_to_merged_zh_file>
- Location: <batch_dir>/<source>_zh.md

## Current Step
- Completed: Step 3 (Merge)
- Next: Step 4 (Final review)

## Batch Directory
- Path: <absolute_path_to_batch_dir>
- Can be cleaned up after Step 4 is confirmed successful
```

**After writing**: State — "Step 3 compression checkpoint saved. All batch details released from context. The merged file at `<path>` is the single source of truth for Step 4."

### Step 4: Final review and move to vault

1. Read the merged output file and verify:
   - Every English block has a corresponding Chinese blockquote, except the skipped content defined in **Skip Rules** (image links, SVG, already-Chinese text), which appears unchanged with no Chinese block
   - No broken markdown formatting
   - Code blocks are preserved intact
   - Frontmatter is intact
2. Move or copy the final file to the desired vault location. **Use the Write tool with the absolute destination path** (e.g., `/Users/han/.openclaw/workspace/docs/notes/article_zh.md`) and pass both `file_path` (absolute path) and `content` (the merged file content).
3. Clean up the batch directory if no longer needed

#### Context Compression After Step 4

After the final file is in place and verified, perform a final compression. The translation is complete — only the result matters now.

**Final update to `<batch_dir>/workflow_state.md`:**

```markdown
# Entzh Workflow State

## Result
- Status: ✅ Complete
- Source: <original_filename>
- Translated file: <absolute_path_to_final_zh_file_in_vault>
- Batch directory: <batch_dir> (can be deleted)

## Completed Steps
- [x] Step 1: Split markdown into batches
- [x] Step 2: Translate batch by batch
- [x] Step 3: Merge translated batches
- [x] Step 4: Final review and move to vault
```

**After writing**: State — "Step 4 compression checkpoint saved. Translation complete. All intermediate details released from context. Final file at `<path>`."

## Scripts

### split_md.py
Split a markdown file into numbered batches with a manifest for progress tracking.

```bash
python /Users/han/.claude/skills/entzh/scripts/split_md.py <input.md> [--batch-size 80] [--output-dir <dir>]
```

### update_manifest.py
Update a batch's status in the manifest after translation.

```bash
python /Users/han/.claude/skills/entzh/scripts/update_manifest.py <manifest.json> <batch_index> <status>
# status: pending | translating | translated | merged
```

### merge_md.py
Merge all translated batches into a single output file.

```bash
python /Users/han/.claude/skills/entzh/scripts/merge_md.py <manifest.json> [--output <output.md>]
```

## Tips

- **Batch size tuning**: Use `--batch-size 60` for very large paragraphs, `--batch-size 120` for list-heavy content. Default 80 works for most documents.
- **Resuming**: If interrupted, check `manifest.json` to see which batches are still `pending` and resume from there. If `translation_context.md` exists, read it first to restore consistency.
- **Context compression**: Two levels of context compression keep the conversation lean:
  1. **Step-level compression**: After each major step (1–4), `workflow_state.md` is updated with only the essential paths and state needed for the next step. Previous step details are released from context.
  2. **Batch-level compression**: During Step 2, every 5 batches a `translation_context.md` checkpoint captures terminology, style decisions, and progress summaries so translation quality remains consistent.
- **Small files**: For files under ~100 lines, skip the split/merge cycle and translate directly in a single pass.
- **Tables**: Never translate a table row-by-row with `>` blockquotes. Keep the original table intact, then append a complete translated table after it with the same column structure. The split script already ensures tables are never broken across batches.
- **Obsidian elements**: Wikilinks (`[[note]]`), embeds (`![[image.png]]`), callouts (`> [!note]`), and tags (`#tag`) are structural syntax — keep them as-is, only translate any surrounding visible text. Callout titles (the text after `[!type]`) can be translated.
- **Special elements**: Footnotes follow the standard rule — translate text content, keep structural syntax, wrap Chinese in `> `.
- **Mixed-language source**: If the source file already contains Chinese (e.g., a Chinese title in the filename), preserve the existing Chinese as-is, only translate the English portions. A block or file that is already Chinese is skipped per the **Skip Rules**.
