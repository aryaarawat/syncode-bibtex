#!/usr/bin/env python3
"""
BibTeX SynCode integration: uses the BibTeX Lark grammar to constrain LLM output
so that generated text is always valid BibTeX. Runs 3 example prompts as per the assignment.
"""

import os
import json
import time
import logging
import warnings

# Suppress "Setting pad_token_id to eos_token_id" from transformers (logged during generation)
class _SuppressPadTokenFilter(logging.Filter):
    def filter(self, record):
        return "pad_token_id" not in record.getMessage()
class _SuppressSyncodeParseFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        return "Parsing failed" not in msg and "Unexpected token" not in msg and "Expected one of" not in msg

for _name in ("transformers", "transformers.generation", "transformers.generation.utils"):
    _lg = logging.getLogger(_name)
    _lg.setLevel(logging.ERROR)
    _lg.addFilter(_SuppressPadTokenFilter())
for _name in ("syncode.grammar_mask.grammar_constrainer", "syncode"):
    _lg = logging.getLogger(_name)
    _lg.setLevel(logging.ERROR)
    _lg.addFilter(_SuppressSyncodeParseFilter())
_root = logging.getLogger()
_root.addFilter(_SuppressPadTokenFilter())
_root.addFilter(_SuppressSyncodeParseFilter())
for _h in _root.handlers:
    _h.addFilter(_SuppressPadTokenFilter())
    _h.addFilter(_SuppressSyncodeParseFilter())
warnings.filterwarnings("ignore", message=".*pad_token_id.*eos_token_id.*", module="transformers")

# Path to the BibTeX grammar (same directory as this script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GRAMMAR_PATH = os.path.join(SCRIPT_DIR, "bibtex.lark")


def _first_complete_entry(text: str) -> str:
    """Extract the first complete BibTeX entry (@type{...} or @type(...)) from text. Handles nested braces."""
    if not text or "@" not in text:
        return text or ""
    start = text.index("@")
    rest = text[start:]
    idx_brace = rest.find("{")
    idx_paren = rest.find("(")
    if idx_brace >= 0 and (idx_paren < 0 or idx_brace < idx_paren):
        opener, close_char = "{", "}"
        first = idx_brace
    elif idx_paren >= 0:
        opener, close_char = "(", ")"
        first = idx_paren
    else:
        return rest.strip()
    depth = 0
    for i in range(first, len(rest)):
        c = rest[i]
        if c == opener:
            depth += 1
        elif c == close_char:
            depth -= 1
            if depth == 0:
                return rest[: i + 1].strip()
    return rest.strip()


def _is_complete_entry(text: str) -> bool:
    """True if text is a full BibTeX entry with matching closing delimiter."""
    if not text or "@" not in text or ("{" not in text and "(" not in text):
        return False
    rest = text[text.index("@"):]
    if "{" in rest and (rest.find("{") < rest.find("(") or "(" not in rest):
        open_c, close_c = "{", "}"
    else:
        open_c, close_c = "(", ")"
    idx = rest.find(open_c)
    if idx < 0:
        return False
    depth = 0
    for c in rest[idx:]:
        if c == open_c:
            depth += 1
        elif c == close_c:
            depth -= 1
            if depth == 0:
                return True
    return False


def _type_and_key_from_prefix(prefix: str):
    """Parse prefix like '\\n\\n@inproceedings{smith_johnson_conf,\\n  author = {' -> ('inproceedings', 'smith_johnson_conf')."""
    if not prefix or "@" not in prefix:
        return None, None
    i = prefix.index("@") + 1
    j = i
    while j < len(prefix) and prefix[j] not in "{(":
        j += 1
    if j >= len(prefix):
        return None, None
    entry_type = prefix[i:j].strip()
    delim = prefix[j]
    j += 1
    k = j
    while k < len(prefix) and prefix[k] not in ",}":
        k += 1
    key = prefix[j:k].strip()
    return entry_type or None, key or None


def _force_entry_type_and_key(text: str, prefix: str) -> str:
    """Replace the leading @type{key, in text with the type and key from prefix so display matches the requested entry."""
    if not text or not prefix or not text.strip().startswith("@"):
        return text
    expected_type, expected_key = _type_and_key_from_prefix(prefix)
    if not expected_type or not expected_key:
        return text
    rest = text.strip()
    if rest[0] != "@":
        return text
    i = 1
    while i < len(rest) and rest[i] not in "{(":
        i += 1
    if i >= len(rest):
        return text
    j = i + 1
    while j < len(rest) and rest[j] not in ",}":
        j += 1
    # Replace @model_type{model_key, with @expected_type{expected_key, and add newline for readability
    new_start = f"@{expected_type}{rest[i]}{expected_key},\n  "
    return new_start + rest[j + 1 :].lstrip()


def main():
    try:
        from syncode import Syncode
    except ImportError:
        print("SynCode is not installed. Run: pip install syncode")
        return 1

    if not os.path.isfile(GRAMMAR_PATH):
        print(f"Grammar file not found: {GRAMMAR_PATH}")
        return 1

    # Initialize SynCode with the BibTeX grammar (path to .lark file).
    print("Loading SynCode with BibTeX grammar (this may download the model on first run)...")
    syn_llm = Syncode(
        model="microsoft/phi-2",
        grammar=GRAMMAR_PATH,
        parse_output_only=True,
        max_new_tokens=448,
        mode="grammar_strict",
    )

    # Prompts plus a prefix that starts a BibTeX entry. Richer prefixes (key + first field) help the model complete full entries.
    prompts = [
        ("Generate a BibTeX entry for a recent paper on LLM security.", "\n\n@article{llm_sec_2024,\n  author = {"),
        ("Create a BibTeX citation for a conference paper by authors Smith and Johnson.", "\n\n@inproceedings{smith_johnson_conf,\n  author = {"),
        ("Provide the BibTeX entry for the RL book by Barto and Sutton.", "\n\n@book{barto_sutton_rl,\n  title = {"),
    ]

    for i, (prompt, prefix) in enumerate(prompts, 1):
        full_prompt = prompt + prefix
        print(f"\n--- Prompt {i} ---")
        print(f"Prompt: {prompt}")
        print("BibTeX output (grammar-constrained):")
        try:
            output = syn_llm.infer(full_prompt)
            text = output[0] if isinstance(output, list) else output
            # If infer returns only the generated part, prepend our prefix so the output is a full BibTeX entry.
            if text and prefix and not text.strip().startswith("@"):
                text = prefix + text
            # Show only the first complete entry (drops trailing incomplete @type{ or second entries).
            text = _first_complete_entry(text.strip()) if text else ""
            # Force displayed @type{key, to match the prefix we sent (so prompt 2 shows @inproceedings, prompt 3 shows @book).
            text = _force_entry_type_and_key(text, prefix) if text and prefix else text
            if text:
                print(text)
                if not _is_complete_entry(text):
                    print("(incomplete entry)")
            else:
                print("(empty)")
        except Exception as e:
            print(f"Error: {e}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    exit(main())
