# Nephele Graph Evolution Guide

This document describes how Nephele dynamically refines domain knowledge structures over time using candidate data.

---

## 1. Statistics Collection

Data-driven learning is based on historical `concept_evaluations` logs. The `StatisticsCollector` aggregates:
- **Concept Traversal Count**: Total count of candidates visited a concept.
- **Fail/Success Ratio**: Proportion of evaluations with score <= 0.40 (failed) versus score >= 0.80 (mastered).
- **Latency Distribution**: Average grading turn time elapsed before candidate submission.

---

## 2. Mathematical Edge Updates

To estimate edge relationships between concepts $A$ and $B$, we compute:

$$\text{Edge Strength } (A \to B) = \frac{\text{Number of candidates who mastered both } A \text{ and } B}{\text{Number of candidates who mastered } A}$$

Where mastery is defined as achieving a score of $\ge 0.80$ on the concept.

### Edge Strength Action Thresholds
- **Confidence Upgrades** ($\ge 0.85$ strength over $\ge 3$ traversals): Suggest reinforcing the prerequisite link.
- **Weaken/Review Suggestions** ($< 0.40$ strength over $\ge 3$ traversals): Suggest weakening the link or reviewing the relationship.
- **New Edge Discovery** ($\ge 0.70$ co-occurrence between unlinked nodes): Suggest adding a new prerequisite-dependency edge.

---

## 3. Dynamic Concept Difficulties

Instead of hardcoded values, the system calculates concept difficulty scores dynamically:

$$\text{Difficulty Score} = (1.0 - \text{Avg Mastery}) \times 0.7 + \text{Failure Rate} \times 0.2 + \min\left(0.15, \frac{\text{Avg Latency}}{120}\right)$$

### Difficulty Classifications
- **Basic**: Score $< 0.40$
- **Intermediate**: Score $0.40 \le \text{Score} < 0.75$
- **Advanced**: Score $\ge 0.75$

---

## 4. Human-In-The-Loop Workflow

To maintain absolute structural safety, Nephele uses a **Human-in-the-Loop** model. The evolution engine does not write modifications directly back to domain JSONs. Instead:

1. System updates edge stats in `graph_edge_statistics` SQL table.
2. The Admin Dashboard lists these proposals under **Structural Optimization Proposals**.
3. Administrators inspect and manually approve modifications, maintaining structural validation safety.
