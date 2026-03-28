"""
Enterprise Text Normalizer — Anti-Evasion Layer
Catches adversarial obfuscation like:
  - Leet speak: f@ck, sh!t, b1tch
  - Misspellings: bitvh, fvck, a$$hole
  - Character insertion: f.u.c.k, b-i-t-c-h
  - Repetition: fuuuuck, shiiit
  - Unicode homoglyphs: Cyrillic а, е, о → Latin a, e, o
  - Letter transpositions: fcuk, siht, btich, fcking
"""

import re
import unicodedata
from itertools import permutations

# ═══════════════════════════════════════════
# LEET SPEAK / SYMBOL → LETTER MAPPINGS
# ═══════════════════════════════════════════
CHAR_MAP = {
    '@': 'a', '4': 'a', '^': 'a',
    '8': 'b',
    '(': 'c', '<': 'c', '{': 'c',
    '3': 'e', '€': 'e',
    '6': 'g', '9': 'g',
    '#': 'h',
    '!': 'i', '1': 'i', '|': 'i',
    '7': 't', '+': 't',
    '0': 'o',
    '5': 's', '$': 's',
    'v': 'v',
    '2': 'z',
    '*': '',   # wildcard used to mask letters
}

# ═══════════════════════════════════════════
# COMMON OBFUSCATED SLUR PATTERNS
# Each tuple: (regex pattern, canonical replacement)
# ═══════════════════════════════════════════
SLUR_PATTERNS = [
    # F-word variants
    (r'\bf+[\W_]*[uv]+[\W_]*[ck]+[\W_]*[ckieyng]*\b', 'fuck'),
    (r'\bf+[\W_]*[a@4]+[\W_]*[gq]+[\W_]*[gq]*[\W_]*[oeiy]*[t]*\b', 'faggot'),
    # S-word variants
    (r'\bs+[\W_]*h+[\W_]*[i!1]+[\W_]*t+\b', 'shit'),
    # B-word variants (the exact case from the screenshot)
    (r'\bb+[\W_]*[i!1]+[\W_]*t+[\W_]*[c(]+[\W_]*h+\b', 'bitch'),
    (r'\bb+[\W_]*[i!1]+[\W_]*t+[\W_]*v+[\W_]*h*\b', 'bitch'),     # bitvh
    # A-word variants
    (r'\b[a@4]+[\W_]*[s$5]+[\W_]*[s$5]+[\W_]*h+[\W_]*[o0]+[\W_]*l+[\W_]*[e3]*\b', 'asshole'),
    # N-word variants (critical to catch)
    (r'\bn+[\W_]*[i!1]+[\W_]*[gq9]+[\W_]*[gq9]+[\W_]*[e3a@]+[\W_]*[r]*\b', 'nigger'),
    # D-word variants
    (r'\bd+[\W_]*[i!1]+[\W_]*[ck]+[\W_]*[ck]*\b', 'dick'),
    # R-word variants
    (r'\br+[\W_]*[e3]+[\W_]*t+[\W_]*[a@4]+[\W_]*r+[\W_]*d+\b', 'retard'),
    # C-word variants
    (r'\bc+[\W_]*[u]+[\W_]*n+[\W_]*t+\b', 'cunt'),
    # K-word / kill threats
    (r'\bk+[\W_]*[i!1]+[\W_]*l+[\W_]*l+\b', 'kill'),
    # D-word / die threats
    (r'\bd+[\W_]*[i!1]+[\W_]*[e3]+\b', 'die'),
    # Idiot variants
    (r'\b[i!1]+[\W_]*d+[\W_]*[i!1]+[\W_]*[o0]+[\W_]*t+\b', 'idiot'),
    # Stupid variants
    (r'\bs+[\W_]*t+[\W_]*[u]+[\W_]*p+[\W_]*[i!1]+[\W_]*d+\b', 'stupid'),
    # Whore variants
    (r'\bw+[\W_]*h+[\W_]*[o0]+[\W_]*r+[\W_]*[e3]+\b', 'whore'),
]

# ═══════════════════════════════════════════
# TRANSPOSITION / ANAGRAM DETECTION
# Maps: sorted letter signature → canonical toxic word
# Catches jumbled spellings like fcuk, siht, btich
# ═══════════════════════════════════════════
TOXIC_WORDS = [
    'fuck', 'shit', 'bitch', 'dick', 'cunt', 'cock',
    'damn', 'hell', 'slut', 'whore', 'ass', 'twat',
    'piss', 'crap', 'tits', 'nigg',
]

# Build sorted-letter → word mapping for anagram detection
# e.g. 'cfku' → 'fuck', 'hist' → 'shit'
ANAGRAM_MAP = {}
for word in TOXIC_WORDS:
    key = ''.join(sorted(word.lower()))
    ANAGRAM_MAP[key] = word

# Known transposition patterns that regex should catch explicitly
# These cover the most common letter-swap evasions with optional suffixes
TRANSPOSITION_PATTERNS = [
    # fcuk and variants (c and u swapped)
    (r'\bf+c+u+k+(?:e[dr]s?|i+n+g+|s)?\b', 'fuck'),
    (r'\bf+u+k+c+(?:e[dr]s?|i+n+g+|s)?\b', 'fuck'),
    (r'\bf+k+u+c+(?:e[dr]s?|i+n+g+|s)?\b', 'fuck'),
    (r'\bf+c+k+u*(?:e[dr]s?|i+n+g+|s)?\b', 'fuck'),
    # siht, stih, tihs (transposed shit)
    (r'\bs+i+h+t+(?:s|t+y)?\b', 'shit'),
    (r'\bs+t+i+h+\b', 'shit'),
    (r'\bh+s+i+t+\b', 'shit'),
    # btich, bithc, bcith (transposed bitch)
    (r'\bb+t+i+c+h+\b', 'bitch'),
    (r'\bb+i+t+h+c+\b', 'bitch'),
    (r'\bb+c+i+t+h+\b', 'bitch'),
    (r'\bb+i+h+t+c+\b', 'bitch'),
    # dcik, dik, dikc (transposed dick)
    (r'\bd+c+i+k+\b', 'dick'),
    (r'\bd+i+k+c+\b', 'dick'),
    # cutn, cntu (transposed cunt)
    (r'\bc+u+t+n+\b', 'cunt'),
    (r'\bc+n+t+u+\b', 'cunt'),
    (r'\bc+n+u+t+\b', 'cunt'),
    # assh0le / ahole transpositions
    (r'\ba+s+h+o+l+e*\b', 'asshole'),
]

# ═══════════════════════════════════════════
# UNICODE HOMOGLYPH → ASCII
# ═══════════════════════════════════════════
HOMOGLYPHS = {
    # Cyrillic lookalikes
    'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c',
    'у': 'y', 'х': 'x', 'В': 'B', 'Н': 'H', 'К': 'K',
    'М': 'M', 'Т': 'T', 'і': 'i',
    # Greek lookalikes
    'α': 'a', 'ε': 'e', 'ο': 'o', 'ι': 'i', 'κ': 'k',
    # Other common swaps
    'ℓ': 'l', '℮': 'e', 'ⅰ': 'i', 'ⅱ': 'ii',
}


class TextNormalizer:
    """Pre-processing layer to defeat adversarial text obfuscation."""

    def __init__(self):
        print("🔧 Initializing Anti-Evasion Text Normalizer...")
        # Pre-compile all regex patterns for performance
        self.compiled_patterns = [
            (re.compile(pat, re.IGNORECASE), repl)
            for pat, repl in SLUR_PATTERNS
        ]
        # Pre-compile transposition patterns
        self.compiled_transpositions = [
            (re.compile(pat, re.IGNORECASE), repl)
            for pat, repl in TRANSPOSITION_PATTERNS
        ]

    def normalize(self, text: str) -> str:
        """
        Normalize adversarial text to canonical form.
        This runs BEFORE the ML/LLM models see the text.
        
        Pipeline:
          1. Unicode normalization (homoglyphs → ASCII)
          2. Leet speak reversal (@ → a, ! → i, etc.)
          3. Strip inserted separators (f.u.c.k → fuck)
          4. Reduce character repetition (fuuuuck → fuck)
          5. Pattern-match known slur obfuscations
          6. Transposition/anagram detection (fcuk → fuck)
          7. Edit-distance fuzzy matching for short words
        """
        result = text

        # Step 1: Unicode normalization
        result = self._normalize_unicode(result)

        # Step 2: Homoglyph replacement
        result = self._replace_homoglyphs(result)

        # Step 3: Leet speak reversal
        result = self._reverse_leet(result)

        # Step 4: Strip separators between letters (f.u.c.k → fuck)
        result = self._strip_separators(result)

        # Step 5: Reduce repetition (fuuuuck → fuck, shiiiit → shit)
        result = self._reduce_repetition(result)

        # Step 6: Pattern-match known obfuscated slurs
        result = self._match_slur_patterns(result)

        # Step 7: Transposition pattern matching (fcuk, siht, btich)
        result = self._match_transposition_patterns(result)

        # Step 8: Anagram detection — sorted-letter signature
        result = self._detect_anagrams(result)

        # Step 9: Fuzzy edit-distance matching for short words
        result = self._fuzzy_match(result)

        return result

    def _normalize_unicode(self, text: str) -> str:
        """NFKD normalize — decomposes special unicode chars."""
        return unicodedata.normalize('NFKD', text)

    def _replace_homoglyphs(self, text: str) -> str:
        """Replace unicode lookalike characters with ASCII equivalents."""
        return ''.join(HOMOGLYPHS.get(c, c) for c in text)

    def _reverse_leet(self, text: str) -> str:
        """Replace common leet speak substitutions with letters."""
        result = []
        i = 0
        while i < len(text):
            ch = text[i]
            if ch in CHAR_MAP:
                # Only replace if it looks like it's being used as a letter
                # (surrounded by letters or at word boundary)
                prev_alpha = (i > 0 and (text[i-1].isalpha() or text[i-1] in CHAR_MAP))
                next_alpha = (i < len(text)-1 and (text[i+1].isalpha() or text[i+1] in CHAR_MAP))
                if prev_alpha or next_alpha:
                    result.append(CHAR_MAP[ch])
                else:
                    result.append(ch)
            else:
                result.append(ch)
            i += 1
        return ''.join(result)

    def _strip_separators(self, text: str) -> str:
        """Remove dots/dashes/spaces inserted between single chars: f.u.c.k → fuck."""
        # Match: letter, separator, letter, separator, letter... (3+ letters with seps)
        pattern = r'(?<!\w)([a-zA-Z])[\s.\-_,;:]+([a-zA-Z])[\s.\-_,;:]+([a-zA-Z](?:[\s.\-_,;:]+[a-zA-Z])*)'
        
        def join_chars(m):
            full = m.group(0)
            return re.sub(r'[\s.\-_,;:]+', '', full)
        
        return re.sub(pattern, join_chars, text)

    def _reduce_repetition(self, text: str) -> str:
        """Reduce character repetition: fuuuuck → fuuck, shiiiit → shiit."""
        # Allow max 2 consecutive same characters
        return re.sub(r'(.)\1{2,}', r'\1\1', text)

    def _match_slur_patterns(self, text: str) -> str:
        """Match known obfuscated slur patterns and replace with canonical form."""
        result = text
        for pattern, replacement in self.compiled_patterns:
            result = pattern.sub(replacement, result)
        return result

    def _match_transposition_patterns(self, text: str) -> str:
        """Match known letter-transposition patterns (fcuk, siht, btich)."""
        result = text
        for pattern, replacement in self.compiled_transpositions:
            result = pattern.sub(replacement, result)
        return result

    def _detect_anagrams(self, text: str) -> str:
        """
        Detect anagram evasions by comparing sorted letter signatures.
        e.g. 'fcuk' → sorted = 'cfku' → matches 'fuck' (sorted = 'cfku')
        Only applies to words 3-8 characters that are pure alphabetic.
        """
        words = text.split()
        result_words = []
        for word in words:
            clean = word.strip('.,!?;:\'"()[]{}').lower()
            if 3 <= len(clean) <= 8 and clean.isalpha():
                # Check if this word is already a known toxic word
                if clean in TOXIC_WORDS:
                    result_words.append(word)
                    continue
                sorted_key = ''.join(sorted(clean))
                if sorted_key in ANAGRAM_MAP:
                    canonical = ANAGRAM_MAP[sorted_key]
                    # Only replace if it's not already the canonical form
                    # and the word doesn't look like a legitimate word
                    if clean != canonical and not self._is_safe_word(clean):
                        result_words.append(canonical)
                        continue
            result_words.append(word)
        return ' '.join(result_words)

    def _is_safe_word(self, word: str) -> bool:
        """
        Check if a word is a known safe/legitimate English word
        that happens to be an anagram of a toxic word.
        This prevents false positives like 'this' being flagged.
        """
        SAFE_WORDS = {
            # Words that are anagrams of toxic words but are safe
            'this', 'hits', 'hist', 'hiss', 'tips', 'spit', 'pits',
            'snit', 'tins', 'unit', 'units', 'diet', 'edit', 'tide',
            'tied', 'side', 'dime', 'amid', 'maid', 'said', 'laid',
            'disc', 'kids', 'kiss', 'miss', 'skit', 'kits', 'sink',
            'skin', 'inks', 'link', 'silk', 'milk', 'risk', 'fish',
            'wish', 'dish', 'chip', 'chit', 'itch', 'rich', 'kick',
            'lick', 'nick', 'pick', 'sick', 'tick', 'wick', 'duck',
            'luck', 'much', 'such', 'tuck', 'cups', 'puns', 'spun',
            'stun', 'nuts', 'cuts', 'gust', 'must', 'rust', 'dust',
            'just', 'bust', 'snug', 'slug', 'plug', 'drug', 'thus',
            'shut', 'huts', 'tush', 'gush', 'push', 'bush', 'rush',
            'lush', 'mush', 'husk', 'dusk', 'task', 'mask', 'cast',
            'mast', 'last', 'past', 'fast', 'vast', 'salt', 'malt',
            'halt', 'cult', 'hull',
            # Common short words
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all',
            'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day',
            'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new',
            'now', 'old', 'see', 'way', 'who', 'did', 'let', 'say',
            'she', 'too', 'use',
        }
        return word.lower() in SAFE_WORDS

    def _fuzzy_match(self, text: str) -> str:
        """
        Damerau-Levenshtein distance check for short words.
        Catches near-miss misspellings with 1 edit (swap, insert, delete, substitute).
        e.g. 'fuk', 'fck', 'sht', 'btch'
        """
        words = text.split()
        result_words = []
        for word in words:
            clean = word.strip('.,!?;:\'"()[]{}').lower()
            if 3 <= len(clean) <= 8 and clean.isalpha():
                # Skip if already canonical
                if clean in TOXIC_WORDS:
                    result_words.append(word)
                    continue
                if self._is_safe_word(clean):
                    result_words.append(word)
                    continue
                # Check Damerau-Levenshtein distance against toxic words
                for toxic in TOXIC_WORDS:
                    dist = self._damerau_levenshtein(clean, toxic)
                    # Only replace if edit distance is 1 (very close match)
                    if dist == 1:
                        result_words.append(toxic)
                        break
                else:
                    result_words.append(word)
            else:
                result_words.append(word)
        return ' '.join(result_words)

    @staticmethod
    def _damerau_levenshtein(s1: str, s2: str) -> int:
        """Compute Damerau-Levenshtein distance (supports transpositions)."""
        len1, len2 = len(s1), len(s2)
        # Quick length-based rejection for performance
        if abs(len1 - len2) > 1:
            return abs(len1 - len2)
        d = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        for i in range(len1 + 1):
            d[i][0] = i
        for j in range(len2 + 1):
            d[0][j] = j
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                cost = 0 if s1[i-1] == s2[j-1] else 1
                d[i][j] = min(
                    d[i-1][j] + 1,        # deletion
                    d[i][j-1] + 1,        # insertion
                    d[i-1][j-1] + cost,   # substitution
                )
                # Transposition
                if i > 1 and j > 1 and s1[i-1] == s2[j-2] and s1[i-2] == s2[j-1]:
                    d[i][j] = min(d[i][j], d[i-2][j-2] + cost)
        return d[len1][len2]


# Singleton
text_normalizer = TextNormalizer()
