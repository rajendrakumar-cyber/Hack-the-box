# HTB Coding Challenge — "Rumour Spine" (Crownspire) — Writeup

**Category:** Coding / Graph / Max-Flow Min-Cut / Minimum Node Cut
**Flag:** `HTB{0n3_c00rd1n4t3d_m0m3nt}`

---

## Summary

We are given:
- A directed graph of $N$ nodes (quiet hands) and $E$ edges.
- A coordinator node $S$ and a target district node $T$.

We need to find the minimum number of intermediate nodes (nodes other than $S$ and $T$) to remove/expose in order to disconnect all paths from $S$ to $T$.

---

## Solution Design

This is the classic **Minimum Node Cut** (vertex-cut) problem, which we solve by converting it to a **Maximum Flow** (Minimum Edge Cut) problem via node-splitting:

1. **Node Splitting:** Split every node $u$ in the original graph into two nodes in the flow network: $u_{in}$ (index $u$) and $u_{out}$ (index $u + N$).
2. **Capacities:**
   - For $u = S$ and $u = T$: We cannot cut/remove these nodes, so the capacity of $S_{in} \to S_{out}$ and $T_{in} \to T_{out}$ is set to $\infty$.
   - For all other nodes $u \notin \{S, T\}$: The capacity of $u_{in} \to u_{out}$ is set to `1` (cost of exposing/removing $u$ is 1).
3. **Edges:** For each original directed edge $u \to v$, add a directed edge $u_{out} \to v_{in}$ with capacity $\infty$ in the flow network.
4. **Max Flow Computation:** Run Edmonds-Karp (or another Max-Flow algorithm) from source $S_{in}$ (index $S$) to sink $T_{out}$ (index $T + N$). The max flow value equals the capacity of the minimum cut, which corresponds to the minimum number of nodes to remove.

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
        E = int(next(iterator))
        S = int(next(iterator))
        T = int(next(iterator))
        
        n_vertices = 2 * N
        INF = 1000000000
        
        capacity = [[0] * n_vertices for _ in range(n_vertices)]
        
        # Add internal node-split edges
        for u in range(N):
            if u == S or u == T:
                capacity[u][u + N] = INF
            else:
                capacity[u][u + N] = 1
                
        # Add original directed edges: u_out -> v_in
        for _ in range(E):
            u = int(next(iterator))
            v = int(next(iterator))
            capacity[u + N][v] = INF
            
        src_node = S
        sink_node = T + N
        
        # Edmonds-Karp Max-Flow
        flow = 0
        parent = [-1] * n_vertices
        
        def bfs():
            visited = [False] * n_vertices
            queue = deque([src_node])
            visited[src_node] = True
            parent[src_node] = -1
            while queue:
                u = queue.popleft()
                for v in range(n_vertices):
                    if not visited[v] and capacity[u][v] > 0:
                        visited[v] = True
                        parent[v] = u
                        if v == sink_node:
                            return True
                        queue.append(v)
            return False
            
        while bfs():
            path_flow = INF
            s = sink_node
            while s != src_node:
                path_flow = min(path_flow, capacity[parent[s]][s])
                s = parent[s]
                
            v = sink_node
            while v != src_node:
                u = parent[v]
                capacity[u][v] -= path_flow
                capacity[v][u] += path_flow
                v = parent[v]
                
            flow += path_flow
            
        print(flow)
    except StopIteration:
        pass

if __name__ == '__main__':
    main()
```

### C
```c
#include <stdio.		h>
#include <stdlib.		h>
#include <string.		h>

#define INF 1000000000

int capacity[245][245];
int parent[245];
int visited[245];
int queue[245];

int bfs(int src, int sink, int n_vertices) {
    memset(visited, 0, sizeof(visited));
    int head = 0, tail = 0;
    queue[tail++] = src;
    visited[src] = 1;
    parent[src] = -1;
    
    while (head < tail) {
        int u = queue[head++];
        for (int v = 0; v < n_vertices; v++) {
            if (!visited[v] && capacity[u][v] > 0) {
                visited[v] = 1;
                parent[v] = u;
                if (v == sink) {
                    return 1;
                }
                queue[tail++] = v;
            }
        }
    }
    return 0;
}

int main() {
    int N, E, S, T;
    if (scanf("%d %d %d %d", &N, &E, &S, &T) != 4) return 0;
    
    int n_vertices = 2 * N;
    
    // Internal capacities for all nodes
    for (int u = 0; u < N; u++) {
        if (u == S || u == T) {
            capacity[u][u + N] = INF;
        } else {
            capacity[u][u + N] = 1;
        }
    }
    
    // Read edges: u_out -> v_in
    for (int i = 0; i < E; i++) {
        int u, v;
        if (scanf("%d %d", &u, &v) != 2) return 0;
        capacity[u + N][v] = INF;
    }
    
    int src_node = S;
    int sink_node = T + N;
    
    int flow = 0;
    while (bfs(src_node, sink_node, n_vertices)) {
        int path_flow = INF;
        int s = sink_node;
        while (s != src_node) {
            int p = parent[s];
            if (capacity[p][s] < path_flow) {
                path_flow = capacity[p][s];
            }
            s = p;
        }
        
        int v = sink_node;
        while (v != src_node) {
            int u = parent[v];
            capacity[u][v] -= path_flow;
            capacity[v][u] += path_flow;
            v = u;
        }
        
        flow += path_flow;
    }
    
    printf("%d\n", flow);
    return 0;
}
```
