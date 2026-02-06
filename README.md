# BibTeX Grammar for Constrained LLM Generation with SynCode

## Assignment Overview
Create a Lark LR grammar for BibTeX citation format and use it with SynCode to constrain LLM outputs. This demonstrates how formal grammars can be used to ensure structured output generation from LLMs.

## Timeframe
One week

## Quick start

**Use Python 3.10, 3.11, or 3.12** (see [Troubleshooting](#troubleshooting) if you see a `tokenizers` build error on Python 3.13).

```bash
# Optional: create a dedicated env (conda)
conda create -n bibtex-syncode python=3.11 -y
conda activate bibtex-syncode

# Install dependencies
pip install -r requirements.txt

# Run grammar unit tests
python test.py

# Run SynCode demo (first run may download the model)
python bibtex_syncode.py
```

## Requirements
- **Python 3.10, 3.11, or 3.12** (SynCode’s pinned `tokenizers` does not support Python 3.13)
- **Lark** – `lark-parser` (grammar parsing)
- **SynCode** – [structuredllm/syncode](https://github.com/structuredllm/syncode) (grammar-constrained generation)
- **Accelerate** – required by SynCode/transformers for model loading and device mapping

Install everything with: `pip install -r requirements.txt`

## Troubleshooting

### "Failed building wheel for tokenizers" on Python 3.13

SynCode depends on `transformers==4.44.0`, which requires `tokenizers` 0.19.x. That version is built with PyO3 0.21.2 and **only supports Python up to 3.12**. On Python 3.13 there is no pre-built wheel, so pip tries to build from source and fails with:

`the configured Python interpreter version (3.13) is newer than PyO3's maximum supported version (3.12)`

**Fix:** Use Python 3.10, 3.11, or 3.12 in a new environment, then install again:

```bash
conda create -n bibtex-syncode python=3.11 -y
conda activate bibtex-syncode
cd /path/to/syncode-bibtex
pip install -r requirements.txt
```

## Tasks

### 1. Implement BibTeX Grammar
Create a Lark LALR(1) grammar that:
- Handles all standard BibTeX entry types
- Supports nested braces in field values
- Correctly processes special characters and LaTeX commands
- Is compatible with SynCode's grammar requirements

### 2. Test Grammar
A unit test file will be provided to verify your grammar implementation. The tests include various complex BibTeX examples:

- Nested braces in field values
- Special characters and LaTeX commands
- Mixed quote/brace formatting

Please see a similar ANTLR grammar here: https://github.com/antlr/grammars-v4/tree/master/bibtex (Note: This grammar is not in the Lark format)

### 3. Integrate with SynCode
Create a script that:
- Uses your grammar with SynCode for grammar-constrained generation
- Tests with at least 3 different prompts asking for BibTeX citations
- Example prompts:
  - "Generate a BibTeX entry for a 3 recent paper on LLM security"
  - "Create a BibTeX citation for a conference paper by authors Smith and Johnson"
  - "Provide the BibTeX entry for RL book Barto and Sutton"

## Deliverables / Project files
- **`bibtex.lark`** – Lark LALR(1) grammar for BibTeX (entry types, keys, nested braces, LaTeX/special chars)
- **`bibtex_syncode.py`** – SynCode integration: loads the grammar and runs 3 example prompts
- **`test.py`** – Unit tests for the grammar (run with `python test.py`)
- **`requirements.txt`** – Dependencies: `lark-parser`, `syncode`, `accelerate`
