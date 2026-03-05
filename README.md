# CloudMesh: Enterprise Network & Resource Optimization Platform

CloudMesh is a full-stack algorithmic simulation dashboard designed for enterprise IT administrators. It models a cloud infrastructure environment where routing, server allocation, load balancing, and network security are optimized using advanced algorithmic design techniques. 

This project was built to practically implement complex algorithms across dynamic programming, network flows, approximation algorithms, and randomized algorithms into a single, cohesive software architecture.

## 🚀 Features & Algorithmic Implementation

The core logic of the platform is divided into five distinct modules, each solving a real-world infrastructure problem using a specific algorithm:

* **Server Resource Allocation (Unit 1):** Uses the **0/1 Knapsack (Branch & Bound)** algorithm to pack the highest-priority microservices onto physical servers without exceeding CPU and RAM capacities. The Branch & Bound approach guarantees an optimal exact solution by pruning suboptimal decision trees.
* **Maximum Bandwidth Routing (Unit 2A):** Utilizes the **Ford-Fulkerson Algorithm (via Edmonds-Karp BFS)** to determine the maximum data throughput across a mesh of network routers, identifying exact flow limits and augmenting paths from western to eastern data centers.
* **Client-Server Load Balancing (Unit 2B):** Implements **Maximum Bipartite Matching (DFS Augmenting Path)** to optimally assign incoming client requests to available edge servers, ensuring maximum efficiency and 1:1 resource allocation.
* **Security Node Placement (Unit 3):** Uses a **2-Approximation Algorithm for Minimum Vertex Cover** to determine the absolute minimum number of servers that require firewall monitoring software so that every single network link is observed.
* **RSA Certificate Key Generation (Unit 4):** Applies the **Miller-Rabin Primality Test (Monte Carlo Randomized Algorithm)** to rapidly generate and verify massive prime numbers required for secure RSA encryption, running multiple rounds to reduce the false-positive probability to near zero.

## 🛠 Tech Stack

* **Backend:** Python, FastAPI, Uvicorn, Pydantic
* **Frontend:** Vanilla HTML5, CSS3, JavaScript (No external framework dependencies)
* **Architecture:** RESTful API client-server model
* **UI Design:** Clean corporate neutral theme with native Light/Dark mode toggling.

## 📂 Project Structure

```text
cloudmesh/
│
├── main.py                  # Python FastAPI backend containing all algorithmic logic
├── cloudmesh.html           # Main frontend UI with neutral theme and interactive graphs
└── cloudmesh_basic.html     # Simplified/alternative frontend UI for basic testing