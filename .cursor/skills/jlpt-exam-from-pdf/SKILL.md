---
name: jlpt-exam-from-pdf
description: >-
  Converts scanned JLPT exam PDFs (真题/答案) into structured Markdown under
  data/exam/. Use when the user provides JLPT PDF files, asks to create exam
  markdown like JLPT_N2_2019_12.md, or mentions 真題・読解・聴解 transcription.
---

# JLPT Exam PDF → Markdown

## Output target

Create `data/exam/<level>/JLPT_<LEVEL>_<YYYY>_<MM>.md` matching the project template:

- Reference: [data/exam/n2/JLPT_N2_2019_12.md](../../data/exam/n2/JLPT_N2_2019_12.md)
- N2 examples: [JLPT_N2_2019_07.md](../../data/exam/n2/JLPT_N2_2019_07.md), [JLPT_N2_2018_12.md](../../data/exam/n2/JLPT_N2_2018_12.md), [JLPT_N2_2018_07.md](../../data/exam/n2/JLPT_N2_2018_07.md)
- N1 examples: [JLPT_N1_2019_07.md](../../data/exam/n1/JLPT_N1_2019_07.md), [JLPT_N1_2019_12_listening.md](../../data/exam/n1/JLPT_N1_2019_12_listening.md), [JLPT_N1_2020_12.md](../../data/exam/n1/JLPT_N1_2020_12.md), [JLPT_N1_2021_07.md](../../data/exam/n1/JLPT_N1_2021_07.md)
- Output only: edit `data/exam/**/JLPT_*.md` directly (one-off build scripts are not kept in repo)

## Workflow

Copy this checklist and track progress:

```
- [ ] 1. Identify level, date, PDF paths (真题 + 答案)
- [ ] 2. Render PDF pages to PNG
- [ ] 3. Extract Q1–47 from PDF/vision (文字・語彙・文法)
- [ ] 4. Extract 読解 passages + Q48–73
- [ ] 5. Extract 聴解 choices + answers
- [ ] 6. Write Markdown + META yaml
- [ ] 7. Spot-check answers against 答案.pdf
```

### Step 1 — Inputs

| File | Role |
|------|------|
| `N2-YYYY-MM-真题.pdf` | Questions (often scanned images) |
| `N2-YYYY-MM-答案.pdf` | Official answer key |
| `YYYY年M月N2.mp3` | Listening audio (optional link in META) |

### Step 2 — Render PDF (required for image PDFs)

`pdfplumber` often returns empty text on scans. Use PyMuPDF:

```bash
python scripts/extract_jlpt_pdf.py "/path/to/N2-2019-07-真题.pdf" \
  --out data/exam/n2/_pdf_2019_07_pages
```

Then **read PNG pages** with the vision tool (page 1 ≈ cover, 2 ≈ rubric, 3+ ≈ questions).

### Step 3 — Section mapping (N2)

| 問題 | Questions | Content |
|------|-----------|---------|
| 1 | 1–5 | 読み方 |
| 2 | 6–10 | 漢字書き |
| 3 | 11–13 | 語彙（文脈） |
| 4 | 14–20 | 語彙（文脈） |
| 5 | 21–25 | 言い換え |
| 6 | 26–30 | 用法 |
| 7 | 31–42 | 文法1 |
| 8 | 43–47 | 並べ替え（★） |
| 9 | 48–52 | 文章の文法 |
| 10 | 53–57 | 短文 |
| 11 | 58–66 | 中文・長文 |
| 12 | 67–68 | A/B 比較 |
| 13 | 69–71 | 長文 |
| 14 | 72–73 | 情報検索 |
| 聴解1–5 | L1–L25 | 選択肢 + 答案 |

### Step 4 — Markdown patterns

**Normal MCQ:**

```markdown
#### Q1

**林さんは誰に対しても＿等しく＿接する人だ。**

- [ ] 1. やさしく
- [ ] 2. ひとしく ✅
- [ ] 3. したしく
- [ ] 4. きびしく

`answer: 2`

---
```

- Wrap tested words in `_underscores_` in the stem.
- Mark correct option with ` ✅` and `` `answer: N` ``.

**Reorder (問題8):**

```markdown
#### Q43

**…＿＿＿＿ ★ ＿＿＿…**

選択肢：1.… 2.… 3.… 4.…

> 並び順: … → ★… → …

- [ ] 1. …
...

`answer: 3`
```

**Reading passage:**

```markdown
#### 【文章(1)】

> Passage text…
>
> （注1）…
```

**Listening (no script on paper):**

```markdown
`answer: (音声確認要)`
```

Use official key values when available from 答案.pdf or trusted answer tables.

### Step 5 — Answers

1. Read `答案.pdf` (render pages if scanned).
2. Cross-check with a second source if ambiguous.
3. For 聴解, prefer official key; note `(音声確認要)` only when key is missing.

### Step 6 — Quality

- Do not invent question text; transcribe from PDF/PNG.
- Long 読解 may be paraphrased only if full text is unreadable — add `> ※ 要PDF確認` note.
- Keep META `sections` in sync with question ranges.
- Filename: `JLPT_N2_2019_07.md` for July 2019 N2.

## Rebuild existing exam

Edit the target `data/exam/**/JLPT_*.md` in place, then run `python scripts/sync_exams.py`.

### N1 section mapping (December 2020)

| 問題 | Questions | Content |
|------|-----------|---------|
| 1 | 1–6 | 読み方 |
| 2 | 7–13 | 語彙（文脈） |
| 3 | 14–19 | 言い換え |
| 4 | 20–25 | 用法 |
| 5 | 26–35 | 文法1 |
| 6 | 36–40 | 並べ替え（★） |
| 7 | 41–44 | 文章の文法 |
| 8–13 | 45–68 | 読解 |
| 聴解1–5 | L1–L35 | 聴解 |

### N1 section mapping (July 2021)

| 問題 | Questions | Content |
|------|-----------|---------|
| 1 | 1–6 | 読み方 |
| 2 | 7–13 | 語彙（文脈） |
| 3 | 14–19 | 言い換え |
| 4 | 20–25 | 用法 |
| 5 | 26–35 | 文法1 |
| 6 | 41–45 | 並べ替え（★） |
| 7 | 46–50 | 文章の文法 |
| 8–13 | 51–75 | 読解 |
| 聴解1–5 | L1–L36 | 聴解 |

For new exams, copy that script’s `ANSWERS` dict + `q_block()` helpers, or hand-edit MD following the template.

## Anti-patterns

- Do not use `pdfplumber` alone on scanned 真题 — it returns blank pages.
- Do not copy December exam text into July files (content differs).
- Do not commit large `_pdf_*_pages/` folders; add to `.gitignore` if needed.
