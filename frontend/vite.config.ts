import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite"; // 🎯 Add this import

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(), // 🎯 Add this plugin
  ],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": {
        target: "http://tennis_api:8000",
        changeOrigin: true,
      },
    },
  },
});
