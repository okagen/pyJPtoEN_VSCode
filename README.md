# JP→EN Fine‑Tuning & Word Doc Translation

This repository demonstrates **two end‑to‑end workflows** using the OpenAI API:
1. **`fine_tuning.py`** – Turns a bilingual glossary (`日英対照表.xlsx`) into JSONL and fine‑tunes a GPT model.
2. **`use.py`** – Uses the resulting fine‑tuned model to translate every paragraph (including tables) inside a Word document (`.docx`) from **Japanese** to **English**, preserving styles.

# Table of Contents

1. [Prerequisites](#Prerequisites)
2. [Core dependencies](#CoreDependencies)
3. [Repo Layout](#RepoLayout)
4. [Fine‑Tuning (fine_tuning.py) outline](#Fine‑Tuning)
5. [Document Translation (use.py) outline](#DocumentTranslation)

---
<a id="Prerequisites"></a>
## ■　Prerequisites

* **Python ≥ 3.9** (tested on 3.11)
* An **OpenAI API key** with fine‑tuning access.
* An Excel glossary with two columns:
  * **「日本語」** – source phrases
  * **「英語」** – target phrases
* The Word doc(s) you want to translate (`.docx`).

<a id="CoreDependencies"></a>
## ■　Core dependencies

* **openai** – OpenAI Python SDK
* **pandas** – Excel reading
* **python‑dotenv** – load `.env`
* **python‑docx** – Word manipulation
* **tqdm** – progress bar

<a id="RepoLayout"></a>
## ■　Repo Layout

```
.
├── 日英対照表.xlsx            # bilingual glossary (example)
├── fine_tuning.py            # launches fine‑tune job
├── use.py                    # translates Word docs
├── requirements.txt          # deps list
└── README.md                 # this file
```

<a id="Fine‑Tuning"></a>
## ■　Fine‑Tuning (fine_tuning.py) outline

### Run

```bash
$ python fine_tuning.py
```

### What happens

1. **Excel → dict** via `pandas`.
2. **dict → JSONL** in‑memory (`vocab_chat.jsonl`).
3. File upload: `purpose="fine‑tune"`.
4. Fine‑tune job on **`gpt‑3.5‑turbo‑0125`** with hyper‑params: 3 epochs, lr‑mult 0.1, batch auto.
5. Poll until `succeeded` / `failed` (every 30 s).
6. Print the **model ID** on success – **copy this** for `use.py`.

> View progress anytime: `https://platform.openai.com/finetune/`.

### Customising

```bash
$ python fine_tuning.py \
    --data-file data/my_glossary.xlsx \
    --model gpt-4o-mini \
    --epochs 5 \
    --suffix "jp-en-2025-07"
```

<a id="DocumentTranslation"></a>
## ■　Document Translation (use.py) outline

### Translate a Word doc:

```bash
$ python use.py 87Q3_決算短信文章案_05281800.docx
# => output_87Q3_決算短信文章案_05281800.docx (styles preserved)
```

### Key features of **`use.py`**

* **Iterates** through every paragraph **and tables** inside the DOCX.
* **Calls** the fine‑tuned model with prompt:
  > "You are a translator from Japanese to English."
* **Replaces** the Japanese text in‑place while preserving original runs/styles when possible.
* **Saves** to an auto‑incremented filename to avoid overwriting originals.
* **Progress** indicator via `tqdm`.


