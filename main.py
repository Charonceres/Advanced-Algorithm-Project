"""
CloudMesh - Enterprise Network & Resource Optimization Platform
Backend: Python FastAPI
Algorithms: 0/1 Knapsack (B&B), Ford-Fulkerson, Bipartite Matching, Vertex Cover, Miller-Rabin
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import random, math, time

app = FastAPI(title="CloudMesh API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ════════════════════════════════════════════════════════════
# UNIT 1 — 0/1 KNAPSACK via Branch & Bound
# Server Resource Allocation
# ════════════════════════════════════════════════════════════

class Application(BaseModel):
    id: str
    name: str
    cpu: float        # CPU cores required
    ram: float        # RAM in GB
    priority: float   # Business priority score

class KnapsackRequest(BaseModel):
    applications: List[Application]
    server_cpu: float
    server_ram: float

def knapsack_branch_bound(items, cpu_cap, ram_cap):
    """
    Branch & Bound for 0/1 Knapsack.
    Sorts items by priority/(cpu+ram) ratio, then uses DFS with upper-bound pruning.
    """
    n = len(items)
    if n == 0:
        return 0, []

    # Sort by value-to-weight ratio for better bounding
    indexed = sorted(
        enumerate(items),
        key=lambda x: x[1]['priority'] / max(x[1]['cpu'] + x[1]['ram'], 0.001),
        reverse=True
    )

    best_value = [0]
    best_selection = [[]]
    steps = []

    def upper_bound(level, cur_val, cur_cpu, cur_ram):
        """Fractional knapsack upper bound"""
        if cur_cpu > cpu_cap or cur_ram > ram_cap:
            return 0
        val = cur_val
        rc, rr = cpu_cap - cur_cpu, ram_cap - cur_ram
        for i in range(level, n):
            _, item = indexed[i]
            if item['cpu'] <= rc and item['ram'] <= rr:
                val += item['priority']
                rc -= item['cpu']
                rr -= item['ram']
            else:
                frac = min(rc / max(item['cpu'], 0.001), rr / max(item['ram'], 0.001))
                val += frac * item['priority']
                break
        return val

    def solve(level, cur_val, cur_cpu, cur_ram, selection):
        if level == n or len(steps) > 500:
            if cur_val > best_value[0]:
                best_value[0] = cur_val
                best_selection[0] = selection[:]
            return

        orig_idx, item = indexed[level]
        steps.append({
            "level": level,
            "item": item['name'],
            "current_value": round(cur_val, 2),
            "pruned": False
        })

        # Branch: INCLUDE
        if cur_cpu + item['cpu'] <= cpu_cap and cur_ram + item['ram'] <= ram_cap:
            selection.append(orig_idx)
            solve(level + 1, cur_val + item['priority'],
                  cur_cpu + item['cpu'], cur_ram + item['ram'], selection)
            selection.pop()

        # Branch: EXCLUDE (prune if bound not promising)
        if upper_bound(level + 1, cur_val, cur_cpu, cur_ram) > best_value[0]:
            solve(level + 1, cur_val, cur_cpu, cur_ram, selection)
        else:
            steps[-1]["pruned"] = True

    solve(0, 0, 0, 0, [])
    return best_value[0], best_selection[0], steps[:50]  # Return first 50 steps

@app.post("/api/allocate")
def allocate_resources(req: KnapsackRequest):
    items = [
        {'id': a.id, 'name': a.name, 'cpu': a.cpu, 'ram': a.ram, 'priority': a.priority}
        for a in req.applications
    ]
    best_val, selected_idx, steps = knapsack_branch_bound(items, req.server_cpu, req.server_ram)
    selected = [req.applications[i] for i in selected_idx]
    rejected = [req.applications[i] for i in range(len(req.applications)) if i not in selected_idx]

    total_cpu = sum(a.cpu for a in selected)
    total_ram = sum(a.ram for a in selected)

    return {
        "selected_applications": [a.dict() for a in selected],
        "rejected_applications": [a.dict() for a in rejected],
        "total_priority": round(best_val, 2),
        "cpu_used": round(total_cpu, 2),
        "ram_used": round(total_ram, 2),
        "cpu_utilization": round(total_cpu / req.server_cpu * 100, 1),
        "ram_utilization": round(total_ram / req.server_ram * 100, 1),
        "branch_bound_steps": steps
    }


# ════════════════════════════════════════════════════════════
# UNIT 2A — FORD-FULKERSON (BFS / Edmonds-Karp)
# Maximum Bandwidth Routing
# ════════════════════════════════════════════════════════════

class FlowEdge(BaseModel):
    source: str
    target: str
    capacity: float

class FlowRequest(BaseModel):
    nodes: List[str]
    edges: List[FlowEdge]
    source: str
    sink: str

def ford_fulkerson_bfs(nodes, edges, source, sink):
    node_idx = {n: i for i, n in enumerate(nodes)}
    n = len(nodes)
    cap = [[0.0] * n for _ in range(n)]
    for e in edges:
        u, v = node_idx[e['source']], node_idx[e['target']]
        cap[u][v] += e['capacity']

    src, snk = node_idx[source], node_idx[sink]
    max_flow = 0
    flow_paths = []

    def bfs(parent):
        visited = [False] * n
        visited[src] = True
        queue = [src]
        while queue:
            u = queue.pop(0)
            for v in range(n):
                if not visited[v] and cap[u][v] > 0:
                    visited[v] = True
                    parent[v] = u
                    if v == snk:
                        return True
                    queue.append(v)
        return False

    iteration = 0
    while True:
        parent = [-1] * n
        if not bfs(parent):
            break
        # Trace path
        path_flow = float('inf')
        path_nodes = []
        v = snk
        while v != src:
            u = parent[v]
            path_flow = min(path_flow, cap[u][v])
            path_nodes.append(nodes[v])
            v = u
        path_nodes.append(nodes[src])
        path_nodes.reverse()

        # Update capacities
        v = snk
        while v != src:
            u = parent[v]
            cap[u][v] -= path_flow
            cap[v][u] += path_flow
            v = u

        max_flow += path_flow
        iteration += 1
        flow_paths.append({
            "iteration": iteration,
            "path": path_nodes,
            "flow": round(path_flow, 2),
            "cumulative_flow": round(max_flow, 2)
        })

    # Build final edge flows
    edge_flows = []
    for e in edges:
        u, v = node_idx[e['source']], node_idx[e['target']]
        used = e['capacity'] - cap[u][v]
        if used > 0:
            edge_flows.append({
                "source": e['source'],
                "target": e['target'],
                "capacity": e['capacity'],
                "flow": round(used, 2),
                "utilization": round(used / e['capacity'] * 100, 1)
            })

    return round(max_flow, 2), flow_paths, edge_flows

@app.post("/api/max-flow")
def calculate_max_flow(req: FlowRequest):
    max_flow, paths, edge_flows = ford_fulkerson_bfs(
        req.nodes,
        [{"source": e.source, "target": e.target, "capacity": e.capacity} for e in req.edges],
        req.source, req.sink
    )
    return {
        "max_flow": max_flow,
        "augmenting_paths": paths,
        "edge_flows": edge_flows,
        "total_iterations": len(paths)
    }


# ════════════════════════════════════════════════════════════
# UNIT 2B — BIPARTITE MATCHING (Hopcroft-Karp style via DFS)
# Client-to-Server Load Balancing
# ════════════════════════════════════════════════════════════

class BipartiteEdge(BaseModel):
    client: str
    server: str
    latency: float = 0.0

class BipartiteRequest(BaseModel):
    clients: List[str]
    servers: List[str]
    edges: List[BipartiteEdge]

def hopcroft_karp_dfs(clients, servers, edges):
    adj = {c: [] for c in clients}
    for e in edges:
        adj[e['client']].append(e['server'])

    match_server: Dict[str, Optional[str]] = {}
    match_client: Dict[str, Optional[str]] = {}

    def try_augment(client, visited):
        for server in adj[client]:
            if server not in visited:
                visited.add(server)
                if server not in match_server or try_augment(match_server[server], visited):
                    match_server[server] = client
                    match_client[client] = server
                    return True
        return False

    total = 0
    augment_log = []
    for client in clients:
        if try_augment(client, set()):
            total += 1
            augment_log.append({
                "client": client,
                "assigned_server": match_client.get(client),
                "status": "matched"
            })
        else:
            augment_log.append({
                "client": client,
                "assigned_server": None,
                "status": "unmatched"
            })

    unmatched_servers = [s for s in servers if s not in match_server]

    return total, match_client, augment_log, unmatched_servers

@app.post("/api/match-servers")
def match_servers(req: BipartiteRequest):
    count, matching, log, unmatched = hopcroft_karp_dfs(req.clients, req.servers, req.edges)
    return {
        "matched_count": count,
        "total_clients": len(req.clients),
        "total_servers": len(req.servers),
        "matching_efficiency": round(count / len(req.clients) * 100, 1) if req.clients else 0,
        "assignments": [{"client": c, "server": s} for c, s in matching.items()],
        "unmatched_servers": unmatched,
        "augmentation_log": log
    }


# ════════════════════════════════════════════════════════════
# UNIT 3 — VERTEX COVER (2-Approximation)
# Firewall / Security Node Placement
# ════════════════════════════════════════════════════════════

class NetworkGraphRequest(BaseModel):
    nodes: List[str]
    edges: List[Dict]  # [{u, v}]

def vertex_cover_2approx(nodes, edges):
    """
    2-Approximation: repeatedly pick an uncovered edge (u,v),
    add both u and v to cover, remove all edges incident to u or v.
    Guarantees cover size ≤ 2 × OPT.
    """
    cover = set()
    remaining = [(e['u'], e['v']) for e in edges]
    steps = []
    iteration = 0

    while remaining:
        u, v = remaining.pop(0)
        cover.add(u)
        cover.add(v)
        iteration += 1
        steps.append({
            "iteration": iteration,
            "chosen_edge": [u, v],
            "added_to_cover": [u, v],
            "cover_so_far": list(cover)
        })
        remaining = [(a, b) for a, b in remaining if a not in cover and b not in cover]

    # Verify all edges are covered
    all_covered = all(e['u'] in cover or e['v'] in cover for e in edges)

    return list(cover), steps, all_covered

@app.post("/api/vertex-cover")
def find_vertex_cover(req: NetworkGraphRequest):
    edges = [e if isinstance(e, dict) else e.dict() for e in req.edges]
    cover, steps, verified = vertex_cover_2approx(req.nodes, edges)

    total_edges = len(edges)
    monitored = sum(1 for e in edges if e['u'] in cover or e['v'] in cover)
    unprotected_nodes = [n for n in req.nodes if n not in cover]

    return {
        "vertex_cover": cover,
        "cover_size": len(cover),
        "total_nodes": len(req.nodes),
        "total_edges": total_edges,
        "monitored_edges": monitored,
        "coverage_ratio": round(monitored / total_edges * 100, 1) if total_edges else 100,
        "unmonitored_nodes": unprotected_nodes,
        "all_edges_covered": verified,
        "approximation_bound": f"≤ {2 * len(cover)} (2-approx guarantee)",
        "algorithm_steps": steps
    }


# ════════════════════════════════════════════════════════════
# UNIT 4 — MILLER-RABIN PRIMALITY TEST
# RSA Key Generation for TLS Certificates
# ════════════════════════════════════════════════════════════

def miller_rabin_test(n: int, k: int = 20) -> tuple[bool, list]:
    """
    Miller-Rabin Monte Carlo primality test.
    Returns (is_prime, list_of_witnesses_used)
    """
    if n < 2: return False, []
    if n in (2, 3): return True, [2]
    if n % 2 == 0: return False, []

    # Write n-1 as 2^r * d
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2

    witnesses_used = []
    for _ in range(k):
        a = random.randrange(2, n - 1)
        witnesses_used.append(a)
        x = pow(a, d, n)  # Fast modular exponentiation
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False, witnesses_used  # Composite

    # Probability of false positive ≤ 4^(-k)
    return True, witnesses_used

def generate_large_prime(bits: int) -> tuple[int, int]:
    """Generate a random prime of given bit length, return (prime, attempts)"""
    attempts = 0
    while True:
        attempts += 1
        candidate = random.getrandbits(bits)
        candidate |= (1 << (bits - 1))  # Ensure correct bit length
        candidate |= 1                   # Ensure odd
        is_prime, _ = miller_rabin_test(candidate, 20)
        if is_prime:
            return candidate, attempts

def extended_gcd(a: int, b: int):
    if a == 0:
        return b, 0, 1
    g, x, y = extended_gcd(b % a, a)
    return g, y - (b // a) * x, x

class KeyGenRequest(BaseModel):
    key_size: int = 256  # bits — keep small for demo speed

@app.post("/api/generate-keys")
def generate_rsa_keys(req: KeyGenRequest):
    bits = max(64, min(req.key_size, 512))
    half = bits // 2

    start = time.time()

    p, p_attempts = generate_large_prime(half)
    q, q_attempts = generate_large_prime(half)
    while q == p:
        q, q_attempts = generate_large_prime(half)

    n = p * q
    phi_n = (p - 1) * (q - 1)

    e = 65537  # Standard public exponent
    _, d, _ = extended_gcd(e % phi_n, phi_n)
    d = d % phi_n

    elapsed = time.time() - start

    # Verify: e*d ≡ 1 (mod φ(n))
    verified = (e * d) % phi_n == 1

    # Miller-Rabin verification details
    _, p_witnesses = miller_rabin_test(p, 20)
    _, q_witnesses = miller_rabin_test(q, 20)

    false_positive_prob = 4 ** (-20)  # Per round

    return {
        "p": str(p),
        "q": str(q),
        "n": str(n),
        "phi_n": str(phi_n),
        "e": e,
        "d": str(d),
        "key_size_bits": bits,
        "generation_time_ms": round(elapsed * 1000, 2),
        "p_generation_attempts": p_attempts,
        "q_generation_attempts": q_attempts,
        "key_verified": verified,
        "p_miller_rabin_rounds": 20,
        "q_miller_rabin_rounds": 20,
        "false_positive_probability": f"≤ 4^(-20) ≈ {false_positive_prob:.2e}",
        "public_key_preview": f"({e}, {str(n)[:30]}...)",
        "private_key_preview": f"({str(d)[:30]}..., {str(n)[:30]}...)"
    }


# ════════════════════════════════════════════════════════════
# HEALTH & ROOT
# ════════════════════════════════════════════════════════════

@app.get("/")
def root():
    return {"status": "CloudMesh API online", "version": "1.0.0", "algorithms": [
        "0/1 Knapsack (Branch & Bound)",
        "Ford-Fulkerson (Edmonds-Karp BFS)",
        "Bipartite Matching (Hopcroft-Karp DFS)",
        "Vertex Cover (2-Approximation)",
        "Miller-Rabin Primality Test"
    ]}

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": time.time()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
