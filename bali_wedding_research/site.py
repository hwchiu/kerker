from __future__ import annotations

from collections import defaultdict
from functools import partial
from html import escape
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import math
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse

from .derive import build_derived_indexes
from .io import load_workspace_records
from .photo_assets import copy_photo_assets_for_site

SITE_CSS = """@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
  --bg: #f5eee4;
  --bg-glow: rgba(244, 160, 124, 0.28);
  --ink: #1d2a2d;
  --muted: #5c6c6f;
  --panel: rgba(255, 248, 240, 0.84);
  --panel-strong: rgba(255, 252, 249, 0.92);
  --line: rgba(29, 42, 45, 0.12);
  --teal: #1f6b68;
  --teal-soft: rgba(31, 107, 104, 0.12);
  --coral: #cf6f53;
  --gold: #c29d4d;
  --shadow: 0 24px 60px rgba(39, 45, 49, 0.12);
  --radius-xl: 28px;
  --radius-lg: 20px;
  --radius-sm: 12px;
}

* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  min-height: 100vh;
  font-family: "Manrope", sans-serif;
  color: var(--ink);
  background:
    radial-gradient(circle at top left, var(--bg-glow), transparent 32%),
    radial-gradient(circle at 90% 10%, rgba(31, 107, 104, 0.16), transparent 24%),
    linear-gradient(180deg, #f9f2ea 0%, #f3eadf 36%, #efe6db 100%);
}

body.lightbox-open {
  overflow: hidden;
}

body::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(120deg, rgba(255, 255, 255, 0.32), transparent 40%),
    repeating-linear-gradient(
      90deg,
      rgba(255, 255, 255, 0.08) 0,
      rgba(255, 255, 255, 0.08) 1px,
      transparent 1px,
      transparent 24px
    );
  opacity: 0.45;
}

a {
  color: inherit;
}

.page-shell {
  width: min(1180px, calc(100vw - 32px));
  margin: 0 auto;
  padding: 32px 0 72px;
}

.hero,
.surface {
  position: relative;
  overflow: hidden;
  background: var(--panel);
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow);
  backdrop-filter: blur(18px);
}

.hero {
  padding: 44px;
  margin-bottom: 22px;
}

.hero::after,
.surface::after {
  content: "";
  position: absolute;
  inset: auto -60px -80px auto;
  width: 180px;
  height: 180px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(31, 107, 104, 0.18), transparent 70%);
}

.eyebrow {
  margin: 0 0 10px;
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--teal);
}

.hero h1,
.detail-hero h1,
.venue-card h2,
.section-head h2 {
  margin: 0;
  font-family: "Cormorant Garamond", serif;
  letter-spacing: -0.02em;
  line-height: 0.92;
}

.hero h1,
.detail-hero h1 {
  font-size: clamp(3rem, 6vw, 5.6rem);
}

.lede {
  max-width: 760px;
  margin: 18px 0 0;
  font-size: 1rem;
  line-height: 1.8;
  color: var(--muted);
}

.hero-grid,
.detail-grid {
  display: grid;
  gap: 18px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-top: 28px;
}

.stat,
.metric,
.quick-fact,
.detail-block,
.card-panel {
  background: var(--panel-strong);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
}

.stat,
.quick-fact {
  padding: 20px;
}

.stat strong,
.quick-fact strong {
  display: block;
  font-size: 1.85rem;
  line-height: 1;
  font-weight: 800;
}

.stat span,
.quick-fact span {
  display: block;
  margin-top: 8px;
  font-size: 0.84rem;
  color: var(--muted);
}

.surface {
  padding: 26px;
  margin-top: 20px;
}

.section-head {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.section-head h2 {
  font-size: clamp(2rem, 3vw, 3.2rem);
}

.section-head p,
.hint,
.subtle {
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
}

.control-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: minmax(0, 1.5fr) repeat(5, minmax(0, 1fr));
}

.control label {
  display: block;
  margin-bottom: 6px;
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}

.control input,
.control select {
  width: 100%;
  appearance: none;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: #fffdfa;
  padding: 14px 18px;
  font: inherit;
  color: var(--ink);
}

.control input:focus,
.control select:focus {
  outline: 2px solid rgba(31, 107, 104, 0.25);
  outline-offset: 2px;
}

.results-meta {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  margin-top: 18px;
  color: var(--muted);
  font-size: 0.92rem;
}

.results-grid {
  display: grid;
  gap: 18px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 20px;
}

.venue-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 100%;
  padding: 26px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.74), rgba(255, 250, 247, 0.96)),
    linear-gradient(140deg, rgba(207, 111, 83, 0.04), rgba(31, 107, 104, 0.02));
  border: 1px solid rgba(29, 42, 45, 0.09);
  border-radius: var(--radius-lg);
  box-shadow: 0 18px 38px rgba(39, 45, 49, 0.08);
  animation: rise 560ms ease both;
}

.card-media {
  overflow: hidden;
  border: 1px solid rgba(29, 42, 45, 0.09);
  border-radius: var(--radius-lg);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.4), rgba(255, 250, 247, 0.7)),
    rgba(31, 107, 104, 0.08);
}

.card-image {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 10;
  object-fit: cover;
}

.venue-card h2 {
  font-size: 2.15rem;
  line-height: 0.95;
}

.card-kicker,
.detail-kicker {
  margin: 0;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--coral);
}

.card-subtitle,
.detail-subtitle {
  margin: 8px 0 0;
  color: var(--muted);
  line-height: 1.7;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip,
.badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 32px;
  padding: 6px 12px;
  border-radius: 999px;
  background: var(--teal-soft);
  color: var(--teal);
  font-size: 0.8rem;
  font-weight: 700;
}

.badge {
  background: rgba(194, 157, 77, 0.15);
  color: #8f702a;
}

.summary {
  margin: 0;
  color: var(--ink);
  line-height: 1.75;
}

.metric-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.metric,
.card-panel {
  padding: 16px;
}

.metric dt {
  margin: 0 0 6px;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}

.metric dd {
  margin: 0;
  line-height: 1.6;
}

.list,
.compact-list {
  margin: 0;
  padding-left: 18px;
  line-height: 1.7;
}

.compact-list li + li,
.list li + li {
  margin-top: 6px;
}

.card-footer,
.detail-actions,
.bread {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.link-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  padding: 0 18px;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--teal), #2f8d89);
  color: #fff;
  text-decoration: none;
  font-weight: 800;
  letter-spacing: 0.02em;
}

.link-button.secondary {
  background: rgba(31, 107, 104, 0.08);
  color: var(--teal);
}

.detail-hero {
  padding: 34px;
}

.detail-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.stack {
  display: grid;
  gap: 16px;
}

.two-column {
  display: grid;
  gap: 18px;
  grid-template-columns: 1.2fr 0.8fr;
}

.price-table,
.source-table {
  width: 100%;
  border-collapse: collapse;
}

.price-table th,
.price-table td,
.source-table th,
.source-table td {
  padding: 14px 0;
  border-bottom: 1px solid var(--line);
  text-align: left;
  vertical-align: top;
  line-height: 1.6;
}

.price-table th,
.source-table th {
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}

.gallery-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.photo-insight-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-bottom: 16px;
}

.gallery-card,
.source-card {
  padding: 18px;
}

.gallery-card {
  display: grid;
  gap: 14px;
}

.gallery-preview-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.gallery-preview-button {
  display: block;
  padding: 0;
  border: 0;
  background: transparent;
  cursor: zoom-in;
}

.gallery-preview {
  display: block;
  width: 100%;
  aspect-ratio: 1 / 1;
  object-fit: cover;
  border-radius: var(--radius-sm);
  border: 1px solid rgba(29, 42, 45, 0.08);
  background: rgba(255, 255, 255, 0.8);
}

.gallery-empty {
  padding: 16px;
  border: 1px dashed rgba(29, 42, 45, 0.16);
  border-radius: var(--radius-sm);
  color: var(--muted);
  background: rgba(255, 255, 255, 0.56);
}

.gallery-card h3,
.source-card h3 {
  margin: 0 0 10px;
  font-size: 1.02rem;
}

.gallery-card p,
.source-card p {
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
}

.style-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.style-card {
  padding: 20px;
  background: var(--panel-strong);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
}

.style-card h3 {
  margin: 0 0 8px;
  font-size: 1.15rem;
}

.style-meta {
  margin: 14px 0 8px;
  font-size: 0.84rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--teal);
}

.style-section-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.style-venue-card {
  display: grid;
  grid-template-columns: minmax(220px, 0.9fr) minmax(0, 1.1fr);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  background: var(--panel-strong);
  overflow: hidden;
}

.style-venue-media {
  min-height: 100%;
  background: rgba(31, 107, 104, 0.08);
}

.style-venue-image {
  display: block;
  width: 100%;
  height: 100%;
  min-height: 220px;
  object-fit: cover;
}

.style-venue-body {
  display: grid;
  gap: 12px;
  padding: 18px;
}

.style-venue-body h3 {
  margin: 0;
  font-size: 1.2rem;
}

.style-summary-list {
  display: grid;
  gap: 10px;
  margin: 0;
}

.style-summary-list dt {
  margin: 0 0 4px;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}

.style-summary-list dd {
  margin: 0;
  line-height: 1.6;
}

.shortlist-grid,
.fit-grid,
.alt-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.shortlist-card,
.fit-card,
.alt-card {
  padding: 18px;
  background: var(--panel-strong);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
}

.shortlist-card h3,
.fit-card h3,
.alt-card h3 {
  margin: 0 0 8px;
  font-size: 1rem;
}

.shortlist-card ol {
  margin: 14px 0 0;
  padding-left: 18px;
  line-height: 1.7;
}

.shortlist-card li + li {
  margin-top: 8px;
}

.toggle-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.toggle-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  padding: 0 14px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: #fffdfa;
  font-size: 0.9rem;
  color: var(--ink);
}

.toggle-chip input {
  width: auto;
  accent-color: var(--teal);
}

.compare-scroll {
  margin-top: 18px;
  overflow-x: auto;
}

.compare-table {
  width: 100%;
  min-width: 820px;
  border-collapse: collapse;
}

.compare-table th,
.compare-table td {
  padding: 14px 16px;
  border-bottom: 1px solid var(--line);
  text-align: left;
  vertical-align: top;
  background: rgba(255, 255, 255, 0.32);
}

.compare-table th {
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
  background: rgba(255, 255, 255, 0.58);
}

.compare-table td strong {
  display: block;
}

.decision-line {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.decision-line + .decision-line {
  margin-top: 10px;
}

.decision-value {
  font-weight: 800;
  color: var(--teal);
}

.empty-state {
  padding: 30px;
  text-align: center;
  border: 1px dashed rgba(29, 42, 45, 0.22);
  border-radius: var(--radius-lg);
  color: var(--muted);
  background: rgba(255, 255, 255, 0.5);
}

.lightbox {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(16, 23, 26, 0.88);
}

.lightbox[hidden] {
  display: none;
}

.lightbox-dialog {
  position: relative;
  width: min(1100px, calc(100vw - 32px));
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 16px;
  align-items: center;
}

.lightbox-frame {
  margin: 0;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.lightbox-image {
  display: block;
  width: 100%;
  max-height: min(80vh, 900px);
  object-fit: contain;
  background: rgba(16, 23, 26, 0.92);
}

.lightbox-caption {
  padding: 14px 18px;
  color: rgba(255, 255, 255, 0.84);
  line-height: 1.6;
}

.lightbox-close,
.lightbox-nav {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  cursor: pointer;
  font: inherit;
  font-size: 1.5rem;
}

.lightbox-close {
  position: absolute;
  top: -12px;
  right: -12px;
}

.lightbox-nav:disabled {
  opacity: 0.4;
  cursor: default;
}

@keyframes rise {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 980px) {
  .hero,
  .surface,
  .detail-hero {
    padding: 24px;
  }

  .control-grid,
  .results-grid,
  .two-column,
  .detail-grid,
  .hero-grid,
  .style-grid,
  .style-section-grid,
  .gallery-grid,
  .photo-insight-grid,
  .shortlist-grid,
  .fit-grid,
  .alt-grid {
    grid-template-columns: 1fr;
  }

  .style-venue-card,
  .lightbox-dialog {
    grid-template-columns: 1fr;
  }

  .lightbox-close {
    top: 12px;
    right: 12px;
  }
}

@media (max-width: 640px) {
  .page-shell {
    width: min(100vw - 18px, 100%);
    padding-top: 18px;
  }

  .hero h1,
  .detail-hero h1 {
    font-size: clamp(2.6rem, 14vw, 4rem);
  }

  .venue-card {
    padding: 20px;
  }
}
"""

SITE_JS = """(function () {
  function initPhotoLightbox() {
    const lightbox = document.getElementById("photoLightbox");
    if (!lightbox) {
      return;
    }

    const triggers = Array.from(document.querySelectorAll("[data-lightbox-image]"));
    if (!triggers.length) {
      return;
    }

    const imageNode = lightbox.querySelector('[data-lightbox-target="image"]');
    const captionNode = lightbox.querySelector('[data-lightbox-target="caption"]');
    const closeNode = lightbox.querySelector("[data-lightbox-close]");
    const prevNode = lightbox.querySelector("[data-lightbox-prev]");
    const nextNode = lightbox.querySelector("[data-lightbox-next]");
    let activeIndex = -1;

    function render(index) {
      const trigger = triggers[index];
      if (!trigger || !imageNode || !captionNode) {
        return;
      }
      imageNode.src = trigger.dataset.lightboxImage || "";
      imageNode.alt = trigger.querySelector("img")?.alt || "";
      captionNode.textContent = trigger.dataset.lightboxCaption || imageNode.alt;
      if (prevNode) {
        prevNode.disabled = triggers.length <= 1;
      }
      if (nextNode) {
        nextNode.disabled = triggers.length <= 1;
      }
    }

    function open(index) {
      activeIndex = index;
      render(index);
      lightbox.hidden = false;
      document.body.classList.add("lightbox-open");
    }

    function close() {
      lightbox.hidden = true;
      document.body.classList.remove("lightbox-open");
      activeIndex = -1;
    }

    function step(delta) {
      if (activeIndex === -1 || !triggers.length) {
        return;
      }
      open((activeIndex + delta + triggers.length) % triggers.length);
    }

    triggers.forEach((trigger, index) => {
      trigger.addEventListener("click", () => open(index));
    });

    closeNode?.addEventListener("click", close);
    prevNode?.addEventListener("click", () => step(-1));
    nextNode?.addEventListener("click", () => step(1));
    lightbox.addEventListener("click", (event) => {
      if (event.target === lightbox) {
        close();
      }
    });
    document.addEventListener("keydown", (event) => {
      if (lightbox.hidden) {
        return;
      }
      if (event.key === "Escape") {
        close();
      } else if (event.key === "ArrowLeft") {
        step(-1);
      } else if (event.key === "ArrowRight") {
        step(1);
      }
    });
  }

  initPhotoLightbox();

  const dataNode = document.getElementById("venue-data");
  if (!dataNode) {
    return;
  }

  const venues = JSON.parse(dataNode.textContent);
  const resultsNode = document.getElementById("results");
  const compareBody = document.getElementById("compareBody");
  const resultCountNode = document.getElementById("resultCount");
  const emptyNode = document.getElementById("emptyState");
  const searchInput = document.getElementById("searchInput");
  const regionFilter = document.getElementById("regionFilter");
  const typeFilter = document.getElementById("typeFilter");
  const guestFilter = document.getElementById("guestFilter");
  const priceFilter = document.getElementById("priceFilter");
  const rainFilter = document.getElementById("rainFilter");
  const stayFilter = document.getElementById("stayFilter");
  const sortSelect = document.getElementById("sortSelect");
  const dinnerFilter = document.getElementById("dinnerFilter");
  const indoorFilter = document.getElementById("indoorFilter");
  const buyoutFilter = document.getElementById("buyoutFilter");
  const microFilter = document.getElementById("microFilter");

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll("\\"", "&quot;")
      .replaceAll("'", "&#39;");
  }

  function normalizeText(value) {
    return String(value)
      .toLowerCase()
      .normalize("NFKD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^0-9a-z\u3400-\u9fff]+/g, " ")
      .trim();
  }

  function renderList(items) {
    if (!items.length) {
      return "<li>尚未整理到資料。</li>";
    }
    return items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  }

  function renderCard(venue) {
    const chips = [
      venue.price_band_label,
      venue.rain_backup_label,
      venue.accommodation_label,
      venue.photo_value_label,
    ];
    const cover = venue.cover_photo_url
      ? `
        <div class="card-media">
          <img class="card-image" src="${escapeHtml(venue.cover_photo_url)}" alt="${escapeHtml(venue.name_zh)}" loading="lazy">
        </div>
      `
      : "";
    return `
      <article class="venue-card">
        ${cover}
        <div>
          <p class="card-kicker">${escapeHtml(venue.region)} / ${escapeHtml(venue.recommended_guest_size_band)}</p>
          <h2>${escapeHtml(venue.name_zh)}</h2>
          <p class="card-subtitle">${escapeHtml(venue.name_en_official)}<br>${escapeHtml(venue.primary_visual_identity)}</p>
        </div>
        <div class="chip-row">
          ${chips.map((chip) => `<span class="chip">${escapeHtml(chip)}</span>`).join("")}
        </div>
        <p class="summary">${escapeHtml(venue.price_summary_text)}</p>
        <dl class="metric-grid">
          <div class="metric">
            <dt>容量</dt>
            <dd>${escapeHtml(venue.capacity_summary)}</dd>
          </div>
          <div class="metric">
            <dt>交通</dt>
            <dd>${escapeHtml(venue.transport_summary)}</dd>
          </div>
          <div class="metric">
            <dt>照片參考</dt>
            <dd>${escapeHtml(venue.photo_summary)}</dd>
          </div>
          <div class="metric">
            <dt>限制風險</dt>
            <dd>${escapeHtml(venue.restriction_label)}</dd>
          </div>
        </dl>
        <div class="chip-row">
          ${venue.decision_fit_labels.map((label) => `<span class="badge">${escapeHtml(label)}</span>`).join("")}
        </div>
        <div class="card-panel">
          <p class="subtle">適合對象</p>
          <ul class="compact-list">${renderList(venue.best_for.slice(0, 2))}</ul>
        </div>
        <div class="card-footer">
          <span class="subtle">${escapeHtml(venue.source_summary)}</span>
          <a class="link-button" href="venues/${escapeHtml(venue.id)}.html">查看場地檔案</a>
        </div>
      </article>
    `;
  }

  function renderCompareRow(venue) {
    return `
      <tr>
        <td>
          <strong>${escapeHtml(venue.name_zh)}</strong>
          <span class="subtle">${escapeHtml(venue.name_en_official)}</span>
        </td>
        <td>${escapeHtml(venue.public_price_anchor_label)}</td>
        <td>${escapeHtml(venue.capacity_summary)}</td>
        <td>${escapeHtml(venue.rain_backup_label)}</td>
        <td>${escapeHtml(venue.transport_summary)}</td>
        <td>${escapeHtml(venue.accommodation_label)}</td>
        <td><a href="venues/${escapeHtml(venue.id)}.html">查看</a></td>
      </tr>
    `;
  }

  function matches(venue) {
    const searchValue = normalizeText(searchInput.value.trim());
    if (searchValue && !venue.search_text.includes(searchValue)) {
      return false;
    }
    if (regionFilter.value && venue.region !== regionFilter.value) {
      return false;
    }
    if (typeFilter.value && !venue.style_keys.includes(typeFilter.value)) {
      return false;
    }
    if (guestFilter.value && venue.recommended_guest_size_band !== guestFilter.value) {
      return false;
    }
    if (priceFilter.value && venue.price_band_key !== priceFilter.value) {
      return false;
    }
    if (rainFilter.value && venue.rain_backup_status !== rainFilter.value) {
      return false;
    }
    if (stayFilter.value && venue.accommodation_fit !== stayFilter.value) {
      return false;
    }
    if (dinnerFilter.checked && !venue.supports_ceremony_and_dinner) {
      return false;
    }
    if (indoorFilter.checked && !venue.has_indoor_backup) {
      return false;
    }
    if (buyoutFilter.checked && !venue.supports_buyout) {
      return false;
    }
    if (microFilter.checked && !venue.supports_micro_wedding) {
      return false;
    }
    return true;
  }

  function sortVenues(items) {
    const sorted = [...items];
    switch (sortSelect.value) {
      case "starting-price":
        sorted.sort((left, right) =>
          left.public_price_sort_key - right.public_price_sort_key ||
          left.airport_drive_time_minutes_estimate - right.airport_drive_time_minutes_estimate ||
          left.curated_rank - right.curated_rank
        );
        break;
      case "airport-time":
        sorted.sort((left, right) =>
          left.airport_drive_time_minutes_estimate - right.airport_drive_time_minutes_estimate ||
          left.traffic_risk_rank - right.traffic_risk_rank ||
          left.curated_rank - right.curated_rank
        );
        break;
      case "dinner-capacity":
        sorted.sort((left, right) =>
          right.guest_capacity_dinner_max - left.guest_capacity_dinner_max ||
          right.guest_capacity_ceremony_max - left.guest_capacity_ceremony_max ||
          left.curated_rank - right.curated_rank
        );
        break;
      case "rain-readiness":
        sorted.sort((left, right) =>
          left.rain_backup_rank - right.rain_backup_rank ||
          Number(right.has_indoor_backup) - Number(left.has_indoor_backup) ||
          left.curated_rank - right.curated_rank
        );
        break;
      case "photo-depth":
        sorted.sort((left, right) =>
          right.photo_count - left.photo_count ||
          right.source_count - left.source_count ||
          left.curated_rank - right.curated_rank
        );
        break;
      default:
        sorted.sort((left, right) => left.curated_rank - right.curated_rank);
        break;
    }
    return sorted;
  }

  function render() {
    const filtered = sortVenues(venues.filter(matches));
    resultsNode.innerHTML = filtered.map(renderCard).join("");
    compareBody.innerHTML = filtered.map(renderCompareRow).join("");
    resultCountNode.textContent = `${filtered.length} / ${venues.length} 個場地顯示中`;
    emptyNode.hidden = filtered.length > 0;
  }

  [
    searchInput,
    regionFilter,
    typeFilter,
    guestFilter,
    priceFilter,
    rainFilter,
    stayFilter,
    sortSelect,
    dinnerFilter,
    indoorFilter,
    buyoutFilter,
    microFilter,
  ].forEach((node) => node.addEventListener("input", render));

  render();
}());
"""

PRICE_BAND_LABELS = {
    "budget": "入門",
    "midrange": "中階",
    "premium": "高階",
    "luxury": "奢華",
    "ultra_luxury": "超奢華",
}

RAIN_BACKUP_LABELS = {
    "strong": "雨備完整",
    "medium": "雨備可用",
    "weak": "雨備偏弱",
    "unknown": "雨備待確認",
}

ACCOMMODATION_LABELS = {
    "one_stop": "住宿整合度高",
    "workable_with_shuttles": "需安排接駁",
    "fragmented": "住宿較分散",
    "unknown": "住宿待確認",
}

RISK_LABELS = {
    "low": "低",
    "medium": "中",
    "high": "高",
    "unknown": "待確認",
}

PHOTO_VALUE_LABELS = {
    "high": "高價值照片集",
    "medium": "可參考照片集",
    "low": "照片量偏少",
    "unknown": "照片覆蓋待確認",
}

PRICE_STATUS_LABELS = {
    "public_price_available": "有公開價格",
    "quote_required": "需另行詢價",
    "unknown": "價格待確認",
}

FX_REFERENCE_DATE = "2026/06/18"
FX_TO_TWD = {
    "USD": 31.655,
    "IDR": 0.001775,
    "TWD": 1.0,
}
FX_NOTE_TEXT = (
    f"公開價格已統一換算為台幣，匯率基準為 {FX_REFERENCE_DATE}："
    "1 USD = NT$31.655、1 IDR = NT$0.001775。"
)

WEDDING_STYLE_DEFINITIONS = [
    {
        "key": "chapel",
        "label": "教堂",
        "description": "優先看玻璃教堂、海景教堂與儀式感最完整的場地。",
    },
    {
        "key": "jungle",
        "label": "叢林",
        "description": "適合想把梯田、峽谷、睡蓮池與綠意放進婚禮主畫面的組合。",
    },
    {
        "key": "water-platform",
        "label": "水上平台",
        "description": "主打鏡面水台、漂浮步道與倒影感，拍照辨識度最高。",
    },
    {
        "key": "cliffside",
        "label": "懸崖",
        "description": "先看懸崖儀式、草坪晚宴與海平線視角最強的選項。",
    },
    {
        "key": "beach",
        "label": "沙灘",
        "description": "重視海灘儀式、腳踩沙地與度假感最直接的氛圍。",
    },
    {
        "key": "indoor",
        "label": "室內",
        "description": "優先看宴會廳與完整室內動線，對雨備與長輩友善度通常較高。",
    },
    {
        "key": "other",
        "label": "其他",
        "description": "偏向花園、別墅包場或混合型玩法，不屬於上面主風格。",
    },
]
WEDDING_STYLE_LABELS = {
    definition["key"]: definition["label"]
    for definition in WEDDING_STYLE_DEFINITIONS
}

EVIDENCE_CATEGORY_LABELS = {
    "pricing": "價格",
    "capacity": "容量",
    "rain_backup": "雨備",
    "photos": "照片",
    "restrictions": "限制",
    "accommodation": "住宿",
    "transport": "交通",
}

VENUE_TYPE_LABELS = {
    "ballroom": "宴會廳",
    "beach": "海灘",
    "chapel": "教堂",
    "cliffside": "懸崖",
    "garden": "花園",
    "jungle": "叢林",
    "lawn": "草坪",
    "rooftop": "屋頂",
    "villa-buyout": "別墅包場",
    "water-platform": "水台",
}

SOURCE_TYPE_LABELS = {
    "official": "官方頁",
    "platform_agency": "平台／代理頁",
    "editorial_case_study": "案例／編輯頁",
    "social_inspiration": "旅客／社群分享",
}

IMAGE_TYPE_LABELS = {
    "blog_feature": "部落格圖集",
    "official_hotel_gallery": "官方飯店圖集",
    "official_wedding_gallery": "官方婚禮圖集",
    "platform_listing_gallery": "平台圖集",
    "real_wedding_feature": "真實婚禮圖集",
    "social_post": "社群分享照片",
}

PHOTO_AUTHENTICITY_LABELS = {
    "official_promotional": "官方宣傳感",
    "real_wedding": "真實婚禮",
    "unknown": "真實度待確認",
}

PHOTO_COVERAGE_LABELS = {
    "large_gallery": "照片量多",
    "small_gallery": "照片量中等",
    "single_image": "單張照片",
    "document_embedded": "文件內嵌圖片",
}

DECISION_VALUE_LABELS = {
    "high": "決策價值高",
    "medium": "決策價值中",
    "low": "決策價值低",
}

SCENE_TAG_LABELS = {
    "arrival-flow": "動線／抵達感",
    "ballroom-reception": "宴會廳晚宴",
    "beach-ceremony": "海灘儀式",
    "chapel-exterior": "教堂外觀",
    "chapel-interior": "教堂內部",
    "cliffside-ceremony": "懸崖儀式",
    "entrance-procession": "進場動線",
    "floral-setup": "花藝佈置",
    "garden-reception": "花園晚宴",
    "guest-seating": "賓客座位配置",
    "jungle-view": "叢林景觀",
    "night-view": "夜景",
    "public-area": "公共空間",
    "rain-backup-space": "雨備空間",
    "room": "客房",
    "water-platform": "水台",
}

TEXT_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

RISK_RANKS = {"low": 0, "medium": 1, "high": 2, "unknown": 3}
RAIN_RANKS = {"strong": 0, "medium": 1, "weak": 2, "unknown": 3}
ACCOMMODATION_RANKS = {
    "one_stop": 0,
    "workable_with_shuttles": 1,
    "fragmented": 2,
    "unknown": 3,
}

HIDDEN_PHOTO_IMAGE_TYPES = {"official_hotel_gallery", "official_wedding_gallery"}
PHOTO_DECISION_RANKS = {"high": 0, "medium": 1, "low": 2}
PHOTO_IMAGE_TYPE_RANKS = {
    "real_wedding_feature": 0,
    "social_post": 1,
    "blog_feature": 2,
    "platform_listing_gallery": 3,
    "official_wedding_gallery": 4,
    "official_hotel_gallery": 5,
}
PHOTO_SOURCE_TYPE_RANKS = {
    "social_inspiration": 0,
    "editorial_case_study": 1,
    "platform_agency": 2,
    "official": 3,
}


def _safe_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")


def _normalize_text(value: str) -> str:
    return re.sub(r"[^0-9a-z\u3400-\u9fff]+", " ", value.lower()).strip()


def _format_number(value: float | int | None) -> str:
    if value is None:
        return "-"
    if int(value) == value:
        return f"{int(value):,}"
    return f"{value:,.0f}"


def _format_currency(amount: float | None, currency: str) -> str:
    if amount is None:
        return "-"
    return f"{currency} {_format_number(amount)}"


def _round_half_up(value: float) -> int:
    return int(math.floor(value + 0.5))


def _amount_to_twd(amount: float | int | None, currency: str) -> float | None:
    if amount is None:
        return None
    rate = FX_TO_TWD.get(currency.upper())
    if rate is None:
        return None
    return float(amount) * rate


def _format_twd(amount: float | None) -> str:
    if amount is None:
        return "-"
    return f"NT${_format_number(_round_half_up(amount))}"


def _price_entries_with_twd(price_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    converted: list[dict[str, Any]] = []
    for entry in price_entries:
        amount_min = _amount_to_twd(entry["amount_min"], entry["currency"])
        amount_max = _amount_to_twd(entry["amount_max"], entry["currency"])
        if amount_min is None and amount_max is None:
            continue
        converted.append(
            {
                **entry,
                "amount_min_twd": amount_min,
                "amount_max_twd": amount_max,
            }
        )
    return converted


def _price_summary_text_for_display(venue: dict[str, Any]) -> str:
    converted = [
        entry
        for entry in _price_entries_with_twd(venue["price_entries"])
        if entry["amount_min_twd"] is not None
    ]
    if converted:
        converted.sort(key=lambda entry: float(entry["amount_min_twd"]))
        best = _format_twd(float(converted[0]["amount_min_twd"]))
        extra_count = max(0, len(converted) - 1)
        if extra_count:
            return f"公開方案約 {best} 起；另有 {extra_count} 組公開方案可對照。"
        return f"公開方案約 {best} 起。"
    if venue["pricing_status"] == "quote_required":
        return "需另行詢價，目前沒有可直接換算的公開價格。"
    return "價格待確認。"


def _format_bool(value: bool) -> str:
    return "可" if value else "不可"


def _looks_like_image_url(url: str) -> bool:
    return Path(urlparse(url).path).suffix.lower() in TEXT_IMAGE_EXTENSIONS


def _tag_label(tag: str) -> str:
    return SCENE_TAG_LABELS.get(tag, tag.replace("-", " "))


def _style_keys_for_venue(venue: dict[str, Any]) -> list[str]:
    keys: list[str] = []
    venue_types = set(venue["venue_types"])
    ceremony_types = set(venue["ceremony_space_types"])
    reception_types = set(venue["reception_space_types"])

    if "chapel" in venue_types or "glass-chapel" in ceremony_types:
        keys.append("chapel")
    if "jungle" in venue_types:
        keys.append("jungle")
    if "water-platform" in venue_types or "water-platform" in ceremony_types:
        keys.append("water-platform")
    if "cliffside" in venue_types or "cliff-lawn" in ceremony_types or "cliff-lawn" in reception_types:
        keys.append("cliffside")
    if "beach" in venue_types or "beachfront" in ceremony_types or "beach-lawn" in reception_types:
        keys.append("beach")
    if "ballroom" in venue_types or "ballroom" in reception_types:
        keys.append("indoor")
    if not keys:
        keys.append("other")
    return keys


def _capacity_summary(venue: dict[str, Any]) -> str:
    return (
        f"儀式 {venue['guest_capacity_ceremony_min']}-{venue['guest_capacity_ceremony_max']} 人 "
        f"| 晚宴 {venue['guest_capacity_dinner_min']}-{venue['guest_capacity_dinner_max']} 人"
    )


def _transport_summary(venue: dict[str, Any]) -> str:
    minutes = venue["airport_drive_time_minutes_estimate"]
    return f"距機場約 {minutes} 分鐘 | 交通風險 {RISK_LABELS[venue['traffic_risk_level']]}"


def _photo_value_key_from_count(photo_count: int) -> str:
    if photo_count >= 6:
        return "high"
    if photo_count >= 3:
        return "medium"
    if photo_count >= 1:
        return "low"
    return "unknown"

def _photo_summary(photo_count: int) -> str:
    value_key = _photo_value_key_from_count(photo_count)
    return f"{photo_count} 筆非官方照片來源 | {PHOTO_VALUE_LABELS[value_key]}"


def _source_summary(source_count: int, photo_count: int) -> str:
    return f"{source_count} 個來源 / {photo_count} 筆非官方照片來源"


def _price_band_label(venue: dict[str, Any]) -> str:
    if venue["price_band_normalized"] is not None:
        return PRICE_BAND_LABELS[venue["price_band_normalized"]]
    if venue["pricing_status"] == "public_price_available":
        return "有公開價格，待換算級距"
    if venue["pricing_status"] == "quote_required":
        return "需另行詢價"
    return "價格待確認"


def _html_list(items: list[str], *, empty_text: str) -> str:
    if not items:
        return f"<li>{escape(empty_text)}</li>"
    return "".join(f"<li>{escape(item)}</li>" for item in items)


def _badge(text: str, *, tone: str = "chip") -> str:
    return f'<span class="{tone}">{escape(text)}</span>'


def _public_price_anchor(venue: dict[str, Any]) -> tuple[str, float]:
    converted = [
        entry
        for entry in _price_entries_with_twd(venue["price_entries"])
        if entry["amount_min_twd"] is not None
    ]
    if converted:
        best_entry = min(converted, key=lambda item: float(item["amount_min_twd"]))
        best_amount = float(best_entry["amount_min_twd"])
        return f"{_format_twd(best_amount)} 起", best_amount

    if venue["pricing_status"] == "quote_required":
        return "需另行詢價", float("inf")
    return "價格待確認", float("inf")


def _is_visible_photo_entry(
    entry: dict[str, Any],
    source_lookup: dict[str, dict[str, Any]],
) -> bool:
    if entry["image_type"] in HIDDEN_PHOTO_IMAGE_TYPES:
        return False
    source = source_lookup.get(entry["source_id"], {})
    return source.get("source_type") != "official"


def _decision_fit_labels(venue: dict[str, Any]) -> list[str]:
    labels = []
    if venue["supports_ceremony_and_dinner"]:
        labels.append("可辦儀式＋晚宴")
    if venue["supports_buyout"]:
        labels.append("可包場")
    if venue["supports_micro_wedding"]:
        labels.append("適合小型婚禮")
    if venue["has_indoor_backup"]:
        labels.append("有室內雨備")
    return labels


def _decision_fit_lines(venue: dict[str, Any], photo_value_key: str) -> list[tuple[str, str]]:
    return [
        ("可只辦儀式", _format_bool(venue["supports_ceremony_only"])),
        ("可辦儀式＋晚宴", _format_bool(venue["supports_ceremony_and_dinner"])),
        ("可整體包場", _format_bool(venue["supports_buyout"])),
        ("適合小型婚禮", _format_bool(venue["supports_micro_wedding"])),
        ("有室內雨備", _format_bool(venue["has_indoor_backup"])),
        ("有遮蔽雨備", _format_bool(venue["has_covered_backup"])),
        ("照片參考深度", PHOTO_VALUE_LABELS[photo_value_key]),
        ("價格風險", RISK_LABELS[venue["price_risk_level"]]),
    ]


def _render_shortlist_track(title: str, description: str, entries: list[dict[str, Any]]) -> str:
    items = "".join(
        "<li>"
        f"<strong>{escape(entry['name_zh'])}</strong><br>"
        f"<span class=\"subtle\">{escape(entry['public_price_anchor_label'])} / "
        f"{escape(entry['rain_backup_label'])} / {escape(entry['transport_summary'])}</span>"
        "</li>"
        for entry in entries
    )
    return (
        '<article class="shortlist-card">'
        f"<h3>{escape(title)}</h3>"
        f'<p class="subtle">{escape(description)}</p>'
        f"<ol>{items}</ol>"
        "</article>"
    )


def _rank_shortlists(entries: list[dict[str, Any]]) -> list[tuple[str, str, list[dict[str, Any]]]]:
    logistics = sorted(
        entries,
        key=lambda entry: (
            entry["airport_drive_time_minutes_estimate"],
            entry["traffic_risk_rank"],
            entry["accommodation_rank"],
            entry["curated_rank"],
        ),
    )[:3]
    rain = sorted(
        entries,
        key=lambda entry: (
            entry["rain_backup_rank"],
            not entry["has_indoor_backup"],
            entry["curated_rank"],
        ),
    )[:3]
    scale = sorted(
        entries,
        key=lambda entry: (
            -entry["guest_capacity_dinner_max"],
            entry["accommodation_rank"],
            entry["curated_rank"],
        ),
    )[:3]
    value = [
        entry
        for entry in sorted(
            entries,
            key=lambda entry: (
                entry["public_price_sort_key"],
                entry["curated_rank"],
            ),
        )
        if entry["public_price_sort_key"] != float("inf")
    ][:3]
    if not value:
        value = entries[:3]
    return [
        ("交通最順", "優先給重視接送順暢、長輩移動負擔較低的組合。", logistics),
        ("雨備最穩", "天氣一變就會影響決策時，先看這一組。", rain),
        ("大桌數優先", "需要真正有晚宴容量的場地，先從這裡看。", scale),
        ("公開入門價最低", "還沒正式詢價前，先做預算初篩最有用。", value),
    ]


def _render_shortlist_section(entries: list[dict[str, Any]]) -> str:
    cards = "".join(
        _render_shortlist_track(title, description, shortlist)
        for title, description, shortlist in _rank_shortlists(entries)
    )
    return (
        '<section class="surface">'
        '<div class="section-head">'
        "<h2>快速初篩路線</h2>"
        '<p>先用最常見的淘汰條件做第一輪：交通、雨備、桌數與公開入門價。</p>'
        "</div>"
        f'<div class="shortlist-grid">{cards}</div>'
        "</section>"
    )


def _entries_by_style(entries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped = {definition["key"]: [] for definition in WEDDING_STYLE_DEFINITIONS}
    for entry in entries:
        for key in entry.get("style_keys", []):
            grouped.setdefault(key, []).append(entry)
    for key in grouped:
        grouped[key] = sorted(
            grouped[key],
            key=lambda entry: (
                entry["public_price_sort_key"],
                entry["airport_drive_time_minutes_estimate"],
                entry["curated_rank"],
            ),
        )
    return grouped


def _render_style_nav(entries: list[dict[str, Any]]) -> str:
    grouped = _entries_by_style(entries)
    cards = []
    for definition in WEDDING_STYLE_DEFINITIONS:
        style_entries = grouped.get(definition["key"], [])
        examples = "、".join(entry["name_zh"] for entry in style_entries[:3]) or "目前尚未歸類到這一型"
        cards.append(
            '<article class="style-card">'
            f'<p class="eyebrow">{escape(definition["label"])}</p>'
            f'<h3>{escape(definition["label"])}</h3>'
            f'<p class="summary">{escape(definition["description"])}</p>'
            f'<p class="style-meta">{len(style_entries)} 個場地</p>'
            f'<p class="hint">{escape(examples)}</p>'
            f'<a class="link-button secondary" href="#style-{escape(definition["key"])}">查看這一類</a>'
            "</article>"
        )
    return (
        '<section class="surface">'
        '<div class="section-head"><h2>依婚禮風格開始挑</h2>'
        '<p>同一個場地可能同時出現在多種風格裡，先從你們最在意的畫面語言開始縮小範圍。</p></div>'
        f'<div class="style-grid">{"".join(cards)}</div>'
        "</section>"
    )


def _render_style_spotlight(entry: dict[str, Any]) -> str:
    cover = ""
    if entry.get("cover_photo_url"):
        cover = (
            '<div class="style-venue-media">'
            f'<img class="style-venue-image" src="{escape(str(entry["cover_photo_url"]))}" alt="{escape(entry["name_zh"])}" loading="lazy">'
            "</div>"
        )
    return (
        '<article class="style-venue-card">'
        f"{cover}"
        '<div class="style-venue-body">'
        f'<p class="card-kicker">{escape(entry["region"])} / {escape(entry["recommended_guest_size_band"])}</p>'
        f'<h3>{escape(entry["name_zh"])}</h3>'
        f'<p class="subtle">{escape(entry["name_en_official"])}</p>'
        f'<p class="summary">{escape(entry["primary_visual_identity"])}</p>'
        f'<div class="chip-row">{_badge(entry["public_price_anchor_label"], tone="badge")}{_badge(entry["rain_backup_label"])}{_badge(entry["accommodation_label"])}</div>'
        '<dl class="style-summary-list">'
        f'<div><dt>交通</dt><dd>{escape(entry["transport_summary"])}</dd></div>'
        f'<div><dt>照片</dt><dd>{escape(entry["photo_summary"])}</dd></div>'
        "</dl>"
        '<div class="card-footer">'
        f'<span class="subtle">{escape(entry["price_summary_text"])}</span>'
        f'<a class="link-button" href="venues/{escape(entry["id"])}.html">查看場地檔案</a>'
        "</div>"
        "</div>"
        "</article>"
    )


def _render_style_sections(entries: list[dict[str, Any]]) -> str:
    grouped = _entries_by_style(entries)
    sections = []
    for definition in WEDDING_STYLE_DEFINITIONS:
        style_entries = grouped.get(definition["key"], [])
        if style_entries:
            body = f'<div class="style-section-grid">{"".join(_render_style_spotlight(entry) for entry in style_entries)}</div>'
        else:
            body = '<div class="empty-state">這一類目前還沒有可用場地，後續補更多資料時會自動出現在這裡。</div>'
        sections.append(
            '<section class="surface style-section" '
            f'id="style-{escape(definition["key"])}">'
            '<div class="section-head">'
            f'<h2>{escape(definition["label"])}</h2>'
            f'<p>{escape(definition["description"])}</p>'
            "</div>"
            f"{body}"
            "</section>"
        )
    return "".join(sections)


def _render_compare_rows(entries: list[dict[str, Any]]) -> str:
    rows = []
    for entry in entries:
        rows.append(
            "<tr>"
            "<td>"
            f"<strong>{escape(entry['name_zh'])}</strong>"
            f"<span class=\"subtle\">{escape(entry['name_en_official'])}</span>"
            "</td>"
            f"<td>{escape(entry['public_price_anchor_label'])}</td>"
            f"<td>{escape(entry['capacity_summary'])}</td>"
            f"<td>{escape(entry['rain_backup_label'])}</td>"
            f"<td>{escape(entry['transport_summary'])}</td>"
            f"<td>{escape(entry['accommodation_label'])}</td>"
            f"<td><a href=\"venues/{escape(entry['id'])}.html\">查看</a></td>"
            "</tr>"
        )
    return "".join(rows)


def _similarity_score(base: dict[str, Any], candidate: dict[str, Any]) -> int:
    score = 0
    if base["region"] == candidate["region"]:
        score += 4
    if base["recommended_guest_size_band"] == candidate["recommended_guest_size_band"]:
        score += 2
    if base["price_band_key"] and base["price_band_key"] == candidate["price_band_key"]:
        score += 1
    if base["accommodation_fit"] == candidate["accommodation_fit"]:
        score += 1
    if base["rain_backup_status"] == candidate["rain_backup_status"]:
        score += 1
    score += len(set(base["venue_types"]) & set(candidate["venue_types"])) * 2
    return score


def _build_alternative_entries(
    current_id: str,
    entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    current = next(entry for entry in entries if entry["id"] == current_id)
    ranked = [
        (entry, _similarity_score(current, entry))
        for entry in entries
        if entry["id"] != current_id
    ]
    ranked = [item for item in ranked if item[1] > 0]
    ranked.sort(
        key=lambda item: (
            -item[1],
            item[0]["airport_drive_time_minutes_estimate"],
            item[0]["curated_rank"],
        ),
    )
    return [entry for entry, _ in ranked[:3]]


def _render_decision_fit(venue: dict[str, Any], photo_value_key: str) -> str:
    lines = "".join(
        '<div class="decision-line">'
        f'<span class="subtle">{escape(label)}</span>'
        f'<span class="decision-value">{escape(value)}</span>'
        "</div>"
        for label, value in _decision_fit_lines(venue, photo_value_key)
    )
    return (
        '<section class="surface">'
        '<div class="section-head"><h2>決策適配</h2>'
        '<p>先確認場地在結構上能不能支撐你們的婚禮形式，再去比風格與美感。</p></div>'
        '<div class="fit-grid">'
        f'<article class="fit-card">{lines}</article>'
        '<article class="fit-card">'
        '<h3>賓客移動感受</h3>'
        f'<p class="summary">{escape(venue["guest_mobility_notes"])}</p>'
        "</article>"
        '<article class="fit-card">'
        '<h3>較不適合</h3>'
        f'<ul class="list">{_html_list(venue["not_ideal_for"], empty_text="尚未整理到資料。")}</ul>'
        "</article>"
        '<article class="fit-card">'
        '<h3>待確認問題</h3>'
        f'<ul class="list">{_html_list(venue["open_questions"], empty_text="目前沒有待確認問題。")}</ul>'
        "</article>"
        '</div>'
        "</section>"
    )


def _render_alternatives(alternatives: list[dict[str, Any]]) -> str:
    if not alternatives:
        return (
            '<section class="surface">'
            '<div class="section-head"><h2>相近替代場地</h2>'
            '<p>目前資料庫裡還沒有足夠接近的替代選項。</p></div>'
            '<div class="empty-state">後續補進更多同區或同風格場地後，這裡就能自動推薦替代名單。</div>'
            "</section>"
        )
    cards = []
    for entry in alternatives:
        cards.append(
            '<article class="alt-card">'
            f'<h3>{escape(entry["name_zh"])}</h3>'
            f'<p class="subtle">{escape(entry["name_en_official"])}<br>{escape(entry["region"])} / {escape(entry["recommended_guest_size_band"])}</p>'
            f'<p class="summary" style="margin-top:12px;">{escape(entry["price_summary_text"])}</p>'
            f'<div class="chip-row" style="margin-top:12px;">{_badge(entry["rain_backup_label"])}{_badge(entry["accommodation_label"])}{_badge(entry["public_price_anchor_label"], tone="badge")}</div>'
            '<div class="detail-actions" style="margin-top:16px;">'
            f'<span class="subtle">{escape(entry["best_for"][0] if entry["best_for"] else "相近條件場地")}</span>'
            f'<a class="link-button secondary" href="{escape(entry["id"])}.html">查看替代場地</a>'
            "</div>"
            "</article>"
        )
    return (
        '<section class="surface">'
        '<div class="section-head"><h2>相近替代場地</h2>'
        '<p>如果這間有進 shortlist，這些是目前資料庫裡條件最接近的備選。</p></div>'
        f'<div class="alt-grid">{"".join(cards)}</div>'
        "</section>"
    )


def _render_card(entry: dict[str, Any]) -> str:
    chips = [
        _badge(entry["price_band_label"]),
        _badge(entry["rain_backup_label"]),
        _badge(entry["accommodation_label"]),
        _badge(entry["photo_value_label"], tone="badge"),
    ]
    cover = ""
    if entry.get("cover_photo_url"):
        cover = (
            '<div class="card-media">'
            f'<img class="card-image" src="{escape(str(entry["cover_photo_url"]))}" alt="{escape(entry["name_zh"])}" loading="lazy">'
            "</div>"
        )
    return (
        '<article class="venue-card">'
        f"{cover}"
        "<div>"
        f'<p class="card-kicker">{escape(entry["region"])} / {escape(entry["recommended_guest_size_band"])}</p>'
        f'<h2>{escape(entry["name_zh"])}</h2>'
        f'<p class="card-subtitle">{escape(entry["name_en_official"])}<br>'
        f'{escape(entry["primary_visual_identity"])}</p>'
        "</div>"
        f'<div class="chip-row">{"".join(chips)}</div>'
        f'<p class="summary">{escape(entry["price_summary_text"])}</p>'
        '<dl class="metric-grid">'
        '<div class="metric"><dt>容量</dt>'
        f'<dd>{escape(entry["capacity_summary"])}</dd></div>'
        '<div class="metric"><dt>交通</dt>'
        f'<dd>{escape(entry["transport_summary"])}</dd></div>'
        '<div class="metric"><dt>照片參考</dt>'
        f'<dd>{escape(entry["photo_summary"])}</dd></div>'
        '<div class="metric"><dt>限制風險</dt>'
        f'<dd>{escape(entry["restriction_label"])}</dd></div>'
        "</dl>"
        '<div class="card-panel">'
        '<p class="subtle">適合對象</p>'
        f'<ul class="compact-list">{_html_list(entry["best_for"][:2], empty_text="尚未整理到資料。")}</ul>'
        "</div>"
        '<div class="card-footer">'
        f'<span class="subtle">{escape(entry["source_summary"])}</span>'
        f'<a class="link-button" href="venues/{escape(entry["id"])}.html">查看場地檔案</a>'
        "</div>"
        "</article>"
    )


def _render_price_table(price_entries: list[dict[str, Any]]) -> str:
    if not price_entries:
        return '<div class="empty-state">目前還沒有整理到公開方案價格。</div>'

    rows = []
    for entry in price_entries:
        amount_parts = []
        twd_min = _amount_to_twd(entry["amount_min"], entry["currency"])
        twd_max = _amount_to_twd(entry["amount_max"], entry["currency"])
        if twd_min is not None:
            amount_parts.append(_format_twd(twd_min))
        if twd_max is not None and twd_max != twd_min:
            amount_parts.append(_format_twd(twd_max))
        amount_text = " 至 ".join(amount_parts) if amount_parts else "-"

        original_parts = []
        if entry["amount_min"] is not None:
            original_parts.append(_format_currency(entry["amount_min"], entry["currency"]))
        if entry["amount_max"] is not None and entry["amount_max"] != entry["amount_min"]:
            original_parts.append(_format_currency(entry["amount_max"], entry["currency"]))
        original_text = (
            f'約原幣 {" 至 ".join(original_parts)}'
            if original_parts
            else "原幣價格未公開"
        )
        included = []
        if entry["includes_stay"]:
            included.append("住宿")
        if entry["includes_decoration"]:
            included.append("佈置")
        if entry["includes_dinner"]:
            included.append("晚宴")
        if entry["includes_tax_service"]:
            included.append("稅金／服務費")
        include_text = ", ".join(included) if included else "僅場地或資料未明"
        rows.append(
            "<tr>"
            f"<td><strong>{escape(entry['label'])}</strong><br><span class=\"subtle\">{escape(entry['conditions_text'])}</span></td>"
            f"<td><strong>{escape(amount_text)}</strong><br><span class=\"subtle\">{escape(original_text)}</span></td>"
            f"<td>{entry['pricing_year']}</td>"
            f"<td>{escape(include_text)}</td>"
            f"<td>{escape(RISK_LABELS.get(entry['confidence'], entry['confidence']))}</td>"
            "</tr>"
        )
    return (
        '<table class="price-table">'
        "<thead><tr>"
        "<th>方案</th><th>價格</th><th>年份</th><th>包含項目</th><th>可信度</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
    )


def _photo_preview_urls(
    entry: dict[str, Any],
    photo_assets_by_entry: dict[str, list[str]],
) -> list[str]:
    preview_urls = photo_assets_by_entry.get(entry["photo_entry_id"], [])
    if preview_urls:
        return preview_urls
    fallback = entry["image_url_or_gallery_url"]
    if _looks_like_image_url(fallback):
        return [fallback]
    return []


def _sort_photo_entries(
    photo_entries: list[dict[str, Any]],
    photo_assets_by_entry: dict[str, list[str]],
    source_lookup: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    def sort_key(entry: dict[str, Any]) -> tuple[Any, ...]:
        preview_urls = _photo_preview_urls(entry, photo_assets_by_entry)
        source_type = source_lookup.get(entry["source_id"], {}).get(
            "source_type",
            "platform_agency",
        )
        return (
            0 if preview_urls else 1,
            0 if entry["authenticity"] == "real_wedding" else 1,
            PHOTO_DECISION_RANKS.get(entry["decision_value"], 99),
            PHOTO_IMAGE_TYPE_RANKS.get(entry["image_type"], 99),
            PHOTO_SOURCE_TYPE_RANKS.get(source_type, 99),
            entry["photo_entry_id"],
        )

    return sorted(photo_entries, key=sort_key)


def _visible_photo_entries(
    photo_entries: list[dict[str, Any]],
    photo_assets_by_entry: dict[str, list[str]],
    source_lookup: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    visible = [
        entry
        for entry in photo_entries
        if _is_visible_photo_entry(entry, source_lookup)
    ]
    return _sort_photo_entries(visible, photo_assets_by_entry, source_lookup)


def _photo_stats(
    photo_entries: list[dict[str, Any]],
    photo_assets_by_entry: dict[str, list[str]],
    source_lookup: dict[str, dict[str, Any]],
) -> dict[str, int | str]:
    visible = _visible_photo_entries(photo_entries, photo_assets_by_entry, source_lookup)
    asset_count = sum(len(_photo_preview_urls(entry, photo_assets_by_entry)) for entry in visible)
    social_count = sum(
        1
        for entry in visible
        if entry["image_type"] in {"social_post", "blog_feature"}
    )
    platform_count = sum(
        1
        for entry in visible
        if entry["image_type"] == "platform_listing_gallery"
    )
    real_count = sum(1 for entry in visible if entry["authenticity"] == "real_wedding")
    hidden_count = len(photo_entries) - len(visible)
    return {
        "visible_count": len(visible),
        "asset_count": asset_count,
        "real_count": real_count,
        "social_count": social_count,
        "platform_count": platform_count,
        "hidden_count": hidden_count,
        "photo_value_key": _photo_value_key_from_count(len(visible)),
    }


def _index_cover_photo_url(
    photo_entries: list[dict[str, Any]],
    photo_assets_by_entry: dict[str, list[str]],
    source_lookup: dict[str, dict[str, Any]],
) -> str | None:
    for entry in _visible_photo_entries(photo_entries, photo_assets_by_entry, source_lookup):
        preview_urls = _photo_preview_urls(entry, photo_assets_by_entry)
        if preview_urls:
            return preview_urls[0].removeprefix("../")
    return None


def _render_photo_cards(
    photo_entries: list[dict[str, Any]],
    photo_assets_by_entry: dict[str, list[str]],
    source_lookup: dict[str, dict[str, Any]],
) -> str:
    visible_entries = _visible_photo_entries(photo_entries, photo_assets_by_entry, source_lookup)
    if not visible_entries:
        return '<div class="empty-state">目前還沒有整理到可參考的照片來源。</div>'
    cards = []
    for entry in visible_entries:
        source = source_lookup.get(entry["source_id"], {})
        preview_urls = _photo_preview_urls(entry, photo_assets_by_entry)
        preview_html = (
            '<div class="gallery-preview-grid">'
            + "".join(
                '<button type="button" class="gallery-preview-button" '
                f'data-lightbox-image="{escape(url)}" '
                f'data-lightbox-caption="{escape(source.get("source_name", entry["photo_entry_id"]))}">'
                f'<img class="gallery-preview" src="{escape(url)}" alt="{escape(source.get("source_name", entry["photo_entry_id"]))}" loading="lazy">'
                "</button>"
                for url in preview_urls[:6]
            )
            + "</div>"
        )
        if not preview_urls:
            preview_html = '<div class="gallery-empty">這個來源目前還沒成功抓到可直接顯示的圖片。</div>'
        cards.append(
            '<article class="gallery-card card-panel">'
            f'<h3>{escape(source.get("source_name", entry["photo_entry_id"]))}</h3>'
            f"{preview_html}"
            f'<div class="chip-row">{_badge(SOURCE_TYPE_LABELS.get(source.get("source_type", ""), "來源類型待確認"))}'
            f'{_badge(IMAGE_TYPE_LABELS.get(entry["image_type"], entry["image_type"]))}'
            f'{_badge(PHOTO_AUTHENTICITY_LABELS.get(entry["authenticity"], entry["authenticity"]))}'
            f'{_badge(DECISION_VALUE_LABELS.get(entry["decision_value"], entry["decision_value"]), tone="badge")}'
            + "".join(_badge(_tag_label(tag)) for tag in entry["scene_tags"][:4])
            + "</div>"
            f'<p>{escape(entry["decision_notes"])}</p>'
            f'<p class="hint">來源頁：{escape(entry["page_url"])}</p>'
            "</article>"
        )
    return f'<div class="gallery-grid">{"".join(cards)}</div>'


def _render_photo_insights(
    photo_entries: list[dict[str, Any]],
    photo_assets_by_entry: dict[str, list[str]],
    source_lookup: dict[str, dict[str, Any]],
) -> str:
    stats = _photo_stats(photo_entries, photo_assets_by_entry, source_lookup)
    insight_items = [
        ("非官方圖源", stats["visible_count"]),
        ("真實婚禮", stats["real_count"]),
        ("旅客／部落格", stats["social_count"]),
        ("已下載本地圖片", stats["asset_count"]),
    ]
    cards = "".join(
        '<div class="quick-fact">'
        f"<strong>{value}</strong>"
        f"<span>{escape(label)}</span>"
        "</div>"
        for label, value in insight_items
    )
    hidden_text = (
        f"為了更貼近實際判斷，這裡預設隱藏了 {stats['hidden_count']} 筆官方飯店圖集。"
        if stats["hidden_count"]
        else "這裡目前只顯示非官方來源的照片。"
    )
    return f'<div class="photo-insight-grid">{cards}</div><p class="hint">{escape(hidden_text)}</p>'


def _render_photo_lightbox() -> str:
    return (
        '<div class="lightbox" id="photoLightbox" hidden>'
        '<div class="lightbox-dialog" role="dialog" aria-modal="true" aria-label="放大照片">'
        '<button type="button" class="lightbox-close" data-lightbox-close aria-label="關閉照片">×</button>'
        '<button type="button" class="lightbox-nav prev" data-lightbox-prev aria-label="上一張照片">‹</button>'
        '<figure class="lightbox-frame">'
        '<img class="lightbox-image" data-lightbox-target="image" alt="">'
        '<figcaption class="lightbox-caption" data-lightbox-target="caption"></figcaption>'
        "</figure>"
        '<button type="button" class="lightbox-nav next" data-lightbox-next aria-label="下一張照片">›</button>'
        "</div>"
        "</div>"
    )


def _render_sources(source_entries: list[dict[str, Any]]) -> str:
    if not source_entries:
        return '<div class="empty-state">目前還沒有整理到來源紀錄。</div>'
    cards = []
    for source in source_entries:
        cards.append(
            '<article class="source-card card-panel">'
            f'<h3>{escape(source["source_name"])}</h3>'
            f'<div class="chip-row">{_badge(SOURCE_TYPE_LABELS.get(source["source_type"], source["source_type"]))}'
            + "".join(_badge(EVIDENCE_CATEGORY_LABELS.get(category, category)) for category in source["evidence_categories"])
            + "</div>"
            f'<p>{escape(source["raw_excerpt_summary"])}</p>'
            '<div class="detail-actions" style="margin-top:16px;">'
            f'<span class="subtle">擷取日期 {escape(source["captured_at"])}</span>'
            f'<a class="link-button secondary" href="{escape(source["source_url"])}" target="_blank" rel="noreferrer">開啟來源頁</a>'
            "</div>"
            "</article>"
        )
    return f'<div class="stack">{"".join(cards)}</div>'


def _render_detail_page(
    venue: dict[str, Any],
    derived: dict[str, Any],
    sources: list[dict[str, Any]],
    photos: list[dict[str, Any]],
    alternatives: list[dict[str, Any]],
    photo_assets_by_entry: dict[str, list[str]],
) -> str:
    source_lookup = {source["source_id"]: source for source in sources}
    photo_stats = _photo_stats(photos, photo_assets_by_entry, source_lookup)
    quick_facts = [
        ("價格模式", PRICE_STATUS_LABELS[venue["pricing_status"]]),
        ("雨備能力", RAIN_BACKUP_LABELS[venue["rain_backup_status"]]),
        ("住宿整合", ACCOMMODATION_LABELS[venue["accommodation_fit"]]),
        ("交通風險", RISK_LABELS[venue["traffic_risk_level"]]),
    ]
    facts_html = "".join(
        '<div class="quick-fact">'
        f"<strong>{escape(value)}</strong>"
        f"<span>{escape(label)}</span>"
        "</div>"
        for label, value in quick_facts
    )
    price_summary_text = _price_summary_text_for_display(venue)

    return (
        "<!doctype html>"
        '<html lang="zh-Hant">'
        "<head>"
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{escape(venue['name_zh'])} | 峇里島婚禮場地檔案</title>"
        '<link rel="stylesheet" href="../assets/site.css">'
        "</head>"
        "<body>"
        '<main class="page-shell">'
        '<section class="detail-hero hero">'
        '<div class="bread">'
        '<a class="link-button secondary" href="../index.html">回到場地索引</a>'
        f'<span class="subtle">{escape(venue["region"])} / {escape(venue["subarea"])}</span>'
        "</div>"
        f'<p class="detail-kicker">{escape(venue["brand_or_group"])}</p>'
        f'<h1>{escape(venue["name_zh"])}</h1>'
        f'<p class="detail-subtitle">{escape(venue["name_en_official"])}<br>{escape(venue["primary_visual_identity"])}</p>'
        '<div class="detail-grid">'
        f"{facts_html}"
        "</div>"
        "</section>"
        f"{_render_decision_fit(venue, str(photo_stats['photo_value_key']))}"
        '<section class="surface">'
        '<div class="section-head"><h2>快速掃描</h2>'
        '<p>把容量、價格、雨備、交通與住宿一次看完，先判斷有沒有 shortlist 資格。</p></div>'
        '<div class="two-column">'
        '<div class="stack">'
        '<div class="card-panel">'
        '<p class="subtle">容量</p>'
        f'<p class="summary">{escape(_capacity_summary(venue))}</p>'
        "</div>"
        '<div class="card-panel">'
        '<p class="subtle">價格摘要</p>'
        f'<p class="summary">{escape(price_summary_text)}</p>'
        f'<p class="hint" style="margin-top:10px;">{escape(FX_NOTE_TEXT)}</p>'
        "</div>"
        '<div class="card-panel">'
        '<p class="subtle">天候與雨備</p>'
        f'<p class="summary">{escape(venue["backup_space_description"])}</p>'
        f'<p class="hint" style="margin-top:10px;">{escape(venue["backup_quality_notes"])} '
        f'{escape(venue["weather_exposure_notes"])}</p>'
        "</div>"
        '<div class="card-panel">'
        '<p class="subtle">交通與住宿</p>'
        f'<p class="summary">{escape(venue["transport_notes"])}</p>'
        f'<p class="hint" style="margin-top:10px;">{escape(venue["onsite_room_inventory_notes"])} '
        f'{escape(venue["nearby_accommodation_notes"])}</p>'
        "</div>"
        "</div>"
        '<div class="stack">'
        '<div class="card-panel">'
        '<p class="subtle">適合對象</p>'
        f'<ul class="list">{_html_list(venue["best_for"], empty_text="尚未整理到適合對象。")}</ul>'
        "</div>"
        '<div class="card-panel">'
        '<p class="subtle">關鍵優勢</p>'
        f'<ul class="list">{_html_list(venue["key_strengths"], empty_text="尚未整理到優勢。")}</ul>'
        "</div>"
        '<div class="card-panel">'
        '<p class="subtle">關鍵風險</p>'
        f'<ul class="list">{_html_list(venue["key_risks"], empty_text="尚未整理到風險。")}</ul>'
        "</div>"
        '<div class="card-panel">'
        '<p class="subtle">待確認問題</p>'
        f'<ul class="list">{_html_list(venue["open_questions"], empty_text="目前沒有待確認問題。")}</ul>'
        "</div>"
        "</div>"
        "</div>"
        "</section>"
        '<section class="surface">'
        '<div class="section-head"><h2>價格條目</h2>'
        '<p>先用公開可見的方案底價做比較；下表主欄位已換算台幣，原始幣別保留在同列方便對照。</p></div>'
        f'<p class="hint" style="margin-bottom:16px;">{escape(FX_NOTE_TEXT)}</p>'
        f"{_render_price_table(venue['price_entries'])}"
        "</section>"
        '<section class="surface">'
        '<div class="section-head"><h2>限制與待確認事項</h2>'
        '<p>這些條件往往比想像中更影響預算、外部廠商選擇和賓客動線。</p></div>'
        '<div class="two-column">'
        '<div class="stack">'
        '<div class="card-panel"><p class="subtle">音量／宵禁</p>'
        f'<p class="summary">{escape(venue["noise_cutoff_notes"])}</p></div>'
        '<div class="card-panel"><p class="subtle">外部廠商政策</p>'
        f'<p class="summary">{escape(venue["external_vendor_policy"])}</p></div>'
        '<div class="card-panel"><p class="subtle">住宿／低消門檻</p>'
        f'<p class="summary">{escape(venue["minimum_stay_requirement_notes"])} {escape(venue["minimum_spend_notes"])}</p></div>'
        "</div>"
        '<div class="stack">'
        '<div class="card-panel"><p class="subtle">空拍／親子／使用限制</p>'
        f'<p class="summary">{escape(venue["drone_policy_notes"])}</p>'
        f'<p class="hint" style="margin-top:10px;">{escape(venue["family_child_notes"])} '
        f'{escape(venue["religious_or_space_use_notes"])} '
        f'{escape(venue["operational_constraints_notes"])}</p></div>'
        '<div class="card-panel"><p class="subtle">資料密度</p>'
        f'<p class="summary">{escape(_source_summary(len(sources), int(photo_stats["visible_count"])))}</p>'
        f'<p class="hint" style="margin-top:10px;">照片覆蓋：'
        f'{escape(PHOTO_VALUE_LABELS[str(photo_stats["photo_value_key"])])}</p></div>'
        "</div>"
        "</div>"
        "</section>"
        '<section class="surface">'
        '<div class="section-head"><h2>照片參考</h2>'
        '<p>直接看真實分享、旅客照片與平台頁面，比對儀式感、雨備、晚宴空間和賓客動線；點照片可放大查看。</p></div>'
        f"{_render_photo_insights(photos, photo_assets_by_entry, source_lookup)}"
        f"{_render_photo_cards(photos, photo_assets_by_entry, source_lookup)}"
        "</section>"
        '<section class="surface">'
        '<div class="section-head"><h2>來源紀錄</h2>'
        '<p>每一筆摘要都對應到實際來源頁，方便你回查價格、照片與限制資訊。</p></div>'
        f"{_render_sources(sources)}"
        "</section>"
        f"{_render_alternatives(alternatives)}"
        '<section class="surface">'
        '<div class="section-head"><h2>快速外查</h2>'
        '<p>需要核對路線、地址或官方房量資訊時，再從這裡開外部頁面。</p></div>'
        '<div class="detail-actions">'
        f'<a class="link-button" href="{escape(venue["official_website"])}" target="_blank" rel="noreferrer">官方網站</a>'
        f'<a class="link-button secondary" href="{escape(venue["maps_url"])}" target="_blank" rel="noreferrer">地圖</a>'
        "</div>"
        "</section>"
        f"{_render_photo_lightbox()}"
        '<script src="../assets/site.js"></script>'
        "</main>"
        "</body>"
        "</html>"
    )


def _index_entry(
    venue: dict[str, Any],
    derived: dict[str, Any],
    sources: list[dict[str, Any]],
    photos: list[dict[str, Any]],
    *,
    curated_rank: int,
) -> dict[str, Any]:
    price_band_key = venue["price_band_normalized"]
    public_price_anchor_label, public_price_sort_key = _public_price_anchor(venue)
    style_keys = _style_keys_for_venue(venue)
    source_lookup = {source["source_id"]: source for source in sources}
    visible_photo_count = sum(
        1
        for entry in photos
        if _is_visible_photo_entry(entry, source_lookup)
    )
    photo_value_key = _photo_value_key_from_count(visible_photo_count)
    search_text = _normalize_text(
        " ".join(
            [
                venue["name_zh"],
                venue["name_en_official"],
                venue["name_en_official"].replace("-", " "),
                venue["region"],
                venue["subarea"],
                venue["primary_visual_identity"],
                *venue["venue_types"],
                *(WEDDING_STYLE_LABELS[key] for key in style_keys),
                *venue["style_tags"],
                *venue["best_for"],
                *venue["key_strengths"],
            ]
        )
    )
    return {
        "id": venue["id"],
        "name_zh": venue["name_zh"],
        "name_en_official": venue["name_en_official"],
        "region": venue["region"],
        "subarea": venue["subarea"],
        "venue_types": venue["venue_types"],
        "venue_type_labels": [VENUE_TYPE_LABELS.get(tag, tag) for tag in venue["venue_types"]],
        "style_keys": style_keys,
        "style_labels": [WEDDING_STYLE_LABELS[key] for key in style_keys],
        "recommended_guest_size_band": venue["recommended_guest_size_band"],
        "price_band_key": price_band_key,
        "price_band_label": _price_band_label(venue),
        "public_price_anchor_label": public_price_anchor_label,
        "public_price_sort_key": public_price_sort_key,
        "pricing_status": venue["pricing_status"],
        "price_summary_text": _price_summary_text_for_display(venue),
        "rain_backup_status": venue["rain_backup_status"],
        "rain_backup_label": RAIN_BACKUP_LABELS[venue["rain_backup_status"]],
        "rain_backup_rank": RAIN_RANKS[venue["rain_backup_status"]],
        "accommodation_fit": venue["accommodation_fit"],
        "accommodation_label": ACCOMMODATION_LABELS[venue["accommodation_fit"]],
        "accommodation_rank": ACCOMMODATION_RANKS[venue["accommodation_fit"]],
        "restriction_level": venue["restriction_level"],
        "restriction_label": RISK_LABELS[venue["restriction_level"]],
        "traffic_risk_level": venue["traffic_risk_level"],
        "traffic_risk_rank": RISK_RANKS[venue["traffic_risk_level"]],
        "price_risk_level": venue["price_risk_level"],
        "photo_value_key": photo_value_key,
        "photo_value_label": PHOTO_VALUE_LABELS[photo_value_key],
        "source_summary": _source_summary(len(sources), visible_photo_count),
        "source_count": len(sources),
        "photo_count": visible_photo_count,
        "capacity_summary": _capacity_summary(venue),
        "transport_summary": _transport_summary(venue),
        "photo_summary": _photo_summary(visible_photo_count),
        "best_for": venue["best_for"],
        "primary_visual_identity": venue["primary_visual_identity"],
        "airport_drive_time_minutes_estimate": venue["airport_drive_time_minutes_estimate"],
        "guest_capacity_ceremony_max": venue["guest_capacity_ceremony_max"],
        "guest_capacity_dinner_max": venue["guest_capacity_dinner_max"],
        "supports_ceremony_and_dinner": venue["supports_ceremony_and_dinner"],
        "supports_buyout": venue["supports_buyout"],
        "supports_micro_wedding": venue["supports_micro_wedding"],
        "has_indoor_backup": venue["has_indoor_backup"],
        "decision_fit_labels": _decision_fit_labels(venue),
        "curated_rank": curated_rank,
        "search_text": search_text,
        "cover_photo_url": None,
    }


def _render_select_options(values: list[str], *, labels: dict[str, str] | None = None) -> str:
    options = ['<option value="">全部</option>']
    for value in values:
        label = labels[value] if labels and value in labels else value
        options.append(f'<option value="{escape(value)}">{escape(label)}</option>')
    return "".join(options)


def _build_site_payload(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    venues, sources, photos = load_workspace_records(root)
    derived_lookup = {
        entry["id"]: entry for entry in build_derived_indexes(root)["venues"]
    }
    sources_by_venue: dict[str, list[dict[str, Any]]] = defaultdict(list)
    photos_by_venue: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for source in sources:
        sources_by_venue[source["venue_id"]].append(source)
    for photo in photos:
        photos_by_venue[photo["venue_id"]].append(photo)

    sorted_venues = sorted(venues, key=lambda entry: (entry["region"], entry["name_en_official"]))
    entries = [
        _index_entry(
            venue,
            derived_lookup[venue["id"]],
            sources_by_venue.get(venue["id"], []),
            photos_by_venue.get(venue["id"], []),
            curated_rank=index,
        )
        for index, venue in enumerate(sorted_venues)
    ]
    totals = {
        "venue_count": len(sorted_venues),
        "photo_count": sum(entry["photo_count"] for entry in entries),
        "source_count": sum(len(sources_by_venue.get(venue["id"], [])) for venue in sorted_venues),
        "regions": sorted({venue["region"] for venue in sorted_venues}),
    }
    return entries, {
        "venues": sorted_venues,
        "sources_by_venue": sources_by_venue,
        "photos_by_venue": photos_by_venue,
        "derived_lookup": derived_lookup,
        "totals": totals,
    }


def _attach_cover_photo_urls(
    entries: list[dict[str, Any]],
    photos_by_venue: dict[str, list[dict[str, Any]]],
    sources_by_venue: dict[str, list[dict[str, Any]]],
    photo_assets_by_entry: dict[str, list[str]],
) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for entry in entries:
        source_lookup = {
            source["source_id"]: source
            for source in sources_by_venue.get(entry["id"], [])
        }
        updated = dict(entry)
        updated["cover_photo_url"] = _index_cover_photo_url(
            photos_by_venue.get(entry["id"], []),
            photo_assets_by_entry,
            source_lookup,
        )
        enriched.append(updated)
    return enriched


def _render_index_page(entries: list[dict[str, Any]], totals: dict[str, Any]) -> str:
    card_html = "".join(_render_card(entry) for entry in entries)
    compare_rows = _render_compare_rows(entries)
    region_values = sorted({entry["region"] for entry in entries})
    style_values = [definition["key"] for definition in WEDDING_STYLE_DEFINITIONS]
    guest_values = sorted({entry["recommended_guest_size_band"] for entry in entries})
    price_values = sorted({entry["price_band_key"] for entry in entries if entry["price_band_key"]})
    rain_values = sorted({entry["rain_backup_status"] for entry in entries})
    stay_values = sorted({entry["accommodation_fit"] for entry in entries})

    return (
        "<!doctype html>"
        '<html lang="zh-Hant">'
        "<head>"
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>峇里島婚禮場地索引</title>"
        '<link rel="stylesheet" href="assets/site.css">'
        "</head>"
        "<body>"
        '<main class="page-shell">'
        '<section class="hero">'
        '<p class="eyebrow">Bali Wedding Research</p>'
        "<h1>峇里島婚禮場地索引</h1>"
        '<p class="lede">先用場地、雨備、交通與住宿快速淘汰，再點進單一場地檔案看價格、容量、非官方照片線索與限制。</p>'
        '<div class="hero-grid">'
        '<div class="stat">'
        f"<strong>{totals['venue_count']}</strong><span>已整理場地</span>"
        "</div>"
        '<div class="stat">'
        f"<strong>{totals['photo_count']}</strong><span>非官方照片來源</span>"
        "</div>"
        '<div class="stat">'
        f"<strong>{totals.get('asset_count', 0)}</strong><span>已下載本地圖片</span>"
        "</div>"
        '<div class="stat">'
        f"<strong>{totals['source_count']}</strong><span>來源頁數</span>"
        "</div>"
        "</div>"
        f'<p class="hint" style="margin-top:16px;">{escape(FX_NOTE_TEXT)}</p>'
        "</section>"
        f"{_render_style_nav(entries)}"
        f"{_render_style_sections(entries)}"
        f"{_render_shortlist_section(entries)}"
        '<section class="surface">'
        '<div class="section-head">'
        "<h2>先篩選再深看</h2>"
        '<p>可用名稱、區域、風格或結構化條件，先把 shortlist 快速收斂。</p>'
        "</div>"
        '<div class="control-grid">'
        '<div class="control"><label for="searchInput">搜尋</label>'
        '<input id="searchInput" type="search" placeholder="可搜名稱、區域、風格與適合對象"></div>'
        '<div class="control"><label for="regionFilter">區域</label>'
        f'<select id="regionFilter">{_render_select_options(region_values)}</select></div>'
        '<div class="control"><label for="typeFilter">婚禮風格</label>'
        f'<select id="typeFilter">{_render_select_options(style_values, labels=WEDDING_STYLE_LABELS)}</select></div>'
        '<div class="control"><label for="guestFilter">適合人數帶</label>'
        f'<select id="guestFilter">{_render_select_options(guest_values)}</select></div>'
        '<div class="control"><label for="priceFilter">價格級距</label>'
        f'<select id="priceFilter">{_render_select_options(price_values, labels=PRICE_BAND_LABELS)}</select></div>'
        '<div class="control"><label for="rainFilter">雨備能力</label>'
        f'<select id="rainFilter">{_render_select_options(rain_values, labels=RAIN_BACKUP_LABELS)}</select></div>'
        '<div class="control"><label for="stayFilter">住宿整合</label>'
        f'<select id="stayFilter">{_render_select_options(stay_values, labels=ACCOMMODATION_LABELS)}</select></div>'
        '<div class="control"><label for="sortSelect">排序方式</label>'
        '<select id="sortSelect"><option value="curated">編輯排序</option><option value="starting-price">公開入門價最低</option><option value="airport-time">距機場最短</option><option value="dinner-capacity">晚宴容量最大</option><option value="rain-readiness">雨備最強</option><option value="photo-depth">照片線索最多</option></select></div>'
        "</div>"
        '<div class="toggle-grid">'
        '<label class="toggle-chip" for="dinnerFilter"><input id="dinnerFilter" type="checkbox">只看可辦儀式＋晚宴</label>'
        '<label class="toggle-chip" for="indoorFilter"><input id="indoorFilter" type="checkbox">只看有室內雨備</label>'
        '<label class="toggle-chip" for="buyoutFilter"><input id="buyoutFilter" type="checkbox">只看可包場</label>'
        '<label class="toggle-chip" for="microFilter"><input id="microFilter" type="checkbox">只看適合小型婚禮</label>'
        "</div>"
        '<div class="results-meta">'
        '<span id="resultCount">'
        f"{len(entries)} / {len(entries)} 個場地顯示中"
        "</span>"
        f'<span>{escape(", ".join(totals["regions"]))}</span>'
        "</div>"
        '</section>'
        '<section class="surface">'
        '<div class="section-head"><h2>全部場地比較</h2>'
        '<p>先橫向掃描最影響決策的條件，再決定哪些值得點開看完整檔案。</p></div>'
        '<div class="compare-scroll"><table class="compare-table"><thead><tr><th>場地</th><th>公開入門價</th><th>容量</th><th>雨備</th><th>交通</th><th>住宿</th><th>明細</th></tr></thead><tbody id="compareBody">'
        f"{compare_rows}"
        '</tbody></table></div>'
        "</section>"
        '<section class="surface">'
        '<div class="section-head"><h2>場地卡片</h2>'
        '<p>如果你要看適合對象、優勢風險與資料密度，這裡比表格更直觀。</p></div>'
        '<div id="results" class="results-grid">'
        f"{card_html}"
        "</div>"
        '<div id="emptyState" class="empty-state" hidden>目前沒有場地符合這組篩選條件。</div>'
        "</section>"
        f'<script id="venue-data" type="application/json">{_safe_json(entries)}</script>'
        '<script src="assets/site.js"></script>'
        "</main>"
        "</body>"
        "</html>"
    )


def _render_static_redirect_page(target: str, *, title: str) -> str:
    safe_target = escape(target, quote=True)
    return (
        "<!doctype html>"
        '<html lang="zh-Hant">'
        "<head>"
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<meta http-equiv="refresh" content="0; url={safe_target}">'
        f"<title>{escape(title)}</title>"
        "<script>"
        f"window.location.replace({json.dumps(target)});"
        "</script>"
        "</head>"
        "<body>"
        f'<p>Redirecting to <a href="{safe_target}">{safe_target}</a>.</p>'
        "</body>"
        "</html>"
    )


def _render_pages_redirect_page() -> str:
    return (
        "<!doctype html>"
        '<html lang="zh-Hant">'
        "<head>"
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>峇里島婚禮場地索引</title>"
        "<script>"
        'const basePath = window.location.pathname.endsWith("/")'
        ' ? window.location.pathname'
        ' : `${window.location.pathname}/`;'
        'window.location.replace(`${basePath}docs/`);'
        "</script>"
        "</head>"
        "<body>"
        '<p>Redirecting to <a href="docs/">docs/</a>.</p>'
        "</body>"
        "</html>"
    )


def write_static_site(root: Path, output_dir: Path) -> list[Path]:
    entries, payload = _build_site_payload(root)
    output_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = output_dir / "assets"
    venue_dir = output_dir / "venues"
    assets_dir.mkdir(parents=True, exist_ok=True)
    venue_dir.mkdir(parents=True, exist_ok=True)

    for existing in venue_dir.glob("*.html"):
        existing.unlink()

    index_path = output_dir / "index.html"
    css_path = assets_dir / "site.css"
    js_path = assets_dir / "site.js"
    photo_assets_by_entry = copy_photo_assets_for_site(root, output_dir)
    entries = _attach_cover_photo_urls(
        entries,
        payload["photos_by_venue"],
        payload["sources_by_venue"],
        photo_assets_by_entry,
    )
    payload["totals"]["asset_count"] = sum(
        len(asset_urls) for asset_urls in photo_assets_by_entry.values()
    )

    index_path.write_text(
        _render_index_page(entries, payload["totals"]),
        encoding="utf-8",
    )
    css_path.write_text(SITE_CSS, encoding="utf-8")
    js_path.write_text(SITE_JS, encoding="utf-8")

    written = [index_path, css_path, js_path]
    for venue in payload["venues"]:
        page_path = venue_dir / f"{venue['id']}.html"
        page_path.write_text(
            _render_detail_page(
                venue,
                payload["derived_lookup"][venue["id"]],
                payload["sources_by_venue"].get(venue["id"], []),
                payload["photos_by_venue"].get(venue["id"], []),
                _build_alternative_entries(venue["id"], entries),
                photo_assets_by_entry,
            ),
            encoding="utf-8",
        )
        written.append(page_path)
    return written


def write_pages_site(root: Path, docs_dir: Path | None = None) -> list[Path]:
    target_docs_dir = docs_dir or root / "docs"
    written = write_static_site(root, target_docs_dir)

    docs_nojekyll_path = target_docs_dir / ".nojekyll"
    legacy_docs_dir = target_docs_dir / "docs"
    legacy_venues_dir = legacy_docs_dir / "venues"
    root_index_path = root / "index.html"
    root_nojekyll_path = root / ".nojekyll"

    legacy_docs_dir.mkdir(parents=True, exist_ok=True)
    legacy_venues_dir.mkdir(parents=True, exist_ok=True)
    for existing in legacy_venues_dir.glob("*.html"):
        existing.unlink()

    docs_nojekyll_path.write_text("", encoding="utf-8")
    legacy_index_path = legacy_docs_dir / "index.html"
    legacy_index_path.write_text(
        _render_static_redirect_page("../", title="峇里島婚禮場地索引"),
        encoding="utf-8",
    )
    legacy_written = [legacy_index_path]
    for detail_page_path in sorted((target_docs_dir / "venues").glob("*.html")):
        legacy_detail_path = legacy_venues_dir / detail_page_path.name
        legacy_detail_path.write_text(
            _render_static_redirect_page(
                f"../../venues/{detail_page_path.name}",
                title="峇里島婚禮場地檔案",
            ),
            encoding="utf-8",
        )
        legacy_written.append(legacy_detail_path)
    root_index_path.write_text(_render_pages_redirect_page(), encoding="utf-8")
    root_nojekyll_path.write_text("", encoding="utf-8")

    return [
        *written,
        docs_nojekyll_path,
        *legacy_written,
        root_index_path,
        root_nojekyll_path,
    ]


def build_site_server(output_dir: Path, *, host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    handler = partial(SimpleHTTPRequestHandler, directory=str(output_dir))
    return ThreadingHTTPServer((host, port), handler)


def serve_site(root: Path, output_dir: Path, *, host: str = "0.0.0.0", port: int = 8000) -> None:
    write_static_site(root, output_dir)
    server = build_site_server(output_dir, host=host, port=port)
    bound_host, bound_port = server.server_address[:2]
    print(f"Serving {output_dir} at http://{bound_host}:{bound_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
