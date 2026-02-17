import React, { useEffect, useMemo, useState } from "react";

type Vec = number[];
type Mat = number[][];

type SimulationConfig = {
  id: string;
  name: string;
  n: number;
  T: number;
  h: number;
  J: number;
  steps: number;
  blockParams: number[];
};

const BLOCK_SIZE = 2;
const COLOR_NEGATIVE = "rgb(0, 0, 255)";
const COLOR_POSITIVE = "rgb(255, 0, 0)";

const DEFAULT_PANEL_CONFIGS: SimulationConfig[] = [
  { id: "sim-a", name: "Simulation A", n: 6, T: 0.35, h: 0.2, J: 0.8, steps: 24, blockParams: [] },
  { id: "sim-b", name: "Simulation B", n: 6, T: 0.6, h: -0.35, J: 0.5, steps: 24, blockParams: [] },
  { id: "sim-c", name: "Simulation C", n: 8, T: 0.2, h: 0.0, J: -0.6, steps: 24, blockParams: [] },
  { id: "sim-d", name: "Simulation D", n: 8, T: 0.75, h: 0.5, J: 0.1, steps: 24, blockParams: [] },
];

const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value));

function normalizeBlockParams(blockParams: number[], n: number): number[] {
  const numBlocks = n * n;
  const next = Array.from({ length: numBlocks }, (_, i) => clamp(blockParams[i] ?? 0, -1, 1));
  if (!next.some((v) => Math.abs(v) > 0.001) && numBlocks > 3) {
    next[0] = 1;
    next[1] = -1;
    next[n] = -1;
    next[n + 1] = 1;
  }
  return next;
}

function hydrateConfigs(): SimulationConfig[] {
  if (typeof window === "undefined") {
    return DEFAULT_PANEL_CONFIGS.map((cfg) => ({
      ...cfg,
      blockParams: normalizeBlockParams(cfg.blockParams, cfg.n),
    }));
  }

  try {
    const raw = window.localStorage.getItem("ising_pages_simulations");
    if (!raw) {
      return DEFAULT_PANEL_CONFIGS.map((cfg) => ({
        ...cfg,
        blockParams: normalizeBlockParams(cfg.blockParams, cfg.n),
      }));
    }

    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) throw new Error("invalid storage format");

    return DEFAULT_PANEL_CONFIGS.map((defaults, index) => {
      const stored = parsed[index] ?? {};
      const n = clamp(Number(stored.n ?? defaults.n) || defaults.n, 2, 12);
      return {
        ...defaults,
        n,
        T: clamp(Number(stored.T ?? defaults.T) || defaults.T, 0, 1),
        h: clamp(Number(stored.h ?? defaults.h) || defaults.h, -1, 1),
        J: clamp(Number(stored.J ?? defaults.J) || defaults.J, -1, 1),
        steps: clamp(Number(stored.steps ?? defaults.steps) || defaults.steps, 1, 40),
        blockParams: normalizeBlockParams(Array.isArray(stored.blockParams) ? stored.blockParams : defaults.blockParams, n),
      };
    });
  } catch {
    return DEFAULT_PANEL_CONFIGS.map((cfg) => ({
      ...cfg,
      blockParams: normalizeBlockParams(cfg.blockParams, cfg.n),
    }));
  }
}

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

function makeNeighborsLattice(nRows: number, nCols: number): number[][] {
  const numBlocks = nRows * nCols;
  const neighbors: number[][] = Array.from({ length: numBlocks }, () => []);
  const idx = (r: number, c: number) => r * nCols + c;

  for (let r = 0; r < nRows; r++) {
    for (let c = 0; c < nCols; c++) {
      const i = idx(r, c);
      const neigh: number[] = [];
      if (r - 1 >= 0) neigh.push(idx(r - 1, c));
      if (r + 1 < nRows) neigh.push(idx(r + 1, c));
      if (c - 1 >= 0) neigh.push(idx(r, c - 1));
      if (c + 1 < nCols) neigh.push(idx(r, c + 1));
      neighbors[i] = neigh;
    }
  }

  return neighbors;
}

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

function blockColor(p: Vec, blockIndex: number, blockSize: number): string {
  const i0 = blockIndex * blockSize;
  const p0 = p[i0];
  const p1 = p[i0 + 1];
  const s = p0 + p1;
  const q0 = s > 0 ? p0 / s : 0.5;
  const q1 = s > 0 ? p1 / s : 0.5;
  const t = Math.max(-1, Math.min(1, q0 - q1));

  let r: number;
  let g: number;
  let b: number;
  if (t >= 0) {
    r = 1;
    g = 1 - t;
    b = 1 - t;
  } else {
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

function buildTransitionMatrix(n: number, T: number, h: number, J: number): Mat {
  const numBlocks = n * n;
  const neighbors = makeNeighborsLattice(n, n);
  const BLCK_ONES = makeBlockOnes(numBlocks, BLOCK_SIZE);
  const BLCK_AVG = makeBlockAvg(numBlocks, BLOCK_SIZE, neighbors);
  const dim = numBlocks * BLOCK_SIZE;

  const D: number[][] = [[(1 + h) / 2, 0], [0, (1 - h) / 2]];
  const M: number[][] = [[(1 + J) / 2, (1 - J) / 2], [(1 - J) / 2, (1 + J) / 2]];

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

  const term1 = BLCK_ONES.map((row) => row.map((v) => 0.5 * T * v));

  return Array.from({ length: dim }, (_, i) =>
    Array.from(
      { length: dim },
      (_, j) => term1[i][j] + (1 - T) * h * h * D_ONES[i][j] + (1 - T) * (1 - h * h) * M_AVG[i][j]
    )
  );
}

const LatticeGraph: React.FC<{
  p: Vec;
  n: number;
  selectedBlock?: number | null;
  onSelectBlock?: (idx: number) => void;
}> = ({ p, n, selectedBlock = null, onSelectBlock }) => {
  const size = 200;
  const margin = 16;
  const step = n > 1 ? (size - 2 * margin) / (n - 1) : 0;
  const nodeRadius = n > 1 ? Math.max(4, 0.45 * step) : (size - 2 * margin) / 4;

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
    <svg viewBox="0 0 200 200" className="w-full h-auto bg-slate-950 rounded-lg border border-slate-800">
      {edges.map(([u, v], i) => (
        <line key={i} x1={positions[u].x} y1={positions[u].y} x2={positions[v].x} y2={positions[v].y} stroke="#475569" strokeWidth={1.5} />
      ))}
      {positions.map((pos, index) => (
        <circle
          key={index}
          cx={pos.x}
          cy={pos.y}
          r={selectedBlock === index ? 1.15 * nodeRadius : nodeRadius}
          fill={blockColor(p, index, BLOCK_SIZE)}
          stroke={selectedBlock === index ? "#f8fafc" : "#0f172a"}
          strokeWidth={selectedBlock === index ? 2.5 : 1.75}
          onClick={() => onSelectBlock?.(index)}
          className={onSelectBlock ? "cursor-pointer" : ""}
        />
      ))}
    </svg>
  );
};

const SimulationCard: React.FC<{
  config: SimulationConfig;
  onChange: (next: SimulationConfig) => void;
}> = ({ config, onChange }) => {
  const [selectedBlock, setSelectedBlock] = useState<number | null>(null);
  const [frame, setFrame] = useState(0);

  const numBlocks = config.n * config.n;
  const blockParams = useMemo(() => normalizeBlockParams(config.blockParams, config.n), [config.blockParams, config.n]);
  const p0 = useMemo(() => blocksToVec(blockParams, numBlocks, BLOCK_SIZE), [blockParams, numBlocks]);
  const transition = useMemo(() => buildTransitionMatrix(config.n, config.T, config.h, config.J), [config.n, config.T, config.h, config.J]);
  const trajectory = useMemo(() => simulate(transition, p0, config.steps), [transition, p0, config.steps]);

  useEffect(() => {
    setFrame(0);
  }, [config.n, config.T, config.h, config.J, config.steps, blockParams]);

  useEffect(() => {
    const id = window.setInterval(() => {
      setFrame((value) => (value + 1) % trajectory.length);
    }, 450);
    return () => window.clearInterval(id);
  }, [trajectory.length]);

  useEffect(() => {
    if (selectedBlock !== null && selectedBlock >= numBlocks) {
      setSelectedBlock(null);
    }
  }, [selectedBlock, numBlocks]);

  const activeState = trajectory[frame % trajectory.length] ?? p0;

  const update = <K extends keyof SimulationConfig>(field: K, value: SimulationConfig[K]) => {
    onChange({ ...config, [field]: value });
  };

  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 space-y-3">
      <header className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">{config.name}</h2>
        <span className="text-xs text-slate-400">frame {frame + 1}/{trajectory.length}</span>
      </header>

      <div className="grid grid-cols-2 gap-2 text-sm">
        <label>
          n
          <input type="number" min={2} max={12} value={config.n} onChange={(e) => update("n", clamp(Number(e.target.value) || 2, 2, 12))} className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-2 py-1" />
        </label>
        <label>
          steps
          <input type="number" min={1} max={40} value={config.steps} onChange={(e) => update("steps", clamp(Number(e.target.value) || 1, 1, 40))} className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-2 py-1" />
        </label>
        <label>
          T
          <input type="number" step={0.05} min={0} max={1} value={config.T} onChange={(e) => update("T", clamp(Number(e.target.value), 0, 1))} className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-2 py-1" />
        </label>
        <label>
          h
          <input type="number" step={0.05} min={-1} max={1} value={config.h} onChange={(e) => update("h", clamp(Number(e.target.value), -1, 1))} className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-2 py-1" />
        </label>
        <label className="col-span-2">
          J
          <input type="number" step={0.05} min={-1} max={1} value={config.J} onChange={(e) => update("J", clamp(Number(e.target.value), -1, 1))} className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-2 py-1" />
        </label>
      </div>

      <div className="grid md:grid-cols-2 gap-3">
        <div>
          <p className="text-xs text-slate-400 mb-1">Initial lattice (click node, then tune its polarization)</p>
          <LatticeGraph p={p0} n={config.n} selectedBlock={selectedBlock} onSelectBlock={setSelectedBlock} />
        </div>
        <div>
          <p className="text-xs text-slate-400 mb-1">Evolved lattice</p>
          <LatticeGraph p={activeState} n={config.n} />
        </div>
      </div>

      {selectedBlock !== null && (
        <div className="rounded-lg border border-slate-700 bg-slate-950 p-2">
          <div className="flex items-center justify-between text-xs mb-1">
            <span>Node {selectedBlock}</span>
            <span>{blockParams[selectedBlock].toFixed(2)}</span>
          </div>
          <input
            type="range"
            min={-1}
            max={1}
            step={0.01}
            value={blockParams[selectedBlock] ?? 0}
            onChange={(e) => {
              const next = [...blockParams];
              next[selectedBlock] = Number(e.target.value);
              update("blockParams", next);
            }}
            className="w-full"
          />
          <div className="text-xs text-slate-400 mt-1">{COLOR_NEGATIVE} ↔ {COLOR_POSITIVE}</div>
        </div>
      )}
    </section>
  );
};

const DynamicalSystemSimulator: React.FC = () => {
  const [configs, setConfigs] = useState<SimulationConfig[]>(() => hydrateConfigs());

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem("ising_pages_simulations", JSON.stringify(configs));
  }, [configs]);

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <div className="max-w-7xl mx-auto space-y-4">
        <header className="space-y-2">
          <h1 className="text-2xl font-bold">Ising Model MDP Simulator (GitHub Pages edition)</h1>
          <p className="text-sm text-slate-300">
            Four independent simulations run in parallel. Each panel has isolated parameters (n, T, h, J, steps, and node-level polarizations), so experiments can diverge without interfering with one another.
          </p>
        </header>

        <div className="grid xl:grid-cols-2 gap-4">
          {configs.map((config, index) => (
            <SimulationCard
              key={config.id}
              config={config}
              onChange={(next) => {
                const clone = [...configs];
                clone[index] = {
                  ...next,
                  blockParams: normalizeBlockParams(next.blockParams, next.n),
                };
                setConfigs(clone);
              }}
            />
          ))}
        </div>
      </div>
    </main>
  );
};

export { makeBlockOnes, makeNeighborsLattice, makeBlockAvg, matVecMul, simulate, blocksToVec, blockColor };

export default DynamicalSystemSimulator;
