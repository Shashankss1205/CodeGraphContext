from collections import Counter
from typing import List

class Solution:
    def minimumDeletions(self, word: str, k: int) -> int:
        # frequency of each lowercase letter
        cnt = Counter(word)
        freqs = [cnt[ch] for ch in cnt]  # only non-zero frequencies
        if not freqs:
            return 0

        max_freq = max(freqs)
        ans = float('inf')

        # Try each possible minimum frequency v (0..max_freq)
        for v in range(0, max_freq + 1):
            deletions = 0
            upper = v + k
            for f in freqs:
                if f < v:
                    # must delete entire character (f deletions)
                    deletions += f
                elif f > upper:
                    # reduce down to upper (f - upper deletions)
                    deletions += f - upper
            ans = min(ans, deletions)

        return ans
