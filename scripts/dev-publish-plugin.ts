import { execFile } from "node:child_process";
import { promises as fs } from "node:fs";
import path from "node:path";
import { promisify } from "node:util";
import type { Plugin } from "vite";

const execFileAsync = promisify(execFile);

const SLUG_PATTERN = /^[a-z0-9][a-z0-9-]*$/;
const REPO_ROOT = path.resolve(process.cwd());
const POSTS_DIR = path.join(REPO_ROOT, "src", "content", "posts");

async function publishPost(slug: string) {
  if (!SLUG_PATTERN.test(slug)) {
    throw new Error(`invalid slug: ${slug}`);
  }

  const filePath = path.join(POSTS_DIR, `${slug}.md`);
  const resolved = path.resolve(filePath);
  if (!resolved.startsWith(POSTS_DIR + path.sep)) {
    throw new Error("path traversal blocked");
  }

  const original = await fs.readFile(resolved, "utf8");
  const replaced = original.replace(/^draft:\s*true\s*$/m, "draft: false");
  if (replaced === original) {
    throw new Error("draft: true line not found — already published?");
  }
  await fs.writeFile(resolved, replaced, "utf8");

  const relPath = path.relative(REPO_ROOT, resolved);
  await execFileAsync("git", ["add", relPath], { cwd: REPO_ROOT });
  await execFileAsync(
    "git",
    ["commit", "-m", `post: publish ${slug}`],
    { cwd: REPO_ROOT },
  );
  await execFileAsync("git", ["push"], { cwd: REPO_ROOT });

  return { slug, file: relPath };
}

export function devPublishPlugin(): Plugin {
  return {
    name: "dev-publish",
    apply: "serve",
    configureServer(server) {
      server.middlewares.use("/__publish", (req, res) => {
        if (req.method !== "POST") {
          res.statusCode = 405;
          res.setHeader("content-type", "application/json");
          res.end(JSON.stringify({ ok: false, error: "POST only" }));
          return;
        }

        const chunks: Buffer[] = [];
        req.on("data", chunk => chunks.push(chunk));
        req.on("end", async () => {
          try {
            const body = JSON.parse(Buffer.concat(chunks).toString("utf8"));
            const slug = String(body?.slug ?? "");
            const result = await publishPost(slug);
            res.statusCode = 200;
            res.setHeader("content-type", "application/json");
            res.end(JSON.stringify({ ok: true, ...result }));
          } catch (err) {
            const message = err instanceof Error ? err.message : String(err);
            res.statusCode = 400;
            res.setHeader("content-type", "application/json");
            res.end(JSON.stringify({ ok: false, error: message }));
          }
        });
      });
    },
  };
}
