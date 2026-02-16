import { render, screen } from "@testing-library/react";
import React from "react";
import DynamicalSystemSimulator, {
  makeBlockOnes,
  makeNeighborsLattice,
  makeBlockAvg,
  matVecMul,
  simulate,
  blocksToVec,
  blockColor,
} from "./DynamicalSystemSimulator";

type Vec = number[];
type Mat = number[][];

describe("makeBlockOnes", () => {
  it("builds a correct 2-block (4x4) block-diagonal ones matrix", () => {
    const A = makeBlockOnes(2, 2);
    expect(A.length).toBe(4);
    expect(A[0].length).toBe(4);

    // block 0
    const block0: Mat = [
      [A[0][0], A[0][1]],
      [A[1][0], A[1][1]],
    ];
    // block 1
    const block1: Mat = [
      [A[2][2], A[2][3]],
      [A[3][2], A[3][3]],
    ];

    // ones in diagonal blocks
    expect(block0).toEqual([
      [1, 1],
      [1, 1],
    ]);
    expect(block1).toEqual([
      [1, 1],
      [1, 1],
    ]);

    // zeros in off-diagonal blocks
    expect(A[0][2]).toBe(0);
    expect(A[0][3]).toBe(0);
    expect(A[1][2]).toBe(0);
    expect(A[1][3]).toBe(0);
  });
});

describe("makeNeighborsLattice", () => {
  it("constructs 4-neighbor structure for a 2x2 grid", () => {
    const neighbors = makeNeighborsLattice(2, 2);
    // index mapping:
    // 0 1
    // 2 3
    expect(neighbors.length).toBe(4);

    // node 0: right (1), down (2)
    expect(new Set(neighbors[0])).toEqual(new Set([1, 2]));

    // node 1: left (0), down (3)
    expect(new Set(neighbors[1])).toEqual(new Set([0, 3]));

    // node 2: up (0), right (3)
    expect(new Set(neighbors[2])).toEqual(new Set([0, 3]));

    // node 3: up (1), left (2)
    expect(new Set(neighbors[3])).toEqual(new Set([1, 2]));
  });
});

describe("makeBlockAvg", () => {
  it("averages neighbors with 1/N and identity within each block", () => {
    const n = 2;
    const numBlocks = n * n;
    const neighbors = makeNeighborsLattice(n, n);
    const A = makeBlockAvg(numBlocks, 2, neighbors);

    // For 2x2, each interior node has 2 neighbors; rows should
    // sum to 1 in 2x2 blocks when there are neighbors
    const dim = numBlocks * 2;
    for (let b = 0; b < numBlocks; b++) {
      const neighCount = neighbors[b].length;
      if (neighCount === 0) continue;
      for (let i = 0; i < 2; i++) {
        const row = b * 2 + i;
        const sum = A[row].reduce((acc, v) => acc + v, 0);
        // allow tiny numerical error, but this is exact arithmetic
        expect(sum).toBeCloseTo(1, 10);
      }
    }
  });
});

describe("matVecMul and simulate", () => {
  it("multiplies matrix and vector correctly", () => {
    const A: Mat = [
      [1, 2],
      [3, 4],
    ];
    const x: Vec = [1, -1];
    const y = matVecMul(A, x);
    // y = [1*1 + 2*(-1), 3*1 + 4*(-1)] = [-1, -1]
    expect(y).toEqual([-1, -1]);
  });

  it("simulate with identity matrix keeps state constant", () => {
    const I: Mat = [
      [1, 0],
      [0, 1],
    ];
    const p0: Vec = [0.3, 0.7];
    const traj = simulate(I, p0, 3);
    expect(traj.length).toBe(4); // 0..3
    for (const p of traj) {
      expect(p).toEqual(p0);
    }
  });
});

describe("blocksToVec", () => {
  it("maps t=1 to [1,0] and t=-1 to [0,1] for each block", () => {
    const numBlocks = 3;
    const tValues = [1, 0, -1]; // three blocks
    const v = blocksToVec(tValues, numBlocks, 2);

    // block 0: t=1 -> [1,0]
    expect(v[0]).toBeCloseTo(1);
    expect(v[1]).toBeCloseTo(0);

    // block 1: t=0 -> [0.5, 0.5]
    expect(v[2]).toBeCloseTo(0.5);
    expect(v[3]).toBeCloseTo(0.5);

    // block 2: t=-1 -> [0,1]
    expect(v[4]).toBeCloseTo(0);
    expect(v[5]).toBeCloseTo(1);
  });
});

describe("blockColor", () => {
  it("produces red for [1,0] and blue for [0,1] and white for [0.5,0.5]", () => {
    // one block only
    const vRed: Vec = [1, 0];
    const vBlue: Vec = [0, 1];
    const vWhite: Vec = [0.5, 0.5];

    const cRed = blockColor(vRed, 0, 2);
    const cBlue = blockColor(vBlue, 0, 2);
    const cWhite = blockColor(vWhite, 0, 2);

    expect(cRed).toBe("rgb(255, 0, 0)");
    expect(cBlue).toBe("rgb(0, 0, 255)");
    expect(cWhite).toBe("rgb(255, 255, 255)");
  });
});

describe("DynamicalSystemSimulator component", () => {
  it("renders headings and initial controls", () => {
    render(<DynamicalSystemSimulator />);

    // main title
    expect(
      screen.getByRole("heading", { name: /Dynamical System Simulator/i })
    ).toBeInTheDocument();

    // parameter labels
    // expect(screen.getByText(/n \(lattice size\)/i)).toBeInTheDocument();
    // expect(screen.getByText(/^T$/)).toBeInTheDocument();
    // expect(screen.getByText(/^h$/)).toBeInTheDocument();
    // expect(screen.getByText(/^J$/)).toBeInTheDocument();
    // expect(screen.getByText(/Steps/)).toBeInTheDocument();

    // sections
    expect(screen.getByText(/Initial State/)).toBeInTheDocument();
    expect(screen.getByText(/Ising-style Visualization/)).toBeInTheDocument();
    expect(screen.getByText(/Trajectory/)).toBeInTheDocument();
  });
});
