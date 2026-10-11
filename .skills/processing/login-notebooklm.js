import { chromium } from 'playwright';

(async () => {
  const profilePath = 'C:\\Users\\flier\\AppData\\Local\\notebooklm-mcp\\Data\\chrome_profile';
  console.log(`\n===========================================================`);
  console.log(`LAUNCHING VISIBLE CHROME FOR NOTEBOOKLM AUTHENTICATION`);
  console.log(`Profile Path: ${profilePath}`);
  console.log(`===========================================================\n`);

  try {
    const context = await chromium.launchPersistentContext(profilePath, {
      headless: false,
      channel: 'chrome', // Uses system Google Chrome
      viewport: null,    // Maximized viewport
    });

    const page = await context.newPage();
    console.log("Navigating to https://notebooklm.google.com/ ...\n");
    await page.goto('https://notebooklm.google.com/');

    console.log("👉 INSTRUCTIONS:");
    console.log("1. In the Chrome window that just opened, sign in to your Google Account.");
    console.log("2. Make sure you can see your notebooks (including 'Proyecto Argentina').");
    console.log("3. Once fully logged in, CLOSE the Chrome browser window.");
    console.log("4. This script will save your session and exit automatically.\n");

    // Monitor page close to exit cleanly
    page.on('close', async () => {
      console.log("Browser window closed. Saving session state...");
      await context.close();
      console.log("Authentication state saved successfully! You can now use the NotebookLM MCP.");
      process.exit(0);
    });

    // Also handle graceful exit if user cancels in terminal
    process.on('SIGINT', async () => {
      console.log("\nInterrupted. Saving session and exiting...");
      await context.close();
      process.exit(0);
    });

  } catch (error) {
    console.error("Failed to launch Chrome:", error);
    process.exit(1);
  }
})();
