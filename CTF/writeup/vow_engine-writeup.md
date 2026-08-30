# HTB Coding Challenge — "Vow Engine" (Crownspire) — Writeup

**Category:** Coding / Graph / BFS State Space
**Flag:** `HTB{th3_b3ll_r1ngs_wr0ng_0n_purp0s3}`

---

## Summary

We are given:
- An undirected graph of $N$ witnesses and $M$ edges with weights $w$ representing cadence keys.
- $Q$ challenges, each querying if a specific target cadence value $T$ ($0 \le T \le 63$) is achievable on any path/walk between two given witnesses $u$ and $v$.

---

## Solution Design

1. **XOR Walk Properties:** 
   In an undirected graph, any walk between $u$ and $v$ can be represented as the combination of:
   - A walk from a reference root $R$ to $u$ with some XOR sum $x_u$.
   - A walk from $R$ to $v$ with some XOR sum $x_v$.
   
   The XOR sum of the combined walk is $x_u \oplus x_v$. Thus, $T$ is achievable between $u$ and $v$ if and only if $u$ and $v$ are in the same connected component, and there exist reachable state XOR sums $x_u$ and $x_v$ from $R$ such that $x_u \oplus x_v = T$.
2. **State Space size:** Since weights $w$ and query targets $T$ are bounded by $63$, the maximum reachable XOR sum is $63$. The number of reachable states for any node $u$ is at most $64$.
3. **BFS Exploration:** We run a BFS from an arbitrary starting node $R$ for each connected component. The state is $(u, x)$, where $u$ is the node and $x$ is the cumulative XOR sum from $R$. We transition from $(u, x)$ to $(v, x \oplus w)$ for all neighbors $v$ of weight $w$.
4. **Answering Queries:** For each query $(u, v, T)$:
   - Check if $u$ and $v$ share a component. If not, output `NO`.
   - Iterate through all possible $x_u \in [0, 63]$. If both $(u, x_u)$ and $(v, x_u \oplus T)$ are reachable, output `YES`. Otherwise, output `NO`.

---

## Code Implementation

### Python
```python
import sys
from collections import deque

def main():
    tokens = sys.stdin.read().split()
    if not tokens:
        return
    iterator = iter(tokens)
    
    try:
        N = int(next(iterator))
        M = int(next(iterator))
        Q = int(next(iterator))
        
        # Build adjacency list
        adj = [[] for _ in range(N)]
        for _ in range(M):
            u = int(next(iterator))
            v = int(next(iterator))
            w = int(next(iterator))
            adj[u].append((v, w))
            adj[v].append((u, w))
            
        # Component IDs and reachability arrays
        comp_id = [-1] * N
        reach = [[False] * 64 for _ in range(N)]
        
        current_comp = 0
        for start_node in range(N):
            if comp_id[start_node] == -1:
                queue = deque([(start_node, 0)])
                comp_id[start_node] = current_comp
                reach[start_node][0] = True
                
                while queue:
                    u, x = queue.popleft()
                    for v, w in adj[u]:
                        nx = x ^ w
                        if comp_id[v] == -1:
                            comp_id[v] = current_comp
                            reach[v][nx] = True
                            queue.append((v, nx))
                        elif not reach[v][nx]:
                            reach[v][nx] = True
                            queue.append((v, nx))
                current_comp += 1
                
        # Process queries
        for _ in range(Q):
            u = int(next(iterator))
            v = int(next(iterator))
            T = int(next(iterator))
            
            if comp_id[u] != comp_id[v]:
                print("NO")
                continue
                
            achievable = False
            for x_u in range(64):
                if reach[u][x_u]:
                    x_v = x_u ^ T
                    if reach[v][x_v]:
                        achievable = True
                        break
            if achievable:
                print("YES")
            else:
                print("NO")
                
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

#define MAXN 1505
#define MAXM 4405

int head[MAXN];
int to[MAXM];
int weight[MAXM];
int next_edge[MAXM];
int edge_cnt = 0;

void add_edge(int u, int v, int w) {
    to[edge_cnt] = v;
    weight[edge_cnt] = w;
    next_edge[edge_cnt] = head[u];
    head[u] = edge_cnt++;
}

int comp_id[MAXN];
char reach[MAXN][64];

typedef struct {
    int u;
    int x;
} State;

State queue[100005];
int q_head, q_tail;

int main() {
    int N, M, Q;
    if (scanf("%d %d %d", &N, &M, &Q) != 3) return 0;
    
    memset(head, -1, sizeof(head));
    for (int i = 0; i < M; i++) {
        int u, v, w;
        if (scanf("%d %d %d", &u, &v, &w) != 3) return 0;
        add_edge(u, v, w);
        add_edge(v, u, w);
    }
    
    memset(comp_id, -1, sizeof(comp_id));
    memset(reach, 0, sizeof(reach));
    
    int current_comp = 0;
    for (int start_node = 0; start_node < N; start_node++) {
        if (comp_id[start_node] == -1) {
            q_head = 0;
            q_tail = 0;
            
            queue[q_tail++] = (State){start_node, 0};
            comp_id[start_node] = current_comp;
            reach[start_node][0] = 1;
            
            while (q_head < q_tail) {
                State curr = queue[q_head++];
                int u = curr.u;
                int x = curr.x;
                
                for (int e = head[u]; e != -1; e = next_edge[e]) {
                    int v = to[e];
                    int w = weight[e];
                    int nx = x ^ w;
                    
                    if (comp_id[v] == -1) {
                        comp_id[v] = current_comp;
                        reach[v][nx] = 1;
                        queue[q_tail++] = (State){v, nx};
                    } else if (!reach[v][nx]) {
                        reach[v][nx] = 1;
                        queue[q_tail++] = (State){v, nx};
                    }
                }
            }
            current_comp++;
        }
    }
    
    for (int q = 0; q < Q; q++) {
        int u, v, T;
        if (scanf("%d %d %d", &u, &v, &T) != 3) return 0;
        
        if (comp_id[u] != comp_id[v]) {
            printf("NO\n");
            continue;
        }
        
        int achievable = 0;
        for (int x_u = 0; x_u < 64; x_u++) {
            if (reach[u][x_u]) {
                int x_v = x_u ^ T;
                if (reach[v][x_v]) {
                    achievable = 1;
                    break;
                }
            }
        }
        if (achievable) {
            printf("YES\n");
        } else {
            printf("NO\n");
        }
    }
    
    return 0;
}
```
