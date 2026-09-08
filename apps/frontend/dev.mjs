/**
 * Custom dev watcher — excludes SQLite files, logs, and build artifacts
 * to prevent infinite restart loops.
 */
import { spawn } from "child_process";
import chokidar from "chokidar";

let serverProcess = null;

function startServer() {
  if (serverProcess) {
    console.log("\x1b[33m[watcher] Restarting server...\x1b[0m");
    serverProcess.kill("SIGTERM");
    // Force kill after 2s if still alive
    setTimeout(() => {
      try { serverProcess.kill("SIGKILL"); } catch {}
    }, 2000);
  }

  serverProcess = spawn("npx", ["tsx", "server.ts"], {
    stdio: "inherit",
    env: { ...process.env, NODE_ENV: "development" },
  });

  serverProcess.on("exit", (code, signal) => {
    if (signal !== "SIGTERM" && signal !== "SIGKILL") {
      console.log(`\x1b[31m[watcher] Server exited with code ${code}. Waiting for file changes...\x1b[0m`);
    }
  });
}

// Debounce: ignore rapid successive changes
let debounceTimer = null;
function debouncedRestart() {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => startServer(), 400);
}

// Watch patterns: only restart on relevant source changes
const watchPaths = ["server.ts", "src"];

const watcher = chokidar.watch(watchPaths, {
  ignoreInitial: true,
  ignored: [
    // SQLite database files
    "**/*.db",
    "**/*.db-journal",
    "**/*.db-wal",
    "**/*.db-shm",
    "**/*.sqlite",
    "**/*.sqlite-journal",
    // Log files
    "**/*.log",
    "**/logs/**",
    // Build/dist artifacts
    "**/dist/**",
    "**/.vite/**",
    "**/node_modules/**",
    // Lock files and configs that change frequently
    "**/*.lock",
    "**/.env",
    "**/.env.local",
    "**/package-lock.json",
    "**/pnpm-lock.yaml",
    // Temporary files
    "**/*.tmp",
    "**/*.temp",
    "**/.DS_Store",
    "**/Thumbs.db",
  ],
  awaitWriteFinish: {
    stabilityThreshold: 500,
    pollInterval: 100,
  },
});

watcher.on("change", (filePath) => {
  console.log(`\x1b[36m[watcher] File changed: ${filePath}\x1b[0m`);
  debouncedRestart();
});

watcher.on("add", (filePath) => {
  // Only restart on .ts/.js/.mjs/.json additions in src/
  if (/\.(ts|tsx|js|mjs|json)$/.test(filePath) && !filePath.includes("node_modules")) {
    console.log(`\x1b[36m[watcher] File added: ${filePath}\x1b[0m`);
    debouncedRestart();
  }
});

console.log("\x1b[32m[watcher] Watching for changes (excluding *.db, *.log, dist/...)\x1b[0m");
startServer();
