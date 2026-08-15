import { expect, test } from "bun:test";
import { existsSync, mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { summarize } from "./gen-reference.mjs";

const SCRIPT = join(import.meta.dir, "gen-reference.mjs");

test("keeps the first sentence, drops trigger text", () => {
  expect(summarize("Create and push semver version tags. Use when tagging a commit.")).toBe(
    "Create and push semver version tags.",
  );
});

test("keeps a description that is a single sentence", () => {
  const only = "Restate the last message in plain human language, with no jargon.";
  expect(summarize(only)).toBe(only);
});

test("does not break on English abbreviations", () => {
  expect(summarize("Deploy to a CDN, e.g. Cloudflare Pages. Use when shipping.")).toBe(
    "Deploy to a CDN, e.g. Cloudflare Pages.",
  );
  expect(summarize("Compare a repo vs. Google's style guide. Use when reviewing.")).toBe(
    "Compare a repo vs. Google's style guide.",
  );
  expect(summarize("Ship it, i.e. Merge the branch. Use when done.")).toBe("Ship it, i.e. Merge the branch.");
  expect(summarize("Ask Dr. Smith to review. Use when unsure.")).toBe("Ask Dr. Smith to review.");
  expect(summarize("Ask Prof. Smith to review. Use when unsure.")).toBe("Ask Prof. Smith to review.");
  expect(summarize("Written by a Ph.D. Reviewer signs off. Use when unsure.")).toBe(
    "Written by a Ph.D. Reviewer signs off.",
  );
  expect(summarize("Takes approx. Two hours. Use when planning.")).toBe("Takes approx. Two hours.");
});

test("does not break on Spanish abbreviations", () => {
  expect(summarize("Despliega en un CDN, p. ej. Cloudflare Pages. Usar al publicar.")).toBe(
    "Despliega en un CDN, p. ej. Cloudflare Pages.",
  );
  expect(summarize("Consulta a la Sra. Zanelli. Usar si hay dudas.")).toBe("Consulta a la Sra. Zanelli.");
  expect(summarize("Consulta a la Dra. Zanelli. Usar si hay dudas.")).toBe("Consulta a la Dra. Zanelli.");
  expect(summarize("Revisa el art. Tercero del reglamento. Usar al auditar.")).toBe(
    "Revisa el art. Tercero del reglamento.",
  );
  expect(summarize("Vence en ene. Febrero ya es tarde. Usar al planificar.")).toBe(
    "Vence en ene. Febrero ya es tarde.",
  );
});

test("treats an accented capital or ¿ as a sentence start", () => {
  expect(summarize("Ordena las tareas. Última revisión incluida.")).toBe("Ordena las tareas.");
  expect(summarize("Ordena las tareas. ¿Cuándo? Usar al planificar.")).toBe("Ordena las tareas.");
});

test("an all-caps acronym still ends a sentence", () => {
  expect(summarize("Drive a slice to a merged PR. Use when shipping.")).toBe("Drive a slice to a merged PR.");
});

test("folds a multi-line YAML description onto one line", () => {
  expect(summarize("Forces the laziest\nsolution that works. Use when coding.")).toBe(
    "Forces the laziest solution that works.",
  );
});

test("updates an existing category README through the CLI", () => {
  const cwd = mkdtempSync(join(tmpdir(), "skill-reference-"));
  try {
    mkdirSync(join(cwd, "skills/productivity/ship-slice"), { recursive: true });
    writeFileSync(join(cwd, "skills/productivity/README.md"), "# Productivity\n\nHandwritten introduction.\n");
    writeFileSync(
      join(cwd, "skills/productivity/ship-slice/SKILL.md"),
      "---\nname: ship-slice\ndescription: Ship a slice safely. Use when delivering work.\n---\n",
    );

    const result = Bun.spawnSync([process.execPath, SCRIPT], { cwd });

    expect(result.exitCode).toBe(0);
    expect(readFileSync(join(cwd, "skills/productivity/README.md"), "utf8")).toBe(
      "# Productivity\n\nHandwritten introduction.\n\n" +
        "<!-- BEGIN GENERATED SKILL REFERENCE -->\n" +
        "- **[ship-slice](./ship-slice/SKILL.md)** — Ship a slice safely.\n" +
        "<!-- END GENERATED SKILL REFERENCE -->\n",
    );
  } finally {
    rmSync(cwd, { recursive: true, force: true });
  }
});

test("updates existing subcategory READMEs without creating missing ones", () => {
  const cwd = mkdtempSync(join(tmpdir(), "skill-reference-"));
  try {
    mkdirSync(join(cwd, "skills/workflows/commit"), { recursive: true });
    mkdirSync(join(cwd, "skills/workflows/release/deploy"), { recursive: true });
    mkdirSync(join(cwd, "skills/workflows/unindexed/archive"), { recursive: true });
    writeFileSync(join(cwd, "skills/workflows/README.md"), "# Workflows\n");
    writeFileSync(join(cwd, "skills/workflows/release/README.md"), "# Release\n");
    writeFileSync(
      join(cwd, "skills/workflows/commit/SKILL.md"),
      "---\nname: commit\ndescription: Commit the work. Use after validation.\n---\n",
    );
    writeFileSync(
      join(cwd, "skills/workflows/release/deploy/SKILL.md"),
      "---\nname: deploy\ndescription: Deploy the work. Use after merging.\n---\n",
    );
    writeFileSync(
      join(cwd, "skills/workflows/unindexed/archive/SKILL.md"),
      "---\nname: archive\ndescription: Archive old work. Use during cleanup.\n---\n",
    );

    const result = Bun.spawnSync([process.execPath, SCRIPT], { cwd });

    expect({
      exitCode: result.exitCode,
      category: readFileSync(join(cwd, "skills/workflows/README.md"), "utf8"),
      subcategory: readFileSync(join(cwd, "skills/workflows/release/README.md"), "utf8"),
      createdMissingReadme: existsSync(join(cwd, "skills/workflows/unindexed/README.md")),
    }).toEqual({
      exitCode: 0,
      category:
        "# Workflows\n\n" +
        "<!-- BEGIN GENERATED SKILL REFERENCE -->\n" +
        "- **[commit](./commit/SKILL.md)** — Commit the work.\n\n" +
        "## Release\n\n" +
        "- **[deploy](./release/deploy/SKILL.md)** — Deploy the work.\n\n" +
        "## Unindexed\n\n" +
        "- **[archive](./unindexed/archive/SKILL.md)** — Archive old work.\n" +
        "<!-- END GENERATED SKILL REFERENCE -->\n",
      subcategory:
        "# Release\n\n" +
        "<!-- BEGIN GENERATED SKILL REFERENCE -->\n" +
        "- **[deploy](./deploy/SKILL.md)** — Deploy the work.\n" +
        "<!-- END GENERATED SKILL REFERENCE -->\n",
      createdMissingReadme: false,
    });
  } finally {
    rmSync(cwd, { recursive: true, force: true });
  }
});

test("check mode reports a stale category README", () => {
  const cwd = mkdtempSync(join(tmpdir(), "skill-reference-"));
  try {
    mkdirSync(join(cwd, "skills/productivity/ship-slice"), { recursive: true });
    writeFileSync(join(cwd, "skills/productivity/README.md"), "# Productivity\n");
    writeFileSync(
      join(cwd, "skills/productivity/ship-slice/SKILL.md"),
      "---\nname: ship-slice\ndescription: Ship a slice safely. Use when delivering work.\n---\n",
    );
    expect(Bun.spawnSync([process.execPath, SCRIPT], { cwd }).exitCode).toBe(0);
    const readme = join(cwd, "skills/productivity/README.md");
    writeFileSync(readme, readFileSync(readme, "utf8").replace("Ship a slice safely.", "Stale summary."));

    const result = Bun.spawnSync([process.execPath, SCRIPT, "--check"], { cwd, stderr: "pipe" });

    expect({ exitCode: result.exitCode, stderr: result.stderr.toString() }).toEqual({
      exitCode: 1,
      stderr: "skills/productivity/README.md is stale. Run: bun scripts/gen-reference.mjs\n",
    });
  } finally {
    rmSync(cwd, { recursive: true, force: true });
  }
});

test("does not manage a README inside a skill directory", () => {
  const cwd = mkdtempSync(join(tmpdir(), "skill-reference-"));
  try {
    mkdirSync(join(cwd, "skills/productivity/commit"), { recursive: true });
    writeFileSync(join(cwd, "skills/productivity/commit/README.md"), "# Commit internals\n");
    writeFileSync(
      join(cwd, "skills/productivity/commit/SKILL.md"),
      "---\nname: commit\ndescription: Commit the work. Use after validation.\n---\n",
    );

    const result = Bun.spawnSync([process.execPath, SCRIPT], { cwd });

    expect({
      exitCode: result.exitCode,
      readme: readFileSync(join(cwd, "skills/productivity/commit/README.md"), "utf8"),
    }).toEqual({ exitCode: 0, readme: "# Commit internals\n" });
  } finally {
    rmSync(cwd, { recursive: true, force: true });
  }
});
