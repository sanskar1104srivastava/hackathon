import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// During local development, /v1 calls go to the FastAPI backend on port 8000.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { '/v1': 'http://localhost:8000' },
  },
})
