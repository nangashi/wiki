#!/usr/bin/env node

import { readFileSync } from "node:fs";
import path from "node:path";

if (process.argv.length !== 3) {
  console.error("usage: node textlint-report.mjs <textlint-json>");
  process.exit(2);
}

let reports;
try {
  reports = JSON.parse(readFileSync(process.argv[2], "utf8"));
} catch (error) {
  console.error(`TEXTLINT_EXEC_ERROR JSON出力を解析できませんでした: ${error.message}`);
  process.exit(2);
}

const requiredRules = new Set([
  "ja-technical-writing/no-invalid-control-character",
  "ja-technical-writing/no-zero-width-spaces",
  "ja-technical-writing/no-nfd",
  "ja-technical-writing/no-hankaku-kana",
  "ja-technical-writing/ja-unnatural-alphabet",
  "ja-technical-writing/no-unmatched-pair",
  "ja-technical-writing/no-dropping-the-ra"
]);

const reviewRules = new Set([
  "ja-technical-writing/no-double-negative-ja",
  "ja-technical-writing/ja-no-abusage",
  "@textlint-ja/ai-writing/no-ai-colon-continuation"
]);

const counts = { required: 0, review: 0, info: 0 };

for (const report of reports) {
  for (const message of report.messages) {
    const level = requiredRules.has(message.ruleId)
      ? "required"
      : reviewRules.has(message.ruleId)
        ? "review"
        : "info";
    counts[level] += 1;
    const relativeFile = path.relative(process.cwd(), report.filePath) || report.filePath;
    const summary = String(message.message).replace(/\s+/g, " ").trim();
    console.log(
      `TEXTLINT_${level.toUpperCase()} file=${relativeFile} line=${message.line} column=${message.column} rule=${message.ruleId} message=${summary}`
    );
  }
}

console.log(`TEXTLINT_SUMMARY required=${counts.required} review=${counts.review} info=${counts.info}`);
if (counts.required > 0) process.exit(1);
