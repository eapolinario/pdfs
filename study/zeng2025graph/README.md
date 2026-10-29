# A Graph Representation Learning-Based Method for Event Prediction

Xi Zeng, Guangchun Luo, Ke Qin, Pengyi Zheng (2025)

- PDF: [`files/zeng2025graph.pdf`](../../files/zeng2025graph.pdf)
- Source: <https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/ise2/9706647>
- Notes: 3 short reading notes in this directory.

## What the paper is trying to do

The paper treats event prediction as a graph problem rather than a plain sequence problem. The key idea is:

- convert events into a graph where nodes are event slots or actors/actions and edges encode likely causality / temporal order;
- use BERT to turn event text into semantic embeddings;
- use a GNN to propagate structure across the event graph;
- then use the fused representation to predict plausible next events or career transitions.

This is a good fit for settings where context matters more than a single sentence: a career change is not only “what happened” but also “who was involved, what order it happened in, and what company/role context it happened in”.

## What I could not find

I could not find a direct code repo from the paper authors. The paper seems to describe a custom pipeline rather than a public implementation. So instead of looking for a literal reproduction, the useful tactic is to map the paper to a standard GNN + language-model stack:

- event text -> BERT (or a sentence transformer) embeddings
- event graph -> graph message passing (GCN/GAT/GraphSAGE style)
- dynamic worker/company graph -> temporal random walks + skip-gram / node2vec style training

That is enough to build intuition before you try an implementation.

## The core intuition, in one sentence

The paper says: if you only model text, you miss the graph structure; if you only model the graph, you miss the semantics.

## Socratic guide

Ask yourself these as you read:

1. Why does the paper construct a causal graph instead of just training on event sequences?
   - A sequence only says “A happened before B”. A graph says “A, B, and C cohere as a structure”, which is more expressive.

2. Why BERT at all?
   - Because event descriptions are not just symbols. The predicate, role, and object carry meaning: “resigned”, “joined”, “promoted”, “left the company” are not interchangeable.

3. Why use a GNN after BERT?
   - BERT gives semantic embeddings for each event node; the GNN stitches together nearby nodes and propagates context. That is the “graph + text” fusion.

4. Why a dynamic bipartite graph for career choices?
   - Employees and companies form two types of nodes; edges represent job history over time. This turns a career-choice problem into a temporal link-prediction problem.

5. Why random walks and skip-gram in the employee case?
   - If you want a useful representation of a node from sequence and context, you want nearby nodes to be close in vector space. Skip-gram does exactly that.

## The implementation sketch

The paper’s method is conceptually close to this:

```python
# 1) Build an event graph
for event in events:
    subject, predicate, object_ = parse(event)
    node = encode(event_text)
    graph.add_node(node)
    for previous in context_window(event):
        graph.add_edge(previous, node, weight=cooccurrence_count(previous, event))

# 2) Semantic regularization with BERT
text_tokens = tokenizer(event_text)
bert_embed = bert(text_tokens)  # contextual event embedding

# 3) Graph propagation with GNN
for layer in range(num_layers):
    for node in graph.nodes:
        neigh = aggregate(neighbor_embeddings(node))
        node.embedding = combine(node.embedding, neigh)

# 4) Fuse graph structure and semantics
h = concat(bert_embed, graph_embedding)
logits = linear(h)
prediction = softmax(logits)

# 5) Career case: dynamic bipartite graph
# employees -- company edges with timestamps
# temporal walk -> skip-gram -> low-dim vectors
# classify likely resignation / job transition
```

The important part is not the exact math; it is the pattern:

- semantic embeddings for nodes,
- message passing over graph structure,
- time-aware walks for dynamic relationships,
- end with a prediction head.

## Reading plan

1. Start with the introduction and ask what kind of prediction problem the paper claims to solve.
2. Read the “script event prediction” section and cleanly separate:
   - event graph construction,
   - BERT regularization,
   - GNN reasoning/aggregation,
   - final prediction.
3. Read the employee career-choice section and translate the words into a graph picture: employee nodes, company nodes, timestamps, edges, and a binary outcome.
4. Only then read the experiment section for what they measured and why it matters.

## Open questions

- [ ] Is the event graph mostly a causal graph or mainly a co-occurrence graph with weights?
- [ ] What is the real benefit of the BERT + GNN fusion versus a strong text-only baseline?
- [ ] Do the dynamics in the employee case really need a temporal graph, or would a static graph plus time features work?
- [ ] Which part of the method is the bottleneck: graph construction, BERT embedding, or the prediction head?
- [ ] If we had to reimplement this in PyG or DGL, what would be the minimal version to get the intended behavior?

## Key sections to read in order

- §1: introduction and motivation
- §3: script event prediction with GNN + BERT
- §4.1: employee career-choice problem setup
- §4.2: dynamic bipartite graph representation learning
- §4.3: evaluation setup

