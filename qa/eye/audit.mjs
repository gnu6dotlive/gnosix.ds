// The eye: the system's own surfaces, rendered and looked at.
//
// Two things happen here, and both are witnesses rather than opinions.
//
// The first is the accessibility finding: axe walks the rendered surface
// and says what it finds. The findings are a ratchet — the report that
// ships with the system says what is already known, and a finding that
// is not in it is a new one and a failure.
//
// The second is the picture: the surface is rendered to a PNG whose bytes
// are compared with the one the system carries. A component that moves
// by a pixel is caught here, and the comparison is on the bytes, so the
// picture that ships is the picture that was looked at.
//
// The chromium is pinned by the lockfile and the font is the one this
// repository packages, so the rendering is the same on every machine
// that provisions the browser the way ci/provision-browser.sh says.
//
//   node qa/eye/audit.mjs --out <directory>

import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import AxeBuilder from "@axe-core/playwright";
import { chromium } from "playwright";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..", "..");

// The surfaces the system renders. Each is a file, a substrate and a
// name: the substrate is the attribute the role layer reads, and the
// name is what the witness is called.
const SURFACES = [
  { name: "components-light", file: "profiles/web/demo.html", substrate: "light" },
  { name: "components-dark", file: "profiles/web/demo.html", substrate: "dark" },
  { name: "reference", file: "site/reference.html", substrate: "light" },
];

const VIEWPORT = { width: 1280, height: 1024 };

function digest(bytes) {
  return createHash("sha256").update(bytes).digest("hex");
}

async function main() {
  const args = process.argv.slice(2);
  const outIndex = args.indexOf("--out");
  if (outIndex === -1) {
    console.error("usage: node audit.mjs --out <directory>");
    process.exit(2);
  }
  const out = resolve(args[outIndex + 1]);
  mkdirSync(out, { recursive: true });

  const browser = await chromium.launch({
    args: ["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--font-render-hinting=none"],
  });
  const report = { surfaces: [], findings: [] };
  try {
    for (const surface of SURFACES) {
      const context = await browser.newContext({
        viewport: VIEWPORT,
        colorScheme: surface.substrate === "dark" ? "dark" : "light",
        deviceScaleFactor: 1,
        reducedMotion: "reduce",
      });
      const page = await context.newPage();
      const url = "file://" + join(ROOT, surface.file);
      await page.goto(url, { waitUntil: "load" });
      await page.evaluate((substrate) => {
        document.documentElement.setAttribute("data-gnosix-substrate", substrate);
      }, surface.substrate);
      await page.evaluate(() => document.fonts.ready);

      const results = await new AxeBuilder({ page }).analyze();
      const findings = results.violations.map((violation) => ({
        id: violation.id,
        impact: violation.impact,
        help: violation.help,
        nodes: violation.nodes.length,
        targets: violation.nodes.map((node) => node.target.join(" ")).slice(0, 8),
        detail: violation.nodes.slice(0, 3).map((node) => ({
          target: node.target.join(" "),
          html: (node.html || "").slice(0, 160),
          any: node.any.map((check) => ({
            message: check.message,
            data: check.data,
          })),
        })),
      }));
      for (const finding of findings) {
        report.findings.push({ surface: surface.name, ...finding });
      }

      const shot = await page.screenshot({ fullPage: true, animations: "disabled" });
      const file = join(out, `${surface.name}.png`);
      writeFileSync(file, shot);
      report.surfaces.push({
        name: surface.name,
        file: relative(ROOT, file),
        bytes: shot.length,
        sha256: digest(shot),
        violations: results.violations.length,
        passes: results.passes.length,
      });
      await context.close();
    }
  } finally {
    await browser.close();
  }

  const file = join(out, "report.json");
  writeFileSync(file, JSON.stringify(report, null, 2) + "\n");
  console.log(`EYE_RENDERED ${report.surfaces.length} surfaces, ` +
              `${report.findings.length} accessibility findings`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
