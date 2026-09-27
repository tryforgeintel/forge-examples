// The free landing page and icons, for people who open the URL in a browser.
import { readFileSync } from "node:fs";
import express from "express";
import { network } from "./payments.js";

const page = readFileSync(new URL("./public/index.html", import.meta.url), "utf8")
  .replaceAll("{{name}}", process.env.SERVICE_NAME ?? "SkyCast")
  .replaceAll("{{accent}}", "#F04B14")
  .replaceAll("{{stack}}", "Node.js and Express")
  .replaceAll("{{network}}", network === "eip155:8453" ? "Base" : network === "eip155:84532" ? "Base Sepolia (testnet)" : network)
  .replaceAll("{{source}}", "https://github.com/tryforgeintel/forge-examples/tree/main/node-express");

export const site = express.Router();
site.get("/", (_req, res) => res.type("html").send(page));
site.use(express.static(new URL("./public", import.meta.url).pathname, { index: false, maxAge: "1d" }));
