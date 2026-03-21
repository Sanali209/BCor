"""Modernized NLP Pipeline for rule-based text transformation.

Ported and improved from legacy NLPSimple/NLPPipline.py.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import nltk


@dataclass
class ReplaceRule:
    """A rule to replace occurrences of specified patterns with a target string."""
    target: str
    patterns: list[str]


@dataclass
class ExtendRule:
    """A rule to append or prepend a string to matches of specified patterns."""
    prefix: str
    patterns: list[str]


class NlpPipeline:
    """Main pipeline for processing text through a series of rules and tokenization."""

    def __init__(self) -> None:
        self.text: str = ""
        self.tokens: list[str] = []
        self.replace_rules: list[ReplaceRule] = []
        self.extend_rules: list[ExtendRule] = []
        self._initialized: bool = False

    def _ensure_nltk(self) -> None:
        """Ensure necessary NLTK data is downloaded."""
        if not self._initialized:
            try:
                nltk.data.find("tokenizers/punkt")
                nltk.data.find("tokenizers/punkt_tab") # Newer nltk versions
            except LookupError:
                nltk.download("punkt", quiet=True)
                nltk.download("punkt_tab", quiet=True)
            self._initialized = True

    def set_text(self, text: str) -> None:
        """Set the input text for the pipeline."""
        self.text = text

    def get_text(self) -> str:
        """Get the current state of the text."""
        return self.text

    def get_tokens(self) -> list[str]:
        """Get the tokens generated from the text."""
        return self.tokens

    def add_replace_rule(self, target: str, patterns: list[str]) -> None:
        """Add a replacement rule to the pipeline."""
        self.replace_rules.append(ReplaceRule(target, patterns))

    def add_extend_rule(self, prefix: str, patterns: list[str]) -> None:
        """Add an extension rule to the pipeline."""
        self.extend_rules.append(ExtendRule(prefix, patterns))

    def run(self) -> None:
        """Execute the pipeline: rules first, then tokenization."""
        self._ensure_nltk()
        self.text = self.text.lower()
        
        # 1. Apply replacement rules
        for rule in self.replace_rules:
            for pattern in rule.patterns:
                self.text = re.sub(pattern, rule.target, self.text)
        
        # 2. Apply extension rules (prepending prefix)
        for ext_rule in self.extend_rules:
            for pattern in ext_rule.patterns:
                # We use \g<0> to reference the matched text and prepend the prefix
                # Using re.IGNORECASE to be robust
                self.text = re.sub(pattern, rf"{ext_rule.prefix}\g<0>", self.text, flags=re.IGNORECASE)

        # 3. Tokenize
        # Using word_tokenize for basic punctuation-aware splitting
        self.tokens = nltk.word_tokenize(self.text)
