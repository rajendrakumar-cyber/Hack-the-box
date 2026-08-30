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
                # Run BFS for this component
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
                
            # Check if there exists x_u in Reach(u) such that (x_u ^ T) in Reach(v)
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
