import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

export default defineConfig({
  plugins: [react()],
  // IMPORTANT: relative base so the bundle loads correctly at /ising-mdp/
  base: "./"
});
