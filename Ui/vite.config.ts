import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

const CRUNCHY_REST = process.env.CRUNCHY_REST ?? "";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "~": path.resolve(__dirname, "./src"),
    },
  },
  define: {
    __CRUNCHY_REST__: JSON.stringify(CRUNCHY_REST),
  },
  server: {
    proxy: {
      "/api": {
        target: process.env.NOTION_SERVER_URL ?? "http://localhost:3001",
        changeOrigin: true,
      },
    },
  },
});
