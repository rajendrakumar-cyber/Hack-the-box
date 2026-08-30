# HTB Coding Challenge — "Ash Record" (Crownspire) — Writeup

**Category:** Coding / Dynamic Programming / Sequence Matching
**Flag:** `HTB{th3_h4ml3t_w4s_k3pt_n0t_burn3d}`

---

## Summary

We are given:
- $N$ recovered residues, each with a timestamp and a material type.
- A suspected extraction sequence of material types of length $P$.
- A minimum time difference `min_gap` required between any two consecutively matched steps.

We need to find the longest prefix of the suspected extraction sequence that can be confirmed by a subsequence of residues that satisfies the time gap constraint.

---

## Solution Design

1. **Preprocessing:** Sort all residues by their timestamp in ascending order.
2. **Dynamic Programming:**
   Let $dp[j]$ be the minimum timestamp at which the prefix of length $j$ ($0 \le j \le P$) of the suspected extraction sequence can be completed.
   - **Base cases:** $dp[0] = -\infty$ (representing 0 steps matched at a very early time) and $dp[1 \dots P] = \infty$.
   - **Transition:** For each sorted residue $(timestamp, material)$, we iterate through the extraction sequence indices backwards $j = P$ down to $1$.
     If the residue's material matches the expected material at step $j$ (which is $S[j - 1]$):
     If the time difference between the current timestamp and the minimum timestamp of the previous step is at least the gap, i.e., $timestamp - dp[j - 1] \ge min\_gap$:
     We can transition and update $dp[j] = \min(dp[j], timestamp)$.
3. **Backward Iteration:** Going from $j = P$ down to $1$ ensures we do not reuse the exact same residue multiple times to satisfy consecutive steps in a single transition sequence.
4. **Result:** The answer is the largest $j$ such that $dp[j] \ne \infty$.

---

## Code Implementation

### Python
```python
import sys

def main():
    tokens = sys.stdin.read().split()
    if not tokens:
        return
    iterator = iter(tokens)
    
    try:
        N = int(next(iterator))
        P = int(next(iterator))
        min_gap = int(next(iterator))
        
        # Suspected extraction sequence
        S = [next(iterator) for _ in range(P)]
        
        # Recovered residues
        residues = []
        for _ in range(N):
            timestamp = int(next(iterator))
            material = next(iterator)
            residues.append((timestamp, material))
            
        # Sort residues by timestamp
        residues.sort(key=lambda x: x[0])
        
        INF = float('inf')
        dp = [INF] * (P + 1)
        dp[0] = -1000000000  # A very small number to satisfy timestamp - dp[0] >= min_gap
        
        for t, m in residues:
            # We must iterate backwards to prevent using the same residue multiple times
            for j in range(P, 0, -1):
                if m == S[j - 1]:
                    if t - dp[j - 1] >= min_gap:
                        if t < dp[j]:
                            dp[j] = t
                            
        # Find the maximum prefix confirmed
        ans = 0
        for j in range(1, P + 1):
            if dp[j] != INF:
                ans = j
            else:
                break
                
        print(ans)
    except StopIteration:
        pass

if __name__ == '__main__':
    main()
```

### C
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>

#define INF 1000000000

struct Residue {
    int timestamp;
    char material[15];
};

struct Residue residues[5005];
char S[15][15];
int dp[15];

int compare_residues(const void *a, const void *b) {
    return (((struct Residue*)a)->timestamp - ((struct Residue*)b)->timestamp);
}

int main() {
    int N, P, min_gap;
    if (scanf("%d %d %d", &N, &P, &min_gap) != 3) return 0;
    
    for (int i = 0; i < P; i++) {
        if (scanf("%10s", S[i]) != 1) return 0;
    }
    
    for (int i = 0; i < N; i++) {
        if (scanf("%d %10s", &residues[i].timestamp, residues[i].material) != 2) return 0;
    }
    
    qsort(residues, N, sizeof(struct Residue), compare_residues);
    
    dp[0] = -1000000000;
    for (int j = 1; j <= P; j++) {
        dp[j] = INF;
    }
    
    for (int i = 0; i < N; i++) {
        int t = residues[i].timestamp;
        char *m = residues[i].material;
        
        for (int j = P; j >= 1; j--) {
            if (strcmp(m, S[j - 1]) == 0) {
                if (t - dp[j - 1] >= min_gap) {
                    if (t < dp[j]) {
                        dp[j] = t;
                    }
                }
            }
        }
    }
    
    int ans = 0;
    for (int j = 1; j <= P; j++) {
        if (dp[j] != INF) {
            ans = j;
        } else {
            break;
        }
    }
    
    printf("%d\n", ans);
    return 0;
}
```
