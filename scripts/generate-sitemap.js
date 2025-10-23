#!/usr/bin/env node

/**
 * Script to generate static sitemap.xml file
 * This creates a proper XML sitemap that can be served directly
 */

const fs = require("fs");
const path = require("path");

// Read the routes file to get climate variables
const routesPath = path.join(__dirname, "../client/src/app/app.routes.ts");
const routesContent = fs.readFileSync(routesPath, "utf8");

// Extract climate variable routes from the routes file (excluding comments)
const climateVariableMatches = routesContent.match(
  /^\s*\[ClimateVarKey\.(\w+)\]:\s*{\s*path:\s*['"`]([^'"`]+)['"`],\s*title:\s*['"`]([^'"`]+)['"`]/gm
);

if (!climateVariableMatches) {
  console.error("No climate variable routes found in app.routes.ts");
  process.exit(1);
}

// Parse the matches
const climateVariables = climateVariableMatches.map((match) => {
  const [, variable, path, title] = match.match(
    /\[ClimateVarKey\.(\w+)\]:\s*{\s*path:\s*['"`]([^'"`]+)['"`],\s*title:\s*['"`]([^'"`]+)['"`]/
  );
  return { variable, path, title };
});

// Generate sitemap XML
const baseUrl = "https://openclimatemap.org";
const currentDate = new Date().toISOString().split("T")[0];

let sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n';
sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n';

// Main pages
const mainPages = [
  { path: "", priority: "1.0", changefreq: "daily" },
  { path: "about", priority: "0.8", changefreq: "monthly" },
  { path: "seasons", priority: "0.8", changefreq: "monthly" },
  { path: "climate-scenarios", priority: "0.8", changefreq: "monthly" },
  { path: "climate-predictions", priority: "0.8", changefreq: "monthly" },
  { path: "climate-matrix", priority: "0.8", changefreq: "monthly" },
];

mainPages.forEach((page) => {
  sitemap += "  <url>\n";
  sitemap += `    <loc>${baseUrl}/${page.path}</loc>\n`;
  sitemap += `    <lastmod>${currentDate}</lastmod>\n`;
  sitemap += `    <changefreq>${page.changefreq}</changefreq>\n`;
  sitemap += `    <priority>${page.priority}</priority>\n`;
  sitemap += "  </url>\n";
});

// Climate variable pages
climateVariables.forEach((variable) => {
  sitemap += "  <url>\n";
  sitemap += `    <loc>${baseUrl}/${variable.path}</loc>\n`;
  sitemap += `    <lastmod>${currentDate}</lastmod>\n`;
  sitemap += `    <changefreq>monthly</changefreq>\n`;
  sitemap += `    <priority>0.7</priority>\n`;
  sitemap += "  </url>\n";
});

sitemap += "</urlset>";

// Write the sitemap to the public directory
const sitemapPath = path.join(__dirname, "../client/public/sitemap.xml");
fs.writeFileSync(sitemapPath, sitemap);

console.log(
  `✅ Generated sitemap.xml with ${climateVariables.length} climate variable routes`
);
console.log("Climate variables included:");
climateVariables.forEach((variable) => {
  console.log(`  - ${variable.title} (/${variable.path})`);
});
