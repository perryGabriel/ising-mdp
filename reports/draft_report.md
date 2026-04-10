# Cross-Model Ising Dynamics: A Teaching-Oriented Study in Model Hierarchies, Mapping, and Scientific Critique

## Abstract

This report studies a hierarchy of Ising-inspired models with a dual purpose: (1) practical cross-model trajectory matching and parameter translation, and (2) pedagogy on scientific modeling, where different simplifying assumptions are proposed, tested, and critiqued against data. Our canonical reference is **Model 1** (independent-spin baseline in this project workflow), and we evaluate how well progressively richer or differently structured approximations recover its manifold behavior under matched experimental protocols. We emphasize uncertainty-aware summaries, explicit diagnostics of mismatch, and transparent validity domains.

---

## 1) Motivation and Philosophy of Modeling

### 1.1 Why multiple models?

In science, a “good model” is not simply the most detailed one—it is the one that is:
- clear about assumptions,
- fit for purpose,
- empirically testable,
- and falsifiable by diagnostics.

This project frames modeling as a **consensus-building workflow**: propose simplified models, align them under common experiments, compare outputs, and iteratively refine the simplifications.

### 1.2 Teaching objective

The primary educational lesson is that disagreement between models is informative. Residuals and mapping failures are not “bugs” to hide; they are evidence that clarifies what each simplification captures versus erases.

---

## 2) Model Hierarchy and Coarse-Graining Choices

We analyze five project models under shared parameter conventions and lattice seeds:

1. **Model 1 (reference in this project):** independent-spin baseline dynamics.
2. **Model 2:** coarse mean-field magnetization chain.
3. **Model 3:** local-neighborhood probability model with mixing.
4. **Model 4:** full exponential-state Gibbs-style model (small lattices only).
5. **Model 5:** restricted-interval affine operator over per-site probabilities.

### 2.1 Strengths vs weaknesses by simplification

- **Model 2 (mean-field):**
  - **Strength:** compact and fast; captures global magnetization tendency.
  - **Weakness:** cannot represent local correlation structure or heterogeneous transients.

- **Model 3 (local + mixing):**
  - **Strength:** introduces neighborhood information and smooth temporal adaptation.
  - **Weakness:** mixing can blur transient rates and may under/over-damp compared to reference dynamics.

- **Model 4 (full-state):**
  - **Strength:** highest mechanistic fidelity among current approximations.
  - **Weakness:** combinatorial state explosion limits tractable lattice size.

- **Model 5 (restricted-interval affine):**
  - **Strength:** explicit bounded parameter control, interpretable affine operator components.
  - **Weakness:** strong structural assumptions may limit expressiveness near nonlinear regimes.

---

## 3) Shared-Lattice Experiment Protocol

To ensure fair comparisons, all models are evaluated with:
- shared lattice sizes (within tractability limits),
- matched seeded initial conditions (or distributions derived from the same seed),
- consistent parameter grids over coupling `J`, field `h`, and temperature `T`,
- identical trajectory horizons and per-time summary extraction.

This avoids conflating model differences with experimental setup differences.

---

## 4) Manifold Construction `(J,h,T,t,m)` and Uncertainty Summaries

From raw trajectories, we construct grouped manifold summaries:
- index: `(model, J, h, T, t)`,
- statistics: `mean_m`, `var_m`, and sample count `n`.

For visualization and pedagogy, we now include:
- trajectory mean bands,
- residual maps,
- and a **summary-grid plot** with **95% CI fill** in a model-by-parameter array.

**Figure placeholder (summary-grid):**  
`[FIGURE A HERE] artifacts/plots/magnetization_summary_grid.png`  
**Caption:** Summary manifold panels. Columns are models; rows are parameter settings `(J,h,T)`. Each panel shows `mean_m(t)` with 95% CI shading to communicate uncertainty and sampling variability.

---

## 5) Parameter Translation Maps Across Models

We fit cross-model parameter maps from source to target manifolds via nearest-neighbor matching, then affine approximations.

### 5.1 Manual parameter adjustments and improved visual alignment

After initial automated fits, we introduced **manual parameter adjustments** to improve practical trajectory alignment in selected comparisons. These adjustments improved qualitative plot agreement (“line up better”), especially in regimes where single global affine maps could not capture distinct transient and steady-state behavior simultaneously.

We treat manual tuning as an explicit experimental intervention:
- report tuned values,
- compare pre/post fit error and visual overlap,
- retain automatic mapping as baseline.

**Figure placeholder (before/after overlays):**  
`[FIGURE B HERE] artifacts/plots/trajectory_matching.png`  
**Caption:** Example trajectory overlays before vs after manual parameter adjustment. Improvement is strongest in visually matched long-time means, with remaining deviations in transient shape.

---

## 6) Evaluation Artifacts: Residual Maps and Trajectory Overlays

Residual diagnostics are central to scientific critique:
- where mappings succeed (low residual regions),
- where they fail (high residual regions),
- and whether failures are systematic by parameter regime.

**Figure placeholder (residual map):**  
`[FIGURE C HERE] artifacts/plots/magnetization_residual_map.png`  
**Caption:** Mean fit error over source `(J,h)` (temperature-averaged) highlighting validity domains of cross-model parameter mapping.

**Figure placeholder (matching artifacts panel):**  
`[FIGURE D HERE] artifacts/plots/matching_artifacts.png`  
**Caption:** Fit-error distribution and time-resolved residual profile, used to separate broad-map quality from local trajectory behavior.

---

## 7) Explicit Renormalization Operator Comparison

We compare:
1. evolve full dynamics then project,
2. project first then evolve coarse dynamics.

The residual between these two paths quantifies non-commutativity of projection/evolution order, indicating where coarse representations lose critical information.

**Figure placeholder (operator comparison):**  
`[FIGURE E HERE] artifacts/operator/renormalization_operator.png`  
**Caption:** Left: two operator-order trajectories. Right: absolute residual over time. Reveals projection-order sensitivity and coarse-graining limits.

**Table placeholder (operator CSV summary):**  
`[TABLE 1 HERE] artifacts/operator/renormalization_operator.csv`  
**Caption:** Per-time values of `m_full_then_project`, `m_project_then_coarse`, and `abs_residual`.

---

## 8) Discussion: Validity Domains, Failure Modes, and Future Work

### 8.1 Why some matches still fail

Current affine parameter translation often conflates two distinct phenomena:
1. **Transient convergence rate** (how quickly trajectories approach their attractor),
2. **Steady-state magnetization level** (long-time mean behavior).

A single static affine remapping of `(J,h,T)` cannot always fit both simultaneously.

### 8.2 Recommended next-step methodology

#### A) Separate transient vs steady-state calibration
- Fit scaling factors or warps for **time-axis/transient dynamics** (e.g., effective timestep mapping),
- Fit parameter remapping separately for **steady-state statistics**.

This decomposition should reduce structural mismatch and improve interpretability.

#### B) Global search for per-model scaling factors

Because gradients are often unavailable/noisy in this discrete stochastic setting, we recommend a **genetic algorithm (GA)** (or other derivative-free optimizer) to fit per-model scaling factors for `(J,h,T)` relative to a canonical base.

Proposed setup:
- choose canonical Ising dynamics as baseline with unit scaling,
- optimize each other model’s scaling factors to minimize weighted manifold residuals,
- include regularization to avoid overfitting specific parameter pockets.

#### C) Regime-aware mappings

Instead of one global linear map, use:
- piecewise-linear maps over parameter partitions,
- or mixture-of-experts conditioned on `(J,h,T)` regime indicators.

### 8.3 Scientific takeaway

The strongest contribution is methodological: competing simplified models can be compared under shared protocols, criticized via residual evidence, and iteratively improved—demonstrating how scientific consensus forms through transparent model/data confrontation.

---

## 9) Conclusion

This project demonstrates a conference-worthy narrative with strong teaching value:
- model hierarchy design,
- uncertainty-aware manifold analysis,
- cross-model parameter translation,
- and explicit diagnostics of failure modes.

The framework supports both practical alignment improvements (including manual adjustments) and principled future optimization (transient/steady-state separation + GA scaling search), while preserving the central pedagogical message: **good scientific models are judged by clarity, testability, and honest residuals—not by apparent complexity alone.**
