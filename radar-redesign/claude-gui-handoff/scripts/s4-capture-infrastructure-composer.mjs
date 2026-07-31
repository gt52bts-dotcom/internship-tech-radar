#!/usr/bin/env node
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const REQUIRED_VIEW = "infrastructure_composer";

function parseArgs(argv) {
  const args = {
    sharedVia: "conversation",
    userDataDir: ".tmp/aws-console-playwright-profile",
    manualTimeoutMs: 180000,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const key = argv[i];
    const value = argv[i + 1];
    if (!key.startsWith("--")) continue;
    i += 1;
    if (key === "--runtime") args.runtime = value;
    else if (key === "--packet") args.packet = value;
    else if (key === "--output-dir") args.outputDir = value;
    else if (key === "--evidence-output") args.evidenceOutput = value;
    else if (key === "--shared-via") args.sharedVia = value;
    else if (key === "--user-data-dir") args.userDataDir = value;
    else if (key === "--manual-timeout-ms") args.manualTimeoutMs = Number(value);
    else usage(`Unknown argument: ${key}`);
  }
  for (const required of ["runtime", "packet", "outputDir", "evidenceOutput"]) {
    if (!args[required]) usage(`Missing --${required.replace(/[A-Z]/g, (m) => `-${m.toLowerCase()}`)}`);
  }
  if (!["gui", "conversation"].includes(args.sharedVia)) {
    usage("--shared-via must be gui or conversation");
  }
  return args;
}

function usage(error) {
  if (error) console.error(error);
  console.error(`
Usage:
  node scripts/s4-capture-infrastructure-composer.mjs \\
    --runtime .\\out\\run\\s4-runtime.json \\
    --packet .\\out\\run\\s4-console-review-packet.json \\
    --output-dir .\\out\\run\\s4-console-review\\<run-id> \\
    --evidence-output .\\out\\run\\s4-console-review\\<run-id>\\s4-console-review-evidence.json \\
    --shared-via conversation

Install Playwright first when needed:
  npm init -y
  npm install --save-dev playwright
  npx playwright install chromium
`);
  process.exit(2);
}

async function loadPlaywright() {
  try {
    return await import("playwright");
  } catch (error) {
    console.error("Playwright is not installed for this workspace.");
    console.error("Run: npm install --save-dev playwright && npx playwright install chromium");
    throw error;
  }
}

function readJson(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

function sha256(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

async function waitForConsoleReady(page, timeoutMs) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const title = await page.title().catch(() => "");
    const url = page.url();
    if (!/signin|login|auth/i.test(url) && /AWS|CloudFormation|Infrastructure|Composer/i.test(title + " " + url)) {
      return;
    }
    await page.waitForTimeout(2000);
  }
  throw new Error("AWS Console did not become ready before the manual login timeout.");
}

async function clickInfrastructureComposer(page) {
  const candidates = [
    page.getByRole("link", { name: /Infrastructure Composer/i }),
    page.getByRole("button", { name: /Infrastructure Composer/i }),
    page.getByText(/Infrastructure Composer/i),
  ];
  for (const candidate of candidates) {
    try {
      await candidate.first().click({ timeout: 5000 });
      await page.waitForLoadState("domcontentloaded", { timeout: 30000 }).catch(() => {});
      return true;
    } catch {
      // AWS Console labels and navigation differ by page state; try the next locator.
    }
  }
  return false;
}

async function canvasClip(page) {
  const handles = await page.locator("canvas, svg, [data-testid*='canvas' i], [class*='canvas' i]").elementHandles();
  const viewport = page.viewportSize() || { width: 1440, height: 900 };
  let best = null;
  for (const handle of handles) {
    const box = await handle.boundingBox().catch(() => null);
    if (!box || box.width < 300 || box.height < 220) continue;
    const area = box.width * box.height;
    if (!best || area > best.area) best = { ...box, area };
  }
  if (best) {
    return {
      x: Math.max(0, Math.floor(best.x)),
      y: Math.max(0, Math.floor(best.y)),
      width: Math.min(viewport.width, Math.floor(best.width)),
      height: Math.min(viewport.height, Math.floor(best.height)),
    };
  }
  return {
    x: Math.floor(viewport.width * 0.16),
    y: Math.floor(viewport.height * 0.18),
    width: Math.floor(viewport.width * 0.68),
    height: Math.floor(viewport.height * 0.68),
  };
}

async function hideConsoleChrome(page) {
  await page.addStyleTag({
    content: `
      header,
      nav,
      [role="banner"],
      [data-testid*="awsc-nav" i],
      [data-testid*="account" i],
      [aria-label*="Account" i],
      [aria-label*="Support" i],
      [class*="awsc-header" i],
      [class*="nav" i] {
        visibility: hidden !important;
      }
    `,
  }).catch(() => {});
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const runtime = readJson(args.runtime);
  const packet = readJson(args.packet);
  if (runtime.status !== "awaiting_console_review") {
    throw new Error("Runtime must be awaiting_console_review before Console capture.");
  }
  if (packet.run_id !== runtime.run_id) {
    throw new Error("Packet and runtime run_id do not match.");
  }

  const target = packet.review_target || {};
  const composerUrl = target.composer_url || `https://${target.target_region}.console.aws.amazon.com/composer/home?region=${target.target_region}`;
  const stackUrl = target.cloudformation_stack_url;
  const { chromium } = await loadPlaywright();
  mkdirSync(args.outputDir, { recursive: true });
  mkdirSync(resolve(args.userDataDir), { recursive: true });

  const browser = await chromium.launchPersistentContext(resolve(args.userDataDir), {
    headless: false,
    viewport: { width: 1440, height: 1000 },
  });
  const page = browser.pages()[0] || await browser.newPage();
  if (stackUrl) {
    await page.goto(stackUrl, { waitUntil: "domcontentloaded", timeout: 60000 });
    await waitForConsoleReady(page, args.manualTimeoutMs);
    const clicked = await clickInfrastructureComposer(page);
    if (!clicked) {
      await page.goto(composerUrl, { waitUntil: "domcontentloaded", timeout: 60000 });
    }
  } else {
    await page.goto(composerUrl, { waitUntil: "domcontentloaded", timeout: 60000 });
    await waitForConsoleReady(page, args.manualTimeoutMs);
  }
  await page.waitForTimeout(5000);

  const outputPng = resolve(args.outputDir, "infrastructure-composer.png");
  await hideConsoleChrome(page);
  await page.screenshot({ path: outputPng, clip: await canvasClip(page) });
  await browser.close();

  const capturedAt = new Date().toISOString();
  const evidence = {
    schema_version: "s4.console-review-evidence.v1",
    run_id: runtime.run_id,
    generated_by: "scripts/s4-capture-infrastructure-composer.mjs",
    review_target: {
      run_id: runtime.run_id,
      stack_name: target.stack_name || runtime.deployment?.stack_name,
      target_region: target.target_region || runtime.deployment?.target_region,
      recipe: target.recipe || runtime.deployment?.recipe,
    },
    capture_contract: {
      redaction_order: "hide_console_chrome_before_capture_then_hash_redacted_png",
      redacted_before_hash: true,
      hash_scope: "redacted_png",
      automated_image_understanding: false,
      human_confirmation_record_only: true,
    },
    screenshots: [
      {
        view: REQUIRED_VIEW,
        screenshot_ref: outputPng,
        sha256: sha256(outputPng),
        captured_at: capturedAt,
        shared_via: args.sharedVia,
        redacted: true,
        hash_scope: "redacted_png",
        stack_name: target.stack_name || runtime.deployment?.stack_name,
        target_region: target.target_region || runtime.deployment?.target_region,
      },
    ],
  };
  mkdirSync(dirname(resolve(args.evidenceOutput)), { recursive: true });
  writeFileSync(args.evidenceOutput, `${JSON.stringify(evidence, null, 2)}\n`, "utf8");

  const imageUrl = pathToFileURL(outputPng).href;
  console.log(JSON.stringify({
    status: "captured",
    run_id: runtime.run_id,
    screenshot: outputPng,
    evidence: resolve(args.evidenceOutput),
    show_to_human_markdown: `![Infrastructure Composer canvas](${imageUrl})`,
    privacy_note: "The image was captured after hiding Console chrome and the SHA-256 is for the redacted PNG. The script does not understand screenshot pixels; a named human must confirm the visible stack canvas.",
    next_question: "是否確認依此 Console 截圖清除這次 PoC？",
  }, null, 2));
}

main().catch((error) => {
  console.error(error?.message || String(error));
  process.exit(1);
});
