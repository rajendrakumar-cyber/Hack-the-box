# HTB Coding Challenge — "Toll Schedule" (Crownspire) — Writeup

**Category:** Coding / Dynamic Programming
**Flag:** `HTB{th3_p4ss_pr3f3rs_0n3_b4nn3r}`

---

## Summary

We are given:
- $N$ convoys, each with a specific arrival time.
- $G$ checkpoint clearances ($G \ge N$), each with an opening time.

We need to assign each convoy to a distinct clearance such that:
1. The clearance opening time is $\ge$ the convoy's arrival time.
2. The total waiting time (clearance opening time minus convoy arrival time) across all convoys is minimized.

---

## Solution Design

1. **Ordering Property:** If we sort both the convoy arrival times $A_1 \le A_2 \le \dots \le A_N$ and the clearance opening times $C_1 \le C_2 \le \dots \le C_G$, any optimal matching preserves their relative order. That is, if convoy $i$ matches clearance $j$, convoy $i+1$ will match some clearance $k > j$.
2. **Dynamic Programming:**
   Let $dp[i][j]$ represent the minimum total wait time to assign the first $i$ sorted convoys using a subset of the first $j$ sorted clearances.
   - **Option 1:** Skip clearance $j$: cost is $dp[i][j-1]$.
   - **Option 2:** Match convoy $i$ with clearance $j$ (valid if $C_j \ge A_i$): cost is $dp[i-1][j-1] + (C_j - A_i)$.
   
   The recurrence relation is:
   $$dp[i][j] = \min(dp[i][j-1], dp[i-1][j-1] + C_j - A_i \quad (\text{if } C_j \ge A_i))$$
3. **Space Optimization:** Since $dp[i][j]$ only depends on the current row $i$ and the previous row $i-1$, we can optimize the space complexity from $O(N \cdot G)$ to $O(G)$ by maintaining only two rows of size $G+1$.

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
        G = int(next(iterator))
        
        A = [int(next(iterator)) for _ in range(N)]
        C = [int(next(iterator)) for _ in range(G)]
        
        A.sort()
        C.sort()
        
        INF = float('inf')
        dp = [0] * (G + 1)
        
        for i in range(1, N + 1):
            next_dp = [INF] * (G + 1)
            curr_a = A[i - 1]
            for j in range(i, G + 1):
                val = next_dp[j - 1]
                curr_c = C[j - 1]
                if curr_c >= curr_a:
                    match_val = dp[j - 1] + (curr_c - curr_a)
                    if match_val < val:
                        val = match_val
                next_dp[j] = val
            dp = next_dp
            
        print(dp[G])
    except StopIteration:
        pass

if __name__ == '__main__':
    main()
```

### C
```c
#include <stdio.h>
#include <stdlib.h>
#include <limits.h>

#define INF (INT_MAX / 2)

int A[1205];
int C[1505];
int dp[1505];
int next_dp[1505];

int compare_ints(const void *a, const void *b) {
    return (*(int*)a - *(int*)b);
}

int main() {
    int N, G;
    if (scanf("%d %d", &N, &G) != 2) return 0;
    
    for (int i = 0; i < N; i++) {
        if (scanf("%d", &A[i]) != 1) return 0;
    }
    for (int i = 0; i < G; i++) {
        if (scanf("%d", &C[i]) != 1) return 0;
    }
    
    qsort(A, N, sizeof(int), compare_ints);
    qsort(C, G, sizeof(int), compare_ints);
    
    for (int j = 0; j <= G; j++) {
        dp[j] = 0;
    }
    
    for (int i = 1; i <= N; i++) {
        for (int j = 0; j <= G; j++) {
            next_dp[j] = INF;
        }
        int curr_a = A[i - 1];
        for (int j = i; j <= G; j++) {
            int val = next_dp[j - 1];
            int curr_c = C[j - 1];
            if (curr_c >= curr_a) {
                int match_val = dp[j - 1] + (curr_c - curr_a);
                if (match_val < val) {
                    val = match_val;
                }
            }
            next_dp[j] = val;
        }
        for (int j = 0; j <= G; j++) {
            dp[j] = next_dp[j];
        }
    }
    
    printf("%d\n", dp[G]);
    return 0;
}
```
