import { expect, test } from "bun:test";
import { summarize } from "./gen-reference.mjs";

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
