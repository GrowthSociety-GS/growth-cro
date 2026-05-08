#!/usr/bin/env node
/* Render a generated GSG HTML file in Playwright and save desktop/mobile proof. */
const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { chromium } = require("playwright");

async function metrics(page, viewport) {
  return await page.evaluate((vp) => {
    const box = (el) => {
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return {
        left: Math.round(r.left),
        right: Math.round(r.right),
        top: Math.round(r.top),
        bottom: Math.round(r.bottom),
        width: Math.round(r.width),
        height: Math.round(r.height),
      };
    };
    const h1s = Array.from(document.querySelectorAll("h1"));
    const heroVisual = document.querySelector(".hero-visual");
    const visualSystem = document.querySelector("[data-visual-system]");
    const visualKinds = Array.from(document.querySelectorAll("[data-visual-kind]"))
      .map((el) => el.getAttribute("data-visual-kind"))
      .filter(Boolean);
    const overflowEls = Array.from(document.querySelectorAll("body *"))
      .map((el) => {
        const r = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);
        return {
          tag: el.tagName.toLowerCase(),
          cls: String(el.className || "").slice(0, 90),
          left: Math.round(r.left),
          right: Math.round(r.right),
          width: Math.round(r.width),
          display: style.display,
        };
      })
      .filter((item) => item.display !== "none" && (item.left < -2 || item.right > window.innerWidth + 2))
      .slice(0, 12);
    const images = Array.from(document.images).map((img) => ({
      src: img.getAttribute("src"),
      complete: img.complete,
      width: img.naturalWidth,
      height: img.naturalHeight,
    }));
    const h1Box = box(h1s[0]);
    const heroBox = box(heroVisual);
    const h1OverlapsHeroVisual = Boolean(
      h1Box && heroBox &&
      h1Box.left < heroBox.right &&
      h1Box.right > heroBox.left &&
      h1Box.top < heroBox.bottom &&
      h1Box.bottom > heroBox.top
    );
    const bodyText = document.body.innerText || "";
    const errors = [];
    if (h1s.length !== 1) errors.push(`h1_count_${h1s.length}`);
    if (!heroVisual) errors.push("missing_hero_visual");
    if (!visualSystem) errors.push("missing_visual_system");
    if (!visualKinds.length) errors.push("missing_visual_kinds");
    if (document.documentElement.scrollWidth > document.documentElement.clientWidth + 2) errors.push("horizontal_overflow");
    if (overflowEls.length) errors.push("overflow_elements");
    if (h1OverlapsHeroVisual) errors.push("h1_overlaps_hero_visual");
    if (bodyText.length < 1200) errors.push("body_too_short");
    if (images.some((img) => !img.complete || img.width === 0)) errors.push("broken_image");
    return {
      viewport: vp,
      title: document.title,
      htmlLang: document.documentElement.lang,
      h1: h1s.length,
      h1Text: h1s[0]?.innerText || "",
      h1Box,
      heroVisual: Boolean(heroVisual),
      heroVisualBox: heroBox,
      h1OverlapsHeroVisual,
      visualSystem: visualSystem?.getAttribute("data-visual-system") || null,
      pageType: visualSystem?.getAttribute("data-page-type") || null,
      visualKinds: Array.from(new Set(visualKinds)),
      visualKindCount: visualKinds.length,
      componentSections: document.querySelectorAll(".component-section").length,
      reasons: document.querySelectorAll(".reason").length,
      proofStripItems: document.querySelectorAll(".proof-strip li").length,
      cta: Boolean(document.querySelector(".cta-button")),
      images,
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
      overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 2,
      overflowEls,
      bodyChars: bodyText.length,
      errors,
    };
  }, viewport);
}

async function run() {
  const htmlPath = process.argv[2];
  const outPrefix = process.argv[3];
  if (!htmlPath || !outPrefix) {
    console.error("Usage: node scripts/qa_gsg_html.js <htmlPath> <outPrefix>");
    process.exit(2);
  }
  const absHtml = path.resolve(htmlPath);
  if (!fs.existsSync(absHtml)) {
    console.error(`HTML not found: ${absHtml}`);
    process.exit(2);
  }
  fs.mkdirSync(path.dirname(path.resolve(outPrefix)), { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const report = {
    checked_at: new Date().toISOString(),
    html: absHtml,
  };
  for (const [name, viewport] of Object.entries({
    desktop: { width: 1440, height: 1200 },
    mobile: { width: 390, height: 1200 },
  })) {
    const page = await browser.newPage({ viewport });
    await page.goto(pathToFileURL(absHtml).href, { waitUntil: "load" });
    await page.waitForTimeout(250);
    const png = path.resolve(`${outPrefix}-${name}.png`);
    await page.screenshot({ path: png, fullPage: false, type: "png" });
    report[name] = await metrics(page, viewport);
    report[name].screenshot = png;
    await page.close();
  }
  await browser.close();
  const qaPath = path.resolve(`${outPrefix}-qa.json`);
  fs.writeFileSync(qaPath, JSON.stringify(report, null, 2));
  const errors = [...(report.desktop.errors || []), ...(report.mobile.errors || [])];
  console.log(`qa_gsg_html=${errors.length ? "FAIL" : "PASS"} ${qaPath}`);
  if (errors.length) {
    console.log(`errors=${Array.from(new Set(errors)).join(",")}`);
    process.exit(1);
  }
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
