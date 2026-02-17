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

    const block0: Mat = [
      [A[0][0], A[0][1]],
      [A[1][0], A[1][1]],
    ];
    const block1: Mat = [
      [A[2][2], A[2][3]],
      [A[3][2], A[3][3]],
    ];

    expect(block0).toEqual([
      [1, 1],
      [1, 1],
    ]);
    expect(block1).toEqual([
      [1, 1],
      [1, 1],
    ]);

    expect(A[0][2]).toBe(0);
    expect(A[0][3]).toBe(0);
    expect(A[1][2]).toBe(0);
    expect(A[1][3]).toBe(0);
  });
});

describe("makeNeighborsLattice", () => {
  it("constructs 4-neighbor structure for a 2x2 grid", () => {
    const neighbors = makeNeighborsLattice(2, 2);
    expect(neighbors.length).toBe(4);
    expect(new Set(neighbors[0])).toEqual(new Set([1, 2]));
    expect(new Set(neighbors[1])).toEqual(new Set([0, 3]));
    expect(new Set(neighbors[2])).toEqual(new Set([0, 3]));
    expect(new Set(neighbors[3])).toEqual(new Set([1, 2]));
  });
});

describe("makeBlockAvg", () => {
  it("averages neighbors with 1/N and identity within each block", () => {
    const n = 2;
    const numBlocks = n * n;
    const neighbors = makeNeighborsLattice(n, n);
    const A = makeBlockAvg(numBlocks, 2, neighbors);

    for (let b = 0; b < numBlocks; b++) {
      const neighCount = neighbors[b].length;
      if (neighCount === 0) continue;
      for (let i = 0; i < 2; i++) {
        const row = b * 2 + i;
        const sum = A[row].reduce((acc, v) => acc + v, 0);
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
    expect(y).toEqual([-1, -1]);
  });

  it("simulate with identity matrix keeps state constant", () => {
    const I: Mat = [
      [1, 0],
      [0, 1],
    ];
    const p0: Vec = [0.3, 0.7];
    const traj = simulate(I, p0, 3);
    expect(traj.length).toBe(4);
    for (const p of traj) {
      expect(p).toEqual(p0);
    }
  });
});

describe("blocksToVec", () => {
  it("maps t=1 to [1,0] and t=-1 to [0,1] for each block", () => {
    const numBlocks = 3;
    const tValues = [1, 0, -1];
    const v = blocksToVec(tValues, numBlocks, 2);

    expect(v[0]).toBeCloseTo(1);
    expect(v[1]).toBeCloseTo(0);
    expect(v[2]).toBeCloseTo(0.5);
    expect(v[3]).toBeCloseTo(0.5);
    expect(v[4]).toBeCloseTo(0);
    expect(v[5]).toBeCloseTo(1);
  });
});

describe("blockColor", () => {
  it("produces red for [1,0] and blue for [0,1] and white for [0.5,0.5]", () => {
    const cRed = blockColor([1, 0], 0, 2);
    const cBlue = blockColor([0, 1], 0, 2);
    const cWhite = blockColor([0.5, 0.5], 0, 2);

    expect(cRed).toBe("rgb(255, 0, 0)");
    expect(cBlue).toBe("rgb(0, 0, 255)");
    expect(cWhite).toBe("rgb(255, 255, 255)");
  });
});

describe("DynamicalSystemSimulator component", () => {
  it("renders four simulation cards", () => {
    render(<DynamicalSystemSimulator />);

    expect(screen.getByRole("heading", { name: /GitHub Pages edition/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Simulation A/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Simulation B/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Simulation C/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Simulation D/i })).toBeInTheDocument();
  });
});
