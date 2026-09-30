// Files for agents that read before they call:
//   /llms.txt                                  what the service is, with links (llmstxt.org)
//   /.well-known/agent-skills/index.json       the skill index (Agent Skills discovery, agentskills.io)
//   /.well-known/agent-skills/<name>/SKILL.md  how to call it, as an Agent Skill
//   /skill.md                                  the same skill, at the path agents often try first
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import express from "express";
import { networkName } from "./payments.js";

const name = process.env.SERVICE_NAME ?? "SkyCast";
// Skill names are lowercase letters, digits and single hyphens, up to 64 characters.
const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 64) || "weather";
const SKILL_PATH = `/.well-known/agent-skills/${slug}/SKILL.md`;

const template = (file) => readFileSync(new URL(`./agent-files/${file}`, import.meta.url), "utf8");
const llms = template("llms.txt");
const skill = template("SKILL.md");

function fill(text, origin) {
  return text
    .replaceAll("{{origin}}", origin)
    .replaceAll("{{name}}", name)
    .replaceAll("{{slug}}", slug)
    .replaceAll("{{network}}", networkName)
    .replaceAll("{{source}}", "https://github.com/tryforgeintel/forge-examples/tree/main/node-express");
}

// Absolute links: PUBLIC_URL when set, else the origin the request came in on.
const originOf = (req) => process.env.PUBLIC_URL?.replace(/\/$/, "") ?? `${req.protocol}://${req.get("host")}`;
const markdown = (res, text) => res.type("text/markdown; charset=utf-8").set("Cache-Control", "public, max-age=300").send(text);

export const agents = express.Router();

agents.get("/llms.txt", (req, res) =>
  res.type("text/plain; charset=utf-8").set("Cache-Control", "public, max-age=300").send(fill(llms, originOf(req))),
);

agents.get([SKILL_PATH, "/skill.md", "/SKILL.md"], (req, res) => markdown(res, fill(skill, originOf(req))));

agents.get("/.well-known/agent-skills/index.json", (req, res) => {
  const body = fill(skill, originOf(req));
  const description = body.match(/^description: (.+)$/m)[1];
  res.set("Cache-Control", "public, max-age=300").json({
    $schema: "https://schemas.agentskills.io/discovery/0.2.0/schema.json",
    skills: [
      {
        name: slug,
        type: "skill-md",
        description,
        url: SKILL_PATH,
        digest: `sha256:${createHash("sha256").update(body).digest("hex")}`,
      },
    ],
  });
});
