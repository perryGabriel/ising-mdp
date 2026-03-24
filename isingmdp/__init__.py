"""Public package exports for the Ising MDP demos.

This compatibility package lets users import from `isingmdp` after
`pip install` while the core implementation continues to live in
`python_demos`.
"""

from python_demos.ising_four_models import (  # noqa: F401
    IsingParams,
    Distribution,
    Spin,
    State,
    expected_site_magnetization,
    gibbs_next_distribution,
    grid_edges,
    grid_neighbors,
    ising_energy,
    logistic,
    model_1_heatmap_trajectory,
    model_1_single_spin,
    model_2_heatmap_trajectory,
    model_2_mean_field,
    model_3_heatmap_trajectory,
    model_3_local_probabilities,
    model_4_full_state_space,
    model_4_heatmap_trajectory,
    normalize,
    probs_to_state_distribution,
    render_lattice,
    sample_from_distribution,
    spins_to_grid,
    state_probability_bars,
)

__all__ = [
    "IsingParams",
    "Distribution",
    "Spin",
    "State",
    "expected_site_magnetization",
    "gibbs_next_distribution",
    "grid_edges",
    "grid_neighbors",
    "ising_energy",
    "logistic",
    "model_1_heatmap_trajectory",
    "model_1_single_spin",
    "model_2_heatmap_trajectory",
    "model_2_mean_field",
    "model_3_heatmap_trajectory",
    "model_3_local_probabilities",
    "model_4_full_state_space",
    "model_4_heatmap_trajectory",
    "normalize",
    "probs_to_state_distribution",
    "render_lattice",
    "sample_from_distribution",
    "spins_to_grid",
    "state_probability_bars",
]
