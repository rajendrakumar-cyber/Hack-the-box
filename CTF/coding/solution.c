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
