# Ising MDP simulator

This repo now targets **GitHub Pages via `/docs`**.

## Local development

```bash
npm install
npm run dev
```

## Build for Pages

```bash
npm run build
```

The Vite build output is written to `docs/`. Commit that folder, then in GitHub set:

- **Settings → Pages → Source**: `Deploy from a branch`
- **Branch**: `main`
- **Folder**: `/docs`

The app renders four independent simulation panels, each with isolated controls and initial-state tuning.
