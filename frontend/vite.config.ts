// Vite build configuration for the React frontend. Registers the React plugin
// for HMR and JSX transform during dev and production builds.
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({ plugins: [react()] })
