# Renormalization operator artifacts

Outputs from `renormalization_operator_demo.py` comparing:
- evolve full then project, vs
- project then evolve coarse,
with per-time residual diagnostics.

## Files in this folder

- `renormalization_operator.csv`
  - `t`: timestep index.
  - `m_full_then_project`: magnetization after evolving the full-state model and then projecting to mean magnetization.
  - `m_project_then_coarse`: magnetization after projecting first and then evolving the coarse mean-field model.
  - `abs_residual`: `|m_full_then_project - m_project_then_coarse|`.

- `renormalization_operator.png`
  - **Left panel**: both trajectories (`m_full_then_project` and `m_project_then_coarse`) over time.
  - **Right panel**: absolute residual `|Δm|` over time.

Interpretation: this artifact tests how much projection and evolution fail to commute for the chosen parameter point and seeded initial state.
