// main.ts — entrypoint for make.fun news-image-20261125.
// Copies the pre-rendered entry.png (drawn by render.py) into the
// grader's output directory. Standard library only, no network,
// deterministic: a pure file copy, so two runs produce identical bytes.
import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = dirname(fileURLToPath(import.meta.url));
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";

mkdirSync(outDir, { recursive: true });
copyFileSync(join(repoRoot, "entry.png"), join(outDir, "entry.png"));
