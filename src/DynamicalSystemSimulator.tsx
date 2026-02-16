import React, { useState, useMemo, useEffect } from "react";

// Types
type Vec = number[];
type Mat = number[][];

const BLOCK_SIZE = 2; // each block is 2x2

// Default block polarizations (used when there is no saved state yet)
// Length should be n^2 for n×n lattice; we will resize when n changes.
// Length 100 = 10x10 lattice; you can overwrite this with your own array.
const DEFAULT_BLOCK_PARAMS: number[] = (() => {
  const arr = Array(100).fill(0);
  arr[0] = 1; // first node fully "red"
  arr[1] = -1; // node fully "blue"
  arr[2] = 1; 
  arr[3] = -1; 
  arr[10] = -1; 
  arr[11] = 1; 
  arr[12] = -1; 
  arr[20] = 1; 
  arr[21] = -1; 
  arr[30] = -1; 
  return arr;
})();

// Build a block-diagonal matrix with 2x2 ones blocks
function makeBlockOnes(numBlocks: number, blockSize: number): Mat {
  const dim = numBlocks * blockSize;
  const A: Mat = Array.from({ length: dim }, () => Array(dim).fill(0));

  for (let b = 0; b < numBlocks; b++) {
    const rowOffset = b * blockSize;
    const colOffset = b * blockSize;
    for (let i = 0; i < blockSize; i++) {
      for (let j = 0; j < blockSize; j++) {
        A[rowOffset + i][colOffset + j] = 1;
      }
    }
  }
  return A;
}

// 4-neighbor adjacency for an n x n grid of blocks
function makeNeighborsLattice(nRows: number, nCols: number): number[][] {
  const numBlocks = nRows * nCols;
  const neighbors: number[][] = Array.from({ length: numBlocks }, () => []);

  const idx = (r: number, c: number) => r * nCols + c;

  for (let r = 0; r < nRows; r++) {
    for (let c = 0; c < nCols; c++) {
      const i = idx(r, c);
      const neigh: number[] = [];
      // up
      if (r - 1 >= 0) neigh.push(idx(r - 1, c));
      // down
      if (r + 1 < nRows) neigh.push(idx(r + 1, c));
      // left
      if (c - 1 >= 0) neigh.push(idx(r, c - 1));
      // right
      if (c + 1 < nCols) neigh.push(idx(r, c + 1));
      neighbors[i] = neigh;
    }
  }

  return neighbors;
}

// BLCK_AVG: each block-row averages its neighbors' block states
// Each block row has (1/N) * [I ... I] in the columns corresponding to neighbors.
function makeBlockAvg(numBlocks: number, blockSize: number, neighbors: number[][]): Mat {
  const dim = numBlocks * blockSize;
  const A: Mat = Array.from({ length: dim }, () => Array(dim).fill(0));

  for (let b = 0; b < numBlocks; b++) {
    const neigh = neighbors[b];
    const N = neigh.length;
    if (N === 0) continue;
    const weight = 1 / N;

    for (const nb of neigh) {
      const rowOffset = b * blockSize;
      const colOffset = nb * blockSize;
      // place weight * I_block in (b, nb) block
      for (let i = 0; i < blockSize; i++) {
        A[rowOffset + i][colOffset + i] += weight;
      }
    }
  }

  return A;
}

function matVecMul(A: Mat, x: Vec): Vec {
  const n = A.length;
  const m = x.length;
  const y: Vec = Array(n).fill(0);
  for (let i = 0; i < n; i++) {
    let sum = 0;
    for (let j = 0; j < m; j++) {
      sum += A[i][j] * x[j];
    }
    y[i] = sum;
  }
  return y;
}

function simulate(A: Mat, p0: Vec, steps: number): Vec[] {
  const traj: Vec[] = [];
  let p = [...p0];
  traj.push([...p]);
  for (let k = 0; k < steps; k++) {
    p = matVecMul(A, p);
    traj.push([...p]);
  }
  return traj;
}

// Map per-block interpolation parameter t ∈ [-1,1] to a full vector
// t = 1  → [1,0] in that block
// t = -1 → [0,1] in that block
// t = 0  → [0.5,0.5] in that block
function blocksToVec(blockParams: number[], numBlocks: number, blockSize: number): Vec {
  const dim = numBlocks * blockSize;
  const v: Vec = Array(dim).fill(0);
  for (let b = 0; b < numBlocks; b++) {
    const t = blockParams[b] ?? 0;
    const p0 = (1 + t) / 2;
    const p1 = (1 - t) / 2;
    const i0 = b * blockSize;
    v[i0] = p0;
    v[i0 + 1] = p1;
  }
  return v;
}

// Map a 2-component block [p0, p1] to a thermal red–white–blue color
function blockColor(p: Vec, blockIndex: number, blockSize: number): string {
  const i0 = blockIndex * blockSize;
  const p0 = p[i0];
  const p1 = p[i0 + 1];
  const s = p0 + p1;
  const q0 = s > 0 ? p0 / s : 0.5;
  const q1 = s > 0 ? p1 / s : 0.5;
  const t = Math.max(-1, Math.min(1, q0 - q1)); // -1 (blue) to +1 (red)

  let r: number, g: number, b: number;
  if (t >= 0) {
    // interpolate between white (t=0) and red (t=1)
    r = 1;
    g = 1 - t;
    b = 1 - t;
  } else {
    // interpolate between white (t=0) and blue (t=-1)
    const u = -t;
    r = 1 - u;
    g = 1 - u;
    b = 1;
  }
  const R = Math.round(255 * r);
  const G = Math.round(255 * g);
  const B = Math.round(255 * b);
  return `rgb(${R}, ${G}, ${B})`;
}

interface IsingVizProps {
  trajectory: Vec[];
  frame: number;
  n: number;
}

const IsingViz: React.FC<IsingVizProps> = ({ trajectory, frame, n }) => {
  if (!trajectory.length) return null;
  const p = trajectory[frame % trajectory.length];

  // positions for n x n grid
  const size = 200;
  const margin = 20;
  const step = n > 1 ? (size - 2 * margin) / (n - 1) : 0;

  // Choose radius so nearest neighbors just touch (slightly smaller than half the spacing)
  const nodeRadius = n > 1 ? 0.45 * step : (size - 2 * margin) / 4;

  const positions: { x: number; y: number }[] = [];
  for (let r = 0; r < n; r++) {
    for (let c = 0; c < n; c++) {
      positions.push({ x: margin + c * step, y: margin + r * step });
    }
  }

  const edges: [number, number][] = [];
  const idx = (r: number, c: number) => r * n + c;
  for (let r = 0; r < n; r++) {
    for (let c = 0; c < n; c++) {
      const i = idx(r, c);
      if (c + 1 < n) edges.push([i, idx(r, c + 1)]);
      if (r + 1 < n) edges.push([i, idx(r + 1, c)]);
    }
  }

  return (
    <svg
      viewBox="0 0 200 200"
      className="w-64 h-64 md:w-64 md:h-64 bg-slate-900 rounded-xl border border-slate-800 mx-auto"
    >
      {/* edges */}
      {edges.map(([u, v], i) => (
        <line
          key={i}
          x1={positions[u].x}
          y1={positions[u].y}
          x2={positions[v].x}
          y2={positions[v].y}
          stroke="#64748b"
          strokeWidth={2}
        />
      ))}

      {/* nodes */}
      {positions.map((pos, idx) => (
        <circle
          key={idx}
          cx={pos.x}
          cy={pos.y}
          r={nodeRadius}
          fill={blockColor(p, idx, BLOCK_SIZE)}
          stroke="#0f172a"
          strokeWidth={2}
        />
      ))}
    </svg>
  );
};

interface InitialLatticeProps {
  p0: Vec;
  selectedBlock: number | null;
  onSelectBlock: (idx: number) => void;
  n: number;
}

const InitialLattice: React.FC<InitialLatticeProps> = ({ p0, selectedBlock, onSelectBlock, n }) => {
  const size = 200;
  const margin = 20;
  const step = n > 1 ? (size - 2 * margin) / (n - 1) : 0;

  // Match radius logic with IsingViz so nodes touch but don't overlap
  const nodeRadius = n > 1 ? 0.45 * step : (size - 2 * margin) / 4;

  const positions: { x: number; y: number }[] = [];
  for (let r = 0; r < n; r++) {
    for (let c = 0; c < n; c++) {
      positions.push({ x: margin + c * step, y: margin + r * step });
    }
  }

  const edges: [number, number][] = [];
  const idx = (r: number, c: number) => r * n + c;
  for (let r = 0; r < n; r++) {
    for (let c = 0; c < n; c++) {
      const i = idx(r, c);
      if (c + 1 < n) edges.push([i, idx(r, c + 1)]);
      if (r + 1 < n) edges.push([i, idx(r + 1, c)]);
    }
  }

  return (
    <svg
      viewBox="0 0 200 200"
      className="w-64 h-64 md:w-64 md:h-64 bg-slate-900 rounded-xl border border-slate-800 cursor-pointer mx-auto"
    >
      {edges.map(([u, v], i) => (
        <line
          key={i}
          x1={positions[u].x}
          y1={positions[u].y}
          x2={positions[v].x}
          y2={positions[v].y}
          stroke="#64748b"
          strokeWidth={2}
        />
      ))}

      {positions.map((pos, idx) => (
        <circle
          key={idx}
          cx={pos.x}
          cy={pos.y}
          r={selectedBlock === idx ? 1.2 * nodeRadius : nodeRadius}
          fill={blockColor(p0, idx, BLOCK_SIZE)}
          stroke={selectedBlock === idx ? "#e5e7eb" : "#0f172a"}
          strokeWidth={selectedBlock === idx ? 3 : 2}
          onClick={() => onSelectBlock(idx)}
        />
      ))}
    </svg>
  );
};

const DynamicalSystemSimulator: React.FC = () => {
  // n x n lattice
  const [n, setN] = useState(() => {
    if (typeof window === "undefined") return 20;
    const stored = window.localStorage.getItem("dsim_n");
    const v = stored !== null ? Number(stored) : NaN;
    return Number.isFinite(v) && v >= 1 ? v : 10;
  });

  const [T, setT] = useState(() => {
    if (typeof window === "undefined") return 1;
    const stored = window.localStorage.getItem("dsim_T");
    const v = stored !== null ? Number(stored) : NaN;
    return Number.isFinite(v) ? v : 1;
  });

  const [h, setH] = useState(() => {
    if (typeof window === "undefined") return 0;
    const stored = window.localStorage.getItem("dsim_h");
    const v = stored !== null ? Number(stored) : NaN;
    return Number.isFinite(v) ? v : 0;
  });

  const [J, setJ] = useState(() => {
    if (typeof window === "undefined") return 0;
    const stored = window.localStorage.getItem("dsim_J");
    const v = stored !== null ? Number(stored) : NaN;
    return Number.isFinite(v) ? v : 0;
  });

  const [steps, setSteps] = useState(() => {
    if (typeof window === "undefined") return 10;
    const stored = window.localStorage.getItem("dsim_steps");
    const v = stored !== null ? Number(stored) : NaN;
    return Number.isFinite(v) && v >= 0 ? v : 20;
  });

  const numBlocks = n * n;
  const dim = numBlocks * BLOCK_SIZE;

  const [blockParams, setBlockParams] = useState<number[]>(() => {
    if (typeof window === "undefined") return DEFAULT_BLOCK_PARAMS;
    const stored = window.localStorage.getItem("dsim_blockParams");
    if (!stored) return DEFAULT_BLOCK_PARAMS;
    try {
      const arr = JSON.parse(stored);
      if (Array.isArray(arr)) {
        return arr.map((x) => (Number.isFinite(Number(x)) ? Number(x) : 0));
      }
    } catch {
      // ignore
    }
    return DEFAULT_BLOCK_PARAMS;
  });

  const [selectedBlock, setSelectedBlock] = useState<number | null>(null);

  // Resize blockParams when n changes
  useEffect(() => {
    setBlockParams((prev) => {
      const nb = numBlocks;
      const next = Array(nb).fill(0) as number[];
      for (let i = 0; i < Math.min(nb, prev.length); i++) {
        next[i] = prev[i];
      }
      if (prev.length === 0 && nb > 0) {
        next[0] = 1;
      }
      return next;
    });
    setSelectedBlock(null);
  }, [numBlocks]);

  // Persist parameters and initial polarizations
  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem("dsim_n", String(n));
    window.localStorage.setItem("dsim_T", String(T));
    window.localStorage.setItem("dsim_h", String(h));
    window.localStorage.setItem("dsim_J", String(J));
    window.localStorage.setItem("dsim_steps", String(steps));
    window.localStorage.setItem("dsim_blockParams", JSON.stringify(blockParams));
  }, [n, T, h, J, steps, blockParams]);

  const neighbors = useMemo(() => makeNeighborsLattice(n, n), [n]);
  const BLCK_ONES = useMemo(() => makeBlockOnes(numBlocks, BLOCK_SIZE), [numBlocks]);
  const BLCK_AVG = useMemo(() => makeBlockAvg(numBlocks, BLOCK_SIZE, neighbors), [numBlocks, neighbors]);

  const A = useMemo(() => {
    // D(h) = diag((1+h)/2, (1-h)/2)
    const D: number[][] = [
      [(1 + h) / 2, 0],
      [0, (1 - h) / 2],
    ];

    // M(J) = (1+J)/2 I + (1-J)/2 [[0,1],[1,0]]
    const M: number[][] = [
      [(1 + J) / 2, (1 - J) / 2],
      [(1 - J) / 2, (1 + J) / 2],
    ];

    // Blockwise left multiplication by a 2x2 matrix on each 2-row block
    const blockLeftMultiply = (block: number[][], base: Mat): Mat => {
      const out: Mat = Array.from({ length: dim }, () => Array(dim).fill(0));
      for (let b = 0; b < numBlocks; b++) {
        const ro = b * BLOCK_SIZE;
        for (let j = 0; j < dim; j++) {
          const x0 = base[ro][j];
          const x1 = base[ro + 1][j];
          out[ro][j] = block[0][0] * x0 + block[0][1] * x1;
          out[ro + 1][j] = block[1][0] * x0 + block[1][1] * x1;
        }
      }
      return out;
    };

    const D_ONES = blockLeftMultiply(D, BLCK_ONES);
    const M_AVG = blockLeftMultiply(M, BLCK_AVG);

    // 0.5 T * BLCK_ONES
    const term1: Mat = BLCK_ONES.map((row) => row.map((v) => 0.5 * T * v));

    // (1-T)[ h^2 D BLCK_ONES + (1-h^2) M BLCK_AVG ]
    const term2: Mat = Array.from({ length: dim }, (_, i) =>
      Array.from({ length: dim }, (_, j) =>
        (1 - T) * h * h * D_ONES[i][j] + (1 - T) * (1 - h * h) * M_AVG[i][j]
      )
    );

    const Aout: Mat = Array.from({ length: dim }, (_, i) =>
      Array.from({ length: dim }, (_, j) => term1[i][j] + term2[i][j])
    );

    return Aout;
  }, [BLCK_ONES, BLCK_AVG, T, h, J, dim, numBlocks]);

  const p0 = useMemo(() => blocksToVec(blockParams, numBlocks, BLOCK_SIZE), [blockParams, numBlocks]);

  const trajectory = useMemo(() => simulate(A, p0, steps), [A, p0, steps]);

  const [frame, setFrame] = useState(0);

  useEffect(() => {
    if (trajectory.length <= 1) return;
    if (typeof window === "undefined") return;
    const id = window.setInterval(() => {
      setFrame((f) => (f + 1) % trajectory.length);
    }, 500); // 500 ms per frame
    return () => window.clearInterval(id);
  }, [trajectory]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center p-6">
      <div className="w-full max-w-5xl space-y-4">
        <h1 className="text-2xl font-bold">Ising Model MDP Dynamical System Simulator</h1>
        <p className="text-sm text-slate-300 space-y-1">
          <span>
            We simulate the linear system on an n×n grid of 2×2 blocks (dimension 2n²) with transition matrix:<br />
          </span>
          <code className="block text-xs bg-slate-900/80 border border-slate-800 rounded-md px-2 py-1 overflow-x-auto">
            {`A = 0.5 T\\,\\mathrm{BLCK\\_ONES} + (1-T)\\big[ h^2\\,\\mathrm{diag}((1+h)/2,(1-h)/2)\\,\\mathrm{BLCK\\_ONES} + (1-h^2)((1+J)/2 I + (1-J)/2 [[0,1],[1,0]])\\,\\mathrm{BLCK\\_AVG} \\big]`}
          </code>
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Parameters card */}
          <div className="space-y-3 p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
            <h2 className="font-semibold mb-2">Parameters</h2>

            <label className="block text-sm mb-2">
              <span className="block mb-1">n (lattice size)</span>
              <input
                type="number"
                value={n}
                min={1}
                max={10}
                onChange={(e) => {
                  const val = Math.max(1, Math.min(10, Number(e.target.value) || 1));
                  setN(val);
                }}
                className="w-full rounded-md bg-slate-900 border border-slate-700 px-2 py-1 text-sm"
              />
            </label>

            <label className="block text-sm mb-2">
              <span className="block mb-1"><br />T (tempurature)</span>
              <input
                type="number"
                value={T}
                onChange={(e) => setT(Number(e.target.value))}
                step={0.05}
                className="w-full rounded-md bg-slate-900 border border-slate-700 px-2 py-1 text-sm"
              />
            </label>

            <label className="block text-sm mb-2">
              <span className="block mb-1"><br />h (external field)</span>
              <input
                type="number"
                value={h}
                onChange={(e) => setH(Number(e.target.value))}
                step={0.05}
                min={-1}
                max={1}
                className="w-full rounded-md bg-slate-900 border border-slate-700 px-2 py-1 text-sm"
              />
            </label>

            <label className="block text-sm mb-2">
              <span className="block mb-1"><br />J (coupling)</span>
              <input
                type="number"
                value={J}
                onChange={(e) => setJ(Number(e.target.value))}
                step={0.05}
                min={-1}
                max={1}
                className="w-full rounded-md bg-slate-900 border border-slate-700 px-2 py-1 text-sm"
              />
            </label>

            <label className="block text-sm mb-2">
              <span className="block mb-1"><br />Steps</span>
              <input
                type="number"
                value={steps}
                onChange={(e) => setSteps(Math.max(0, Number(e.target.value) || 0))}
                className="w-full rounded-md bg-slate-900 border border-slate-700 px-2 py-1 text-sm"
              />
            </label>

            <label className="block text-sm">
              <span className="block mb-1"><br />Initial state p₀ (derived from node sliders)</span>
              <textarea
                value={p0.map((v) => v.toFixed(3)).join(", ")}
                readOnly
                rows={3}
                className="w-full rounded-md bg-slate-900 border border-slate-700 px-2 py-1 text-sm"
              />
            </label>
          </div>

          {/* Lattices card: stacked initial + evolution, old style */}
          <div className="space-y-3 p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
            <h2 className="font-semibold mb-2">Visualization</h2>

            {/* Initial lattice and sliders */}
            <h3 className="font-medium text-sm mb-1">Initial State</h3>
            <p className="text-xs text-slate-400 mb-1">
              Click a node to select it, then adjust its slider below. Each node encodes the magnetic polarization of an atom in the lattice, between -1 (blue) and +1 (red).
            </p>
            <InitialLattice
              p0={p0}
              selectedBlock={selectedBlock}
              onSelectBlock={setSelectedBlock}
              n={n}
            />

            {selectedBlock !== null && (
              <div className="mt-2 space-y-1 text-xs">
                <div className="flex items-center justify-between">
                  <span>Node {selectedBlock}</span>
                  <span className="text-slate-300">
                    t = {blockParams[selectedBlock]?.toFixed(2)}
                  </span>
                </div>
                <input
                  type="range"
                  min={-1}
                  max={1}
                  step={0.01}
                  value={blockParams[selectedBlock] ?? 0}
                  onChange={(e) => {
                    const t = Number(e.target.value);
                    setBlockParams((prev) => {
                      const next = [...prev];
                      next[selectedBlock] = t;
                      return next;
                    });
                  }}
                  className="w-full"
                />
                <div>
                  {(() => {
                    const t = blockParams[selectedBlock] ?? 0;
                    const p0b = (1 + t) / 2;
                    const p1b = (1 - t) / 2;
                    return (
                      <span className="text-slate-300">
                        P(+ve magnitization) ≈ {p0b.toFixed(3)}
                      </span>
                    );
                  })()}
                </div>
              </div>
            )}

            {/* Ising-style evolution viz stacked below */}
            <div className="mt-4">
              <h3 className="font-medium text-sm mb-1">Ising-style Visualization</h3>
              <p className="text-xs text-slate-400 mb-1">
                Time evolution of the same n×n lattice under the linear update. Node color encodes [p₁, p₂]:
                red ≈ [1,0], blue ≈ [0,1], white ≈ [0.5,0.5]. The animation loops through the trajectory.
              </p>
              <IsingViz trajectory={trajectory} frame={frame} n={n} />
            </div>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <h2 className="font-semibold mb-2">Trajectory</h2>
          <div className="overflow-x-auto text-xs max-h-80 overflow-y-auto">
            <table className="min-w-full border-collapse">
              <thead>
                <tr>
                  <th className="border border-slate-800 px-2 py-1 text-left">k</th>
                  {Array.from({ length: dim }, (_, i) => (
                    <th
                      key={i}
                      className="border border-slate-800 px-2 py-1 text-right"
                    >
                      p[{i}]
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {trajectory.map((p, k) => (
                  <tr key={k}>
                    <td className="border border-slate-800 px-2 py-1">{k}</td>
                    {p.map((v, i) => (
                      <td
                        key={i}
                        className="border border-slate-800 px-2 py-1 text-right"
                      >
                        {v.toFixed(4)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export {
  makeBlockOnes,
  makeNeighborsLattice,
  makeBlockAvg,
  matVecMul,
  simulate,
  blocksToVec,
  blockColor,
};

export default DynamicalSystemSimulator;
