import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { stripVTControlCharacters } from "node:util";

test("the Next launcher disables telemetry without a caller opt-out", () => {
  const cwd = mkdtempSync(join(tmpdir(), "family-food-telemetry-"));
  const env = { ...process.env, CI: "1", FORCE_COLOR: "0", NEXT_TELEMETRY_DEBUG: "1" };
  delete env.NEXT_TELEMETRY_DISABLED;
  const status = path => stripVTControlCharacters(execFileSync(process.execPath, [
    fileURLToPath(new URL(path, import.meta.url)), "telemetry", "status",
  ], { cwd, env, encoding: "utf8" }));
  try {
    assert.match(status("../node_modules/next/dist/bin/next"), /Status:\s+Enabled/);
    assert.match(status("../run-next.mjs"), /Status:\s+Disabled/);
  } finally {
    rmSync(cwd, { recursive: true, force: true });
  }
});
