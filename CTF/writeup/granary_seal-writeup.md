# HTB Coding Challenge — "Granary Seal" (Crownspire) — Writeup

**Category:** Coding / Validation
**Flag:** `HTB{th3_0ld_s3qu3nc3_n3v3r_h3s1t4t3s}`

---

## Summary

The challenge requires us to validate a batch of transaction orders. Each order consists of three space-separated names representing: `clerk`, `countersigner`, and `courier`. 
We are given:
- A custody roll of valid clerks.
- A custody roll of valid countersigners.
- A custody roll of valid couriers.
- A list of $N$ orders.

An order "survives" if and only if all three people involved in the order appear on their respective custody rolls. The output should be the number of orders that survive.

---

## Solution Design

1. **Storage/Lookups:** To perform lookups in $O(1)$ constant time, we read each of the three custody rolls and store the names in hash sets: `clerks`, `countersigners`, and `couriers`.
2. **Order Verification:** We process the batch of orders one by one. For each order, we check if the `clerk` is in the `clerks` set, the `countersigner` is in the `countersigners` set, and the `courier` is in the `couriers` set. If all three exist, the order is valid, and we increment our counter.
3. **Robust Token-Based Parsing:** To ensure we don't run into issues with trailing/leading whitespaces or blank lines, we read standard input entirely and split by whitespace into a stream of tokens.

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
        # Read clerks custody roll
        C = int(next(iterator))
        clerks = set(next(iterator) for _ in range(C))
        
        # Read countersigners custody roll
        CS = int(next(iterator))
        countersigners = set(next(iterator) for _ in range(CS))
        
        # Read couriers custody roll
        R = int(next(iterator))
        couriers = set(next(iterator) for _ in range(R))
        
        # Validate orders
        N = int(next(iterator))
        valid_count = 0
        for _ in range(N):
            clerk = next(iterator)
            countersigner = next(iterator)
            courier = next(iterator)
            if clerk in clerks and countersigner in countersigners and courier in couriers:
                valid_count += 1
                
        print(valid_count)
    except StopIteration:
        pass

if __name__ == '__main__':
    main()
```

### C
```c
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

char clerks[25][35];
char countersigners[25][35];
char couriers[25][35];

int C, CS, R, N;

int is_in_list(char list[][35], int size, const char *name) {
    for (int i = 0; i < size; i++) {
        if (strcmp(list[i], name) == 0) {
            return 1;
        }
    }
    return 0;
}

int main() {
    if (scanf("%d", &C) != 1) return 0;
    for (int i = 0; i < C; i++) {
        if (scanf("%30s", clerks[i]) != 1) return 0;
    }
    
    if (scanf("%d", &CS) != 1) return 0;
    for (int i = 0; i < CS; i++) {
        if (scanf("%30s", countersigners[i]) != 1) return 0;
    }
    
    if (scanf("%d", &R) != 1) return 0;
    for (int i = 0; i < R; i++) {
        if (scanf("%30s", couriers[i]) != 1) return 0;
    }
    
    if (scanf("%d", &N) != 1) return 0;
    
    int valid_count = 0;
    for (int i = 0; i < N; i++) {
        char clerk[35], countersigner[35], courier[35];
        if (scanf("%30s %30s %30s", clerk, countersigner, courier) != 3) {
            break;
        }
        if (is_in_list(clerks, C, clerk) &&
            is_in_list(countersigners, CS, countersigner) &&
            is_in_list(couriers, R, courier)) {
            valid_count++;
        }
    }
    
    printf("%d\n", valid_count);
    return 0;
}
```
