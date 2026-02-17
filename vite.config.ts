import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

export default defineConfig({
  plugins: [react()],
  // IMPORTANT: relative base so bundle assets resolve from /docs on GitHub Pages
  base: "./",
  build: {
    outDir: "docs",
    emptyOutDir: true,
  },
});
