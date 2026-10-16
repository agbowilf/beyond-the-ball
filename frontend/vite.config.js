import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Scenario and insight JSON live in ../scenarios, outside the Vite root.
export default defineConfig({
  plugins: [react()],
  server: { fs: { allow: ['..'] } },
})
