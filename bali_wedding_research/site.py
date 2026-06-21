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

SITE_CSS = """@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700;9..144,800&family=Noto+Sans+TC:wght@400;500;700;900&display=swap');

:root {
  --bg: #f1eadf;
  --bg-glow: rgba(181, 147, 98, 0.18);
  --ink: #1e2924;
  --muted: #5f695f;
  --panel: rgba(255, 250, 244, 0.92);
  --panel-strong: rgba(255, 253, 249, 0.98);
  --line: rgba(30, 41, 36, 0.1);
  --line-strong: rgba(30, 41, 36, 0.18);
  --teal: #27473f;
  --teal-soft: rgba(39, 71, 63, 0.08);
  --coral: #9a5b46;
  --gold: #ac8d5f;
  --hero-ink: #f7f1e7;
  --shadow-sm: 0 18px 40px rgba(27, 33, 29, 0.08);
  --shadow-md: 0 24px 56px rgba(27, 33, 29, 0.12);
  --shadow-lg: 0 32px 80px rgba(27, 33, 29, 0.16);
  --radius-xl: 30px;
  --radius-lg: 22px;
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
  font-family: "Noto Sans TC", sans-serif;
  color: var(--ink);
  background:
    radial-gradient(circle at top left, var(--bg-glow), transparent 32%),
    radial-gradient(circle at 88% 8%, rgba(39, 71, 63, 0.12), transparent 20%),
    linear-gradient(180deg, #f6f0e7 0%, #eee5d8 42%, #e7ddd0 100%);
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
    linear-gradient(180deg, rgba(255, 255, 255, 0.24), transparent 24%),
    radial-gradient(circle at 18% 12%, rgba(255, 255, 255, 0.26), transparent 18%);
  opacity: 0.45;
}

a {
  color: inherit;
}

.page-shell {
  width: min(1200px, calc(100vw - 32px));
  margin: 0 auto;
  padding: 28px 0 88px;
}

.hero,
.surface {
  position: relative;
  overflow: hidden;
  border-radius: var(--radius-xl);
}

.surface {
  background: var(--panel);
  border: 1px solid rgba(255, 255, 255, 0.56);
  box-shadow: var(--shadow-sm);
  backdrop-filter: blur(6px);
}

.hero {
  padding: 48px;
  margin-bottom: 24px;
  background:
    linear-gradient(135deg, rgba(32, 57, 50, 0.98), rgba(26, 44, 38, 0.98)),
    radial-gradient(circle at 100% 0%, rgba(172, 141, 95, 0.24), transparent 24%);
  border: 1px solid rgba(202, 183, 149, 0.22);
  box-shadow: var(--shadow-lg);
  color: var(--hero-ink);
}

.hero::after,
.surface::after {
  content: "";
  position: absolute;
  inset: auto -40px -70px auto;
  width: 160px;
  height: 160px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(172, 141, 95, 0.18), transparent 70%);
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
  font-family: "Fraunces", serif;
  letter-spacing: -0.02em;
  line-height: 0.96;
}

.hero h1,
.detail-hero h1 {
  font-size: clamp(3rem, 6vw, 5.6rem);
}

.lede {
  max-width: 760px;
  margin: 18px 0 0;
  font-size: 1.04rem;
  line-height: 1.8;
  color: var(--muted);
}

.hero .eyebrow,
.hero .card-kicker,
.hero .detail-kicker {
  color: rgba(247, 241, 231, 0.76);
}

.hero .lede,
.hero .hint,
.hero .subtle {
  color: rgba(247, 241, 231, 0.8);
}

.hero-layout {
  display: grid;
  gap: 28px;
  grid-template-columns: minmax(0, 1.45fr) minmax(300px, 0.75fr);
  align-items: end;
}

.hero-copy {
  display: grid;
  gap: 0;
}

.hero-panel {
  display: grid;
  gap: 16px;
  padding: 22px;
  background: rgba(255, 249, 238, 0.08);
  border: 1px solid rgba(255, 240, 220, 0.14);
  border-radius: var(--radius-lg);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.index-layout {
  display: grid;
  gap: 24px;
  grid-template-columns: minmax(0, 1fr) 300px;
  align-items: start;
}

.index-main {
  min-width: 0;
}

.index-sidebar {
  min-width: 0;
}

.page-toc {
  position: sticky;
  top: 14px;
  z-index: 16;
  display: grid;
  gap: 18px;
  padding: 22px 24px;
  background:
    linear-gradient(180deg, rgba(255, 252, 247, 0.96), rgba(250, 244, 236, 0.92));
  border: 1px solid rgba(255, 255, 255, 0.62);
  box-shadow: var(--shadow-md);
  backdrop-filter: blur(10px);
}

.page-toc-head {
  display: flex;
  flex-wrap: wrap;
  align-items: end;
  justify-content: space-between;
  gap: 16px;
}

.page-toc-title {
  display: grid;
  gap: 8px;
}

.page-toc-title h2 {
  margin: 0;
  font-family: "Fraunces", serif;
  font-size: clamp(1.5rem, 2vw, 2rem);
  letter-spacing: -0.03em;
}

.page-toc-groups {
  display: grid;
  gap: 14px;
}

.toc-group {
  display: grid;
  gap: 10px;
}

.toc-group .subtle {
  font-size: 0.8rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.page-toc-nav {
  display: grid;
  gap: 10px;
}

.page-toc-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 42px;
  padding: 0 16px;
  border-radius: 999px;
  border: 1px solid rgba(39, 71, 63, 0.12);
  background: rgba(39, 71, 63, 0.05);
  color: var(--ink);
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 700;
  line-height: 1;
  transition:
    transform 180ms ease,
    background-color 180ms ease,
    border-color 180ms ease,
    color 180ms ease,
    box-shadow 180ms ease;
}

.page-toc-link:hover,
.page-toc-link:focus-visible {
  transform: translateY(-1px);
  border-color: rgba(39, 71, 63, 0.2);
  background: rgba(39, 71, 63, 0.08);
}

.page-toc-link.is-active {
  background: var(--teal);
  border-color: var(--teal);
  color: var(--hero-ink);
  box-shadow: 0 10px 24px rgba(39, 71, 63, 0.22);
}

.toc-current {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 18px;
  border: 1px solid rgba(39, 71, 63, 0.12);
  background: rgba(39, 71, 63, 0.06);
}

.toc-current-label {
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}

.toc-current strong {
  font-size: 0.98rem;
  color: var(--teal);
}

.hero-list {
  margin: 0;
  padding-left: 18px;
  line-height: 1.8;
}

.hero-list li + li {
  margin-top: 6px;
}

.hero-actions,
.detail-anchor-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 24px;
}

.quick-link,
.detail-anchor-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 0 15px;
  border-radius: 999px;
  border: 1px solid rgba(255, 246, 230, 0.14);
  background: rgba(255, 249, 238, 0.08);
  color: var(--hero-ink);
  text-decoration: none;
  font-size: 0.88rem;
  font-weight: 700;
  letter-spacing: 0.01em;
  transition: transform 180ms ease, background-color 180ms ease, border-color 180ms ease;
}

.quick-link:hover,
.quick-link:focus-visible,
.detail-anchor-link:hover,
.detail-anchor-link:focus-visible {
  transform: translateY(-1px);
  background: rgba(255, 249, 238, 0.16);
  border-color: rgba(255, 240, 220, 0.22);
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
  padding: 22px;
}

.hero .stat {
  background: rgba(255, 249, 238, 0.1);
  border: 1px solid rgba(255, 240, 220, 0.12);
  color: var(--hero-ink);
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

.hero .stat span {
  color: rgba(247, 241, 231, 0.72);
}

.hero-rate-note {
  margin-top: 18px;
}

.surface {
  padding: 28px;
  margin-top: 22px;
}

.section-head {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
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

.status-inline {
  display: grid;
  gap: 8px;
  margin-top: 14px;
  padding: 14px 16px;
  border-radius: 18px;
  border: 1px solid rgba(194, 157, 77, 0.24);
  background: rgba(255, 250, 242, 0.94);
}

.status-inline.status-inline-ok {
  border-color: rgba(31, 107, 104, 0.2);
  background: rgba(243, 250, 249, 0.96);
}

.status-inline.status-inline-watch {
  border-color: rgba(194, 157, 77, 0.28);
  background: rgba(255, 249, 239, 0.96);
}

.status-inline.status-inline-alert {
  border-color: rgba(203, 108, 81, 0.28);
  background: rgba(255, 243, 239, 0.97);
}

.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: fit-content;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.04em;
}

.status-pill-ok {
  background: rgba(31, 107, 104, 0.12);
  color: var(--teal);
}

.status-pill-watch {
  background: rgba(194, 157, 77, 0.18);
  color: #8f6c16;
}

.status-pill-alert {
  background: rgba(203, 108, 81, 0.16);
  color: #9f4933;
}

.status-summary,
.status-note,
.status-meta {
  margin: 0;
}

.status-summary {
  color: var(--ink);
  line-height: 1.65;
}

.status-meta {
  font-size: 0.82rem;
  color: var(--muted);
}

.compare-status {
  display: grid;
  gap: 6px;
}

.control-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: minmax(0, 1.8fr) repeat(3, minmax(0, 1fr));
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
  border: 1px solid var(--line-strong);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.92);
  padding: 14px 18px;
  font: inherit;
  color: var(--ink);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6);
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
  gap: 20px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 20px;
}

.venue-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-height: 100%;
  padding: 24px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(255, 250, 244, 0.98));
  border: 1px solid rgba(30, 41, 36, 0.08);
  border-top: 4px solid rgba(172, 141, 95, 0.5);
  border-radius: var(--radius-lg);
  box-shadow: 0 16px 38px rgba(32, 37, 34, 0.08);
  animation: rise 560ms ease both;
}

.card-media {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(29, 42, 45, 0.08);
  border-radius: var(--radius-lg);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.48), rgba(255, 250, 247, 0.74)),
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
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(39, 71, 63, 0.08);
  color: var(--teal);
  font-size: 0.78rem;
  font-weight: 700;
}

.badge {
  background: rgba(172, 141, 95, 0.16);
  color: #7f6131;
}

.summary {
  margin: 0;
  color: var(--ink);
  line-height: 1.75;
}

.metric-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.metric,
.card-panel {
  padding: 18px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.44);
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
  background: linear-gradient(135deg, var(--teal), #3d5e55);
  color: #fff;
  text-decoration: none;
  font-weight: 800;
  letter-spacing: 0.02em;
  box-shadow: 0 12px 28px rgba(39, 71, 63, 0.18);
  transition: transform 180ms ease, box-shadow 180ms ease, background-color 180ms ease;
}

.link-button.secondary {
  background: rgba(39, 71, 63, 0.08);
  color: var(--teal);
  box-shadow: none;
  border: 1px solid rgba(39, 71, 63, 0.12);
}

.link-button:hover,
.link-button:focus-visible,
.compare-detail-link:hover,
.compare-detail-link:focus-visible {
  transform: translateY(-1px);
}

.detail-hero {
  padding: 40px;
}

.detail-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-top: 24px;
}

.stack {
  display: grid;
  gap: 18px;
}

.two-column {
  display: grid;
  gap: 20px;
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
  gap: 16px;
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
  gap: 16px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.74), rgba(255, 250, 247, 0.94)),
    rgba(31, 107, 104, 0.02);
}

.gallery-card-header {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 12px;
}

.gallery-source-meta {
  margin: 6px 0 0;
  color: var(--muted);
  font-size: 0.86rem;
}

.gallery-source-count,
.style-card-count {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 11px;
  border-radius: 999px;
  background: rgba(31, 107, 104, 0.08);
  color: var(--teal);
  font-size: 0.78rem;
  font-weight: 800;
  white-space: nowrap;
}

.photo-gallery-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.photo-gallery-item {
  display: grid;
  gap: 12px;
  padding: 14px;
  border: 1px solid rgba(29, 42, 45, 0.08);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
  box-shadow: var(--shadow-sm);
}

.gallery-preview-button {
  display: block;
  position: relative;
  padding: 0;
  border: 0;
  background: transparent;
  cursor: zoom-in;
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.gallery-preview {
  display: block;
  width: 100%;
  aspect-ratio: 4 / 5;
  object-fit: cover;
  border-radius: var(--radius-sm);
  border: 1px solid rgba(29, 42, 45, 0.08);
  background: rgba(255, 255, 255, 0.8);
  transition: transform 220ms ease;
}

.gallery-preview-button:hover .gallery-preview,
.gallery-preview-button:focus-visible .gallery-preview {
  transform: scale(1.03);
}

.gallery-preview-overlay {
  position: absolute;
  left: 10px;
  bottom: 10px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(18, 25, 27, 0.7);
  color: rgba(255, 255, 255, 0.92);
  font-size: 0.74rem;
  font-weight: 800;
  letter-spacing: 0.04em;
}

.gallery-preview-fallback {
  display: grid;
  gap: 10px;
  align-content: end;
  min-height: 220px;
  padding: 18px;
  border: 1px dashed rgba(171, 191, 255, 0.28);
  border-radius: var(--radius-sm);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(143, 180, 255, 0.08)),
    radial-gradient(circle at top right, rgba(255, 210, 143, 0.18), transparent 28%);
  color: var(--hero-ink);
  text-decoration: none;
}

.gallery-preview-fallback strong {
  font-size: 1.05rem;
}

.gallery-preview-fallback-kicker {
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(224, 233, 255, 0.74);
}

.gallery-preview-hint {
  margin: -4px 0 0;
  color: var(--muted);
  font-size: 0.84rem;
  line-height: 1.6;
}

.gallery-empty {
  padding: 16px;
  border: 1px dashed rgba(29, 42, 45, 0.16);
  border-radius: var(--radius-sm);
  color: var(--muted);
  background: rgba(255, 255, 255, 0.56);
}

.photo-gallery-meta {
  display: grid;
  gap: 6px;
}

.photo-gallery-title {
  margin: 0;
  font-size: 1rem;
}

.photo-gallery-summary-text {
  margin: 0;
  color: var(--muted);
  font-size: 0.88rem;
  line-height: 1.5;
}

.photo-gallery-details {
  display: grid;
  gap: 10px;
  border-top: 1px solid rgba(29, 42, 45, 0.08);
  padding-top: 10px;
}

.photo-gallery-summary {
  cursor: pointer;
  color: var(--teal);
  font-size: 0.82rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  list-style: none;
}

.photo-gallery-summary::-webkit-details-marker {
  display: none;
}

.photo-gallery-link {
  display: inline-flex;
  align-items: center;
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--teal);
  text-decoration: none;
}

.photo-gallery-link:hover,
.photo-gallery-link:focus-visible {
  text-decoration: underline;
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

.advanced-filters {
  margin-top: 16px;
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  background: var(--panel-strong);
  overflow: hidden;
}

.advanced-filters summary {
  cursor: pointer;
  list-style: none;
  padding: 16px 18px;
  font-size: 0.92rem;
  font-weight: 800;
  color: var(--teal);
}

.advanced-filters summary::-webkit-details-marker {
  display: none;
}

.advanced-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  padding: 0 18px 18px;
}

.filter-guide {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-bottom: 18px;
}

.filter-guide-card {
  padding: 18px;
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.56);
}

.filter-guide-card h3 {
  margin: 0 0 8px;
  font-size: 1rem;
}

.advanced-toggle-grid {
  padding: 0 18px 18px;
  margin-top: 0;
}

.snapshot-grid,
.space-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.summary-card,
.space-card {
  padding: 20px;
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.68);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.44);
}

.summary-card-emphasis {
  background: linear-gradient(180deg, rgba(31, 107, 104, 0.08), rgba(255, 255, 255, 0.92));
}

.summary-card .summary,
.space-card .summary {
  margin-top: 8px;
}

.space-summary {
  display: grid;
  gap: 10px;
  margin: 14px 0;
}

.space-summary dt {
  margin: 0 0 4px;
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}

.space-summary dd {
  margin: 0;
  line-height: 1.6;
}

.price-table-wrap {
  overflow-x: auto;
}

.status-overview-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.status-overview-card {
  display: grid;
  gap: 14px;
  padding: 20px;
  background: var(--panel-strong);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.46);
}

.status-overview-top {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 12px;
}

.status-overview-top h3 {
  margin: 4px 0 0;
  font-size: 1.18rem;
}

.status-overview-card .status-summary {
  margin: 0;
}

.style-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.style-card {
  display: grid;
  gap: 0;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(34, 55, 48, 0.98), rgba(26, 43, 38, 0.98));
  border: 1px solid rgba(26, 43, 38, 0.18);
  border-radius: var(--radius-lg);
  box-shadow: 0 18px 34px rgba(28, 35, 32, 0.12);
  color: var(--hero-ink);
}

.style-card-media {
  position: relative;
  min-height: 180px;
  background: linear-gradient(135deg, rgba(172, 141, 95, 0.24), rgba(39, 71, 63, 0.48));
}

.preview-media-fallback {
  display: grid;
}

.style-card-media::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(19, 34, 30, 0.06), rgba(19, 34, 30, 0.62));
}

.style-card-media-placeholder::before {
  content: "";
  position: absolute;
  inset: 18px;
  border: 1px solid rgba(255, 241, 220, 0.16);
  border-radius: 18px;
}

.style-card-image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-media-content {
  position: relative;
  z-index: 1;
  display: grid;
  align-content: end;
  gap: 12px;
  min-height: 100%;
  padding: 22px;
}

.preview-media-kicker {
  margin: 0;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(247, 241, 231, 0.78);
}

.preview-media-note {
  margin: 0;
  color: rgba(247, 241, 231, 0.86);
  line-height: 1.6;
}

.preview-media-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.preview-media-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid rgba(255, 244, 227, 0.24);
  background: rgba(255, 255, 255, 0.08);
  color: var(--hero-ink);
  font-size: 0.88rem;
  font-weight: 700;
  text-decoration: none;
  transition: transform 160ms ease, background 160ms ease, border-color 160ms ease;
}

.preview-media-link:hover,
.preview-media-link:focus-visible {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.14);
  border-color: rgba(255, 244, 227, 0.42);
}

.style-card-body {
  display: grid;
  gap: 14px;
  padding: 22px;
}

.style-card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.style-card h3 {
  margin: 0 0 8px;
  font-size: 1.5rem;
}

.style-card .summary {
  color: rgba(247, 241, 231, 0.82);
}

.style-meta {
  margin: 0;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(247, 241, 231, 0.62);
}

.style-card .eyebrow {
  color: rgba(247, 241, 231, 0.72);
}

.style-card-count {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(255, 249, 238, 0.1);
  color: rgba(247, 241, 231, 0.78);
  font-size: 0.75rem;
  font-weight: 800;
}

.style-card-examples {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.style-card-examples li {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 249, 238, 0.08);
  color: var(--hero-ink);
  font-size: 0.82rem;
  line-height: 1.35;
}

.style-section-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.style-venue-card {
  display: grid;
  grid-template-columns: minmax(220px, 0.9fr) minmax(0, 1.1fr);
  border: 1px solid rgba(30, 41, 36, 0.08);
  border-radius: var(--radius-lg);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(255, 250, 244, 0.99));
  overflow: hidden;
  box-shadow: 0 16px 36px rgba(28, 35, 32, 0.08);
}

.style-venue-media {
  position: relative;
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
  gap: 14px;
  padding: 20px;
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
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.46);
}

.shortlist-card h3,
.fit-card h3,
.alt-card h3 {
  margin: 0 0 8px;
  font-size: 1rem;
}

.shortlist-list {
  display: grid;
  gap: 12px;
  margin: 14px 0 0;
  padding: 0;
  list-style: none;
}

.shortlist-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  padding: 14px;
  border: 1px solid rgba(29, 42, 45, 0.08);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.54);
}

.shortlist-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 999px;
  background: rgba(31, 107, 104, 0.08);
  color: var(--teal);
  font-size: 0.8rem;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.shortlist-item-body {
  display: grid;
  gap: 6px;
}

.shortlist-item-body strong {
  font-size: 0.95rem;
  line-height: 1.45;
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
  padding-bottom: 4px;
  border: 1px solid rgba(30, 41, 36, 0.08);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.7);
}

.compare-table {
  width: 100%;
  min-width: 760px;
  border-collapse: collapse;
}

.compare-table th,
.compare-table td {
  padding: 14px 16px;
  border-bottom: 1px solid var(--line);
  text-align: left;
  vertical-align: top;
  background: transparent;
}

.compare-table th {
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
  background: rgba(255, 250, 244, 0.92);
}

.compare-table td strong {
  display: block;
}

.compare-venue {
  display: grid;
  gap: 4px;
}

.compare-cell-price {
  font-weight: 800;
  color: var(--teal);
}

.compare-detail-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(31, 107, 104, 0.08);
  color: var(--teal);
  text-decoration: none;
  font-size: 0.88rem;
  font-weight: 800;
  transition: transform 180ms ease, background-color 180ms ease;
}

.compare-table td[data-column-label]::before {
  content: "";
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
  padding: 24px;
  background: rgba(16, 23, 26, 0.9);
  backdrop-filter: blur(8px);
}

.lightbox[hidden] {
  display: none;
}

.lightbox-dialog {
  position: relative;
  width: min(1120px, calc(100vw - 32px));
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 14px;
  align-items: center;
}

.lightbox-frame {
  position: relative;
  margin: 0;
  background: rgba(17, 24, 26, 0.88);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 24px 54px rgba(0, 0, 0, 0.22);
}

.lightbox-image {
  display: block;
  width: 100%;
  max-height: min(80vh, 900px);
  object-fit: contain;
  background: rgba(16, 23, 26, 0.92);
}

.lightbox-caption {
  display: grid;
  gap: 8px;
  padding: 16px 18px 18px;
  color: rgba(255, 255, 255, 0.84);
  line-height: 1.6;
  background: linear-gradient(180deg, rgba(9, 13, 15, 0), rgba(9, 13, 15, 0.48));
}

.lightbox-caption-top {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
}

.lightbox-title {
  font-size: 1rem;
  color: #fff;
}

.lightbox-meta {
  font-size: 0.82rem;
  color: rgba(255, 255, 255, 0.72);
}

.lightbox-copy {
  margin: 0;
}

.lightbox-hint {
  font-size: 0.78rem;
  color: rgba(255, 255, 255, 0.64);
}

.lightbox-status {
  position: absolute;
  top: 14px;
  left: 14px;
  min-width: 56px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(16, 23, 26, 0.7);
  color: rgba(255, 255, 255, 0.92);
  font-size: 0.8rem;
  font-weight: 800;
  text-align: center;
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
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  cursor: pointer;
  font: inherit;
  font-size: 1.5rem;
  backdrop-filter: blur(8px);
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

  .hero-layout {
    grid-template-columns: 1fr;
  }

  .index-layout {
    grid-template-columns: 1fr;
  }

  .control-grid,
  .advanced-grid,
  .results-grid,
  .two-column,
  .detail-grid,
  .hero-grid,
  .style-grid,
  .style-section-grid,
  .gallery-grid,
  .photo-insight-grid,
  .status-overview-grid,
  .shortlist-grid,
  .snapshot-grid,
  .space-grid,
  .fit-grid,
  .alt-grid {
    grid-template-columns: 1fr;
  }

  .style-venue-card,
  .lightbox-dialog {
    grid-template-columns: 1fr;
  }

  .filter-guide {
    grid-template-columns: 1fr;
  }

  .style-grid,
  .shortlist-grid,
  .status-overview-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .detail-grid,
  .photo-insight-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .gallery-card-header {
    align-items: start;
  }

  .hero-panel {
    padding: 18px;
  }

  .page-toc {
    top: 10px;
    padding: 18px 20px;
  }

  .page-toc-head {
    align-items: start;
  }

  .lightbox-close {
    top: 12px;
    right: 12px;
  }
}

@media (max-width: 640px) {
  .page-shell {
    width: min(100vw - 16px, 100%);
    padding-top: 16px;
  }

  .hero,
  .surface,
  .detail-hero {
    padding: 20px;
    border-radius: 24px;
  }

  .hero h1,
  .detail-hero h1 {
    font-size: clamp(2.6rem, 14vw, 4rem);
  }

  .hero-actions,
  .detail-anchor-nav,
  .page-toc-nav {
    flex-wrap: nowrap;
    overflow-x: auto;
    padding-bottom: 4px;
    margin-right: -4px;
    scroll-snap-type: x proximity;
  }

  .quick-link,
  .detail-anchor-link,
  .page-toc-link {
    flex: 0 0 auto;
    scroll-snap-align: start;
  }

  .page-toc {
    top: 8px;
    padding: 16px;
    gap: 14px;
  }

  .page-toc-head {
    display: grid;
    gap: 12px;
  }

  .page-toc-title h2 {
    font-size: 1.3rem;
  }

  .toc-current {
    width: 100%;
    justify-content: space-between;
  }

  .venue-card {
    padding: 20px;
  }

  .style-grid,
  .shortlist-grid,
  .status-overview-grid {
    grid-auto-flow: column;
    grid-auto-columns: minmax(250px, 84vw);
    grid-template-columns: none;
    overflow-x: auto;
    padding-bottom: 4px;
    scroll-snap-type: x proximity;
  }

  .style-card,
  .shortlist-card,
  .status-overview-card {
    scroll-snap-align: start;
  }

  .advanced-filters summary {
    padding: 14px 16px;
  }

  .detail-grid,
  .photo-insight-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .photo-gallery-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
  }

  .gallery-card-header {
    flex-direction: column;
  }

  .compare-scroll {
    overflow: visible;
  }

  .compare-table {
    min-width: 0;
  }

  .compare-table thead {
    display: none;
  }

  .compare-table tbody {
    display: grid;
    gap: 12px;
  }

  .compare-table tr {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    padding: 18px;
    border: 1px solid var(--line);
    border-radius: var(--radius-lg);
    background: rgba(255, 255, 255, 0.58);
    box-shadow: var(--shadow-sm);
  }

  .compare-table td {
    display: grid;
    gap: 8px;
    padding: 0;
    border: 0;
    background: transparent;
  }

  .compare-row .compare-cell-venue,
  .compare-row .compare-cell-detail {
    grid-column: 1 / -1;
  }

  .compare-row .compare-cell-price {
    padding: 12px 14px;
    border: 1px solid rgba(31, 107, 104, 0.12);
    border-radius: 16px;
    background: rgba(31, 107, 104, 0.08);
  }

  .compare-row .compare-cell-venue::before {
    display: none;
  }

  .compare-table td[data-column-label]::before {
    content: attr(data-column-label);
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
  }

  .compare-detail-link {
    width: 100%;
    justify-content: space-between;
  }

  .lightbox {
    padding: 12px;
  }

  .lightbox-dialog {
    width: min(100vw - 4px, 100%);
    gap: 12px;
  }

  .lightbox-image {
    max-height: min(64vh, 560px);
  }

  .lightbox-nav {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    z-index: 1;
    width: 44px;
    height: 44px;
  }

  .lightbox-nav.prev {
    left: 10px;
  }

  .lightbox-nav.next {
    right: 10px;
  }
}

/* 2026 redesign overrides */
:root {
  --bg: #08111f;
  --bg-glow: rgba(105, 139, 255, 0.22);
  --ink: #eef2ff;
  --muted: #a6b4d3;
  --panel: rgba(10, 18, 36, 0.82);
  --panel-strong: rgba(14, 24, 48, 0.94);
  --line: rgba(150, 173, 255, 0.14);
  --line-strong: rgba(173, 195, 255, 0.28);
  --teal: #8fb4ff;
  --teal-soft: rgba(143, 180, 255, 0.12);
  --coral: #ffb5b7;
  --gold: #ffd28f;
  --hero-ink: #f7f8ff;
  --shadow-sm: 0 22px 48px rgba(3, 8, 20, 0.32);
  --shadow-md: 0 30px 70px rgba(2, 6, 18, 0.42);
  --shadow-lg: 0 40px 110px rgba(2, 6, 18, 0.56);
  --radius-xl: 36px;
  --radius-lg: 28px;
  --radius-sm: 18px;
}

html {
  color-scheme: dark;
}

body {
  color: var(--ink);
  background:
    radial-gradient(circle at 12% 10%, rgba(110, 147, 255, 0.32), transparent 22%),
    radial-gradient(circle at 88% 6%, rgba(255, 135, 187, 0.2), transparent 24%),
    radial-gradient(circle at 76% 78%, rgba(101, 231, 203, 0.16), transparent 26%),
    linear-gradient(180deg, #060c18 0%, #091224 34%, #0d1830 100%);
}

body::before {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.08), transparent 24%),
    radial-gradient(circle at 20% 14%, rgba(255, 255, 255, 0.1), transparent 18%),
    radial-gradient(circle at 82% 22%, rgba(144, 182, 255, 0.14), transparent 18%);
  opacity: 1;
}

body::after {
  content: "";
  position: fixed;
  inset: auto auto 6% 6%;
  width: 320px;
  height: 320px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(114, 241, 214, 0.14), transparent 68%);
  filter: blur(16px);
  pointer-events: none;
}

.page-shell {
  width: min(1360px, calc(100vw - 40px));
  padding: 36px 0 120px;
}

.hero,
.detail-hero,
.surface,
.page-toc,
.style-card,
.venue-card,
.style-venue-card,
.gallery-card,
.source-card,
.photo-gallery-item,
.shortlist-card,
.fit-card,
.alt-card,
.status-overview-card,
.snapshot-card,
.space-card,
.card-panel,
.metric,
.quick-fact,
.detail-block,
.shortlist-item,
.hero .stat {
  border-color: rgba(150, 173, 255, 0.14);
  box-shadow: var(--shadow-sm);
}

.hero,
.detail-hero {
  padding: 56px;
  background:
    linear-gradient(135deg, rgba(13, 22, 46, 0.96), rgba(19, 14, 44, 0.92) 58%, rgba(8, 52, 71, 0.9) 100%),
    radial-gradient(circle at top right, rgba(255, 210, 143, 0.18), transparent 26%);
  border: 1px solid rgba(171, 191, 255, 0.18);
  box-shadow: var(--shadow-lg);
}

.hero::before,
.detail-hero::before,
.surface::before {
  content: "";
  position: absolute;
  inset: 1px;
  border-radius: inherit;
  border: 1px solid rgba(255, 255, 255, 0.05);
  pointer-events: none;
}

.hero::after,
.surface::after,
.detail-hero::after {
  inset: auto 5% -72px auto;
  width: 260px;
  height: 260px;
  background: radial-gradient(circle, rgba(143, 180, 255, 0.2), transparent 70%);
}

.surface {
  margin-top: 28px;
  padding: 32px;
  background:
    linear-gradient(180deg, rgba(13, 21, 41, 0.88), rgba(9, 17, 34, 0.94)),
    rgba(10, 18, 36, 0.9);
  border: 1px solid rgba(150, 173, 255, 0.14);
  backdrop-filter: blur(18px);
}

.surface + .surface {
  margin-top: 24px;
}

.hero-layout {
  gap: 36px;
  grid-template-columns: minmax(0, 1.6fr) minmax(320px, 0.8fr);
  align-items: stretch;
}

.hero-copy {
  gap: 8px;
}

.hero h1,
.detail-hero h1,
.section-head h2,
.venue-card h2,
.style-card h3 {
  letter-spacing: -0.04em;
}

.hero h1,
.detail-hero h1 {
  max-width: 10ch;
  line-height: 0.9;
}

.hero-panel {
  align-content: start;
  padding: 28px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(143, 180, 255, 0.04));
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.hero-grid,
.detail-grid {
  gap: 16px;
  margin-top: 32px;
}

.hero .stat,
.quick-fact {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(143, 180, 255, 0.04));
}

.hero .stat strong,
.quick-fact strong {
  font-size: 2.1rem;
}

.eyebrow,
.card-kicker,
.detail-kicker,
.metric dt,
.control label,
.style-meta,
.price-table th,
.source-table th,
.compare-table th,
.toc-current-label {
  color: rgba(205, 217, 255, 0.78);
}

.lede,
.section-head p,
.hint,
.subtle,
.card-subtitle,
.detail-subtitle,
.gallery-source-meta,
.photo-gallery-summary-text,
.gallery-preview-hint,
.results-meta,
.status-meta,
.gallery-card p,
.source-card p,
.summary,
.style-summary-list dd,
.metric dd,
.compare-table td,
.price-table td,
.source-table td,
.photo-gallery-link,
.empty-state,
.gallery-empty {
  color: var(--muted);
}

.hero .lede,
.hero .hint,
.hero .subtle,
.hero .card-kicker,
.hero .detail-kicker,
.hero .eyebrow,
.hero-rate-note {
  color: rgba(233, 239, 255, 0.78);
}

.section-head {
  align-items: start;
  margin-bottom: 24px;
}

.section-head h2 {
  font-size: clamp(2.3rem, 3.6vw, 3.8rem);
}

.index-layout {
  gap: 28px;
  grid-template-columns: minmax(0, 1fr) 320px;
}

.page-toc {
  top: 20px;
  gap: 22px;
  padding: 24px;
  background:
    linear-gradient(180deg, rgba(17, 27, 52, 0.92), rgba(11, 18, 35, 0.98));
  border: 1px solid rgba(171, 191, 255, 0.18);
  box-shadow: var(--shadow-md);
}

.page-toc-link,
.quick-link,
.detail-anchor-link,
.toggle-chip,
.compare-detail-link,
.photo-gallery-link {
  border-color: rgba(171, 191, 255, 0.18);
  background: rgba(143, 180, 255, 0.08);
  color: var(--hero-ink);
}

.page-toc-link:hover,
.page-toc-link:focus-visible,
.quick-link:hover,
.quick-link:focus-visible,
.detail-anchor-link:hover,
.detail-anchor-link:focus-visible,
.toggle-chip:hover,
.compare-detail-link:hover,
.compare-detail-link:focus-visible {
  background: rgba(143, 180, 255, 0.16);
  border-color: rgba(201, 214, 255, 0.28);
}

.page-toc-link.is-active {
  background: linear-gradient(135deg, #99b9ff, #c4b0ff);
  border-color: transparent;
  color: #111a32;
  box-shadow: 0 14px 30px rgba(111, 144, 255, 0.32);
}

.toc-current {
  border-color: rgba(171, 191, 255, 0.16);
  background: rgba(255, 255, 255, 0.05);
}

.toc-current strong {
  color: var(--hero-ink);
}

.control input,
.control select {
  border-color: rgba(171, 191, 255, 0.18);
  background: rgba(255, 255, 255, 0.06);
  color: var(--hero-ink);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.control input::placeholder {
  color: rgba(198, 210, 246, 0.6);
}

.control input:focus,
.control select:focus {
  outline: 2px solid rgba(153, 185, 255, 0.46);
}

.advanced-filters,
.compare-scroll {
  border-color: rgba(171, 191, 255, 0.18);
  background: rgba(255, 255, 255, 0.03);
}

.advanced-filters summary {
  color: var(--hero-ink);
}

.results-meta {
  padding-top: 4px;
}

.style-grid {
  gap: 18px;
}

.style-card {
  position: relative;
  background:
    linear-gradient(180deg, rgba(20, 31, 59, 0.94), rgba(13, 22, 42, 0.98));
  border: 1px solid rgba(171, 191, 255, 0.16);
}

.style-card::before,
.venue-card::before,
.style-venue-card::before {
  content: "";
  position: absolute;
  inset: 0 0 auto 0;
  height: 4px;
  background: linear-gradient(90deg, #9cc0ff, #ffcda0, #8ff2df);
  pointer-events: none;
}

.style-card:nth-child(2n)::before,
.venue-card:nth-child(2n)::before {
  background: linear-gradient(90deg, #8ff2df, #9cc0ff, #c8b3ff);
}

.style-card:nth-child(3n)::before,
.venue-card:nth-child(3n)::before {
  background: linear-gradient(90deg, #ffcda0, #ffb6d9, #9cc0ff);
}

.style-card-media {
  min-height: 200px;
  background:
    radial-gradient(circle at top right, rgba(255, 205, 160, 0.28), transparent 26%),
    linear-gradient(135deg, rgba(99, 132, 255, 0.34), rgba(25, 93, 110, 0.52));
}

.style-card-media::after {
  background: linear-gradient(180deg, rgba(8, 12, 24, 0.02), rgba(8, 12, 24, 0.76));
}

.style-card-media-placeholder::before {
  inset: 20px;
  border-color: rgba(255, 255, 255, 0.14);
}

.style-card-media.preview-media-fallback {
  min-height: 200px;
}

.style-venue-media.preview-media-fallback,
.card-media.preview-media-fallback {
  min-height: 220px;
}

.style-card-body,
.style-venue-body,
.gallery-card,
.source-card,
.photo-gallery-item,
.shortlist-card,
.fit-card,
.alt-card,
.status-overview-card,
.snapshot-card,
.summary-card,
.space-card,
.detail-block,
.card-panel,
.metric,
.shortlist-item {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(143, 180, 255, 0.02));
}

.summary-card-emphasis {
  background: linear-gradient(180deg, rgba(143, 180, 255, 0.15), rgba(255, 255, 255, 0.04));
  border-color: rgba(143, 180, 255, 0.22);
}

.style-card-count,
.gallery-source-count,
.chip,
.badge,
.shortlist-index,
.status-pill {
  background: rgba(255, 255, 255, 0.08);
  color: var(--hero-ink);
}

.badge {
  background: rgba(255, 210, 143, 0.16);
  color: #ffe6c4;
}

.results-grid {
  gap: 22px;
}

.venue-card {
  overflow: hidden;
  gap: 20px;
  padding: 0;
  background:
    linear-gradient(180deg, rgba(14, 24, 48, 0.98), rgba(10, 18, 36, 0.98));
  border: 1px solid rgba(171, 191, 255, 0.14);
  border-top: 0;
  box-shadow: var(--shadow-md);
  transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
}

.venue-card > div,
.venue-card > p,
.venue-card > dl,
.venue-card > article {
  padding-left: 24px;
  padding-right: 24px;
}

.venue-card > :first-child {
  padding-top: 0;
}

.venue-card > :last-child {
  padding-bottom: 24px;
}

.venue-card:hover,
.venue-card:focus-within,
.style-venue-card:hover {
  transform: translateY(-4px);
  border-color: rgba(201, 214, 255, 0.24);
  box-shadow: 0 34px 82px rgba(2, 7, 18, 0.55);
}

.card-media {
  border: 0;
  border-radius: calc(var(--radius-lg) - 2px) calc(var(--radius-lg) - 2px) 0 0;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0));
}

.card-image {
  aspect-ratio: 16 / 9;
  filter: saturate(1.04) contrast(1.02);
}

.venue-card h2 {
  font-size: clamp(2rem, 3vw, 2.6rem);
}

.metric-grid,
.filter-guide,
.photo-insight-grid,
.shortlist-grid,
.fit-grid,
.alt-grid {
  gap: 14px;
}

.link-button {
  background: linear-gradient(135deg, #97b8ff, #c7b5ff 54%, #86ecd8);
  color: #111a32;
  box-shadow: 0 16px 34px rgba(111, 144, 255, 0.26);
}

.link-button.secondary {
  background: rgba(255, 255, 255, 0.06);
  color: var(--hero-ink);
  border-color: rgba(171, 191, 255, 0.18);
}

.compare-table th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: rgba(18, 28, 55, 0.96);
  color: rgba(224, 233, 255, 0.84);
}

.compare-table td {
  border-bottom-color: rgba(171, 191, 255, 0.1);
}

.compare-cell-price,
.decision-value,
.photo-gallery-summary,
.photo-gallery-link,
.compare-detail-link,
.toc-current strong {
  color: var(--hero-ink);
}

.compare-row:nth-child(2n) td {
  background: rgba(255, 255, 255, 0.025);
}

.style-venue-card {
  position: relative;
  background: linear-gradient(180deg, rgba(14, 24, 48, 0.98), rgba(10, 18, 36, 0.98));
  border-color: rgba(171, 191, 255, 0.14);
}

.gallery-card,
.source-card,
.photo-gallery-item,
.advanced-filters,
.compare-scroll,
.shortlist-item,
.empty-state,
.gallery-empty {
  border-color: rgba(171, 191, 255, 0.14);
}

.photo-gallery-item,
.shortlist-item,
.empty-state,
.gallery-empty {
  background: rgba(255, 255, 255, 0.04);
}

.gallery-preview,
.style-venue-image {
  border-color: rgba(171, 191, 255, 0.14);
}

.lightbox {
  background: rgba(4, 8, 18, 0.92);
}

.lightbox-frame {
  background: rgba(9, 15, 29, 0.96);
  border-color: rgba(255, 255, 255, 0.08);
}

@media (max-width: 980px) {
  .page-shell {
    width: min(100vw - 24px, 100%);
    padding-bottom: 96px;
  }

  .hero,
  .detail-hero,
  .surface {
    padding: 24px;
  }

  .index-layout {
    grid-template-columns: 1fr;
  }

  .page-toc {
    top: 12px;
  }

  .style-grid,
  .results-grid,
  .style-section-grid,
  .shortlist-grid,
  .fit-grid,
  .alt-grid,
  .filter-guide,
  .photo-insight-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .page-shell {
    width: min(100vw - 16px, 100%);
    padding-top: 16px;
  }

  .hero,
  .detail-hero,
  .surface {
    padding: 20px;
    border-radius: 26px;
  }

  .hero h1,
  .detail-hero h1 {
    max-width: none;
  }

  .venue-card > div,
  .venue-card > p,
  .venue-card > dl,
  .venue-card > article {
    padding-left: 18px;
    padding-right: 18px;
  }

  .venue-card > :last-child {
    padding-bottom: 18px;
  }

  .page-toc,
  .hero-actions,
  .detail-anchor-nav,
  .page-toc-nav,
  .style-grid {
    scrollbar-width: none;
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
    const titleNode = lightbox.querySelector('[data-lightbox-target="title"]');
    const metaNode = lightbox.querySelector('[data-lightbox-target="meta"]');
    const hintNode = lightbox.querySelector('[data-lightbox-target="hint"]');
    const statusNode = lightbox.querySelector('[data-lightbox-target="status"]');
    const closeNode = lightbox.querySelector("[data-lightbox-close]");
    const prevNode = lightbox.querySelector("[data-lightbox-prev]");
    const nextNode = lightbox.querySelector("[data-lightbox-next]");
    const frameNode = lightbox.querySelector(".lightbox-frame");
    let activeGroup = [];
    let activeIndex = -1;
    let lastFocusedTrigger = null;
    let touchStartX = 0;
    let touchStartY = 0;

    function render(index) {
      const trigger = activeGroup[index];
      if (!trigger || !imageNode || !captionNode) {
        return;
      }
      imageNode.src = trigger.dataset.lightboxImage || "";
      imageNode.alt = trigger.querySelector("img")?.alt || "";
      const titleText = trigger.dataset.lightboxCaptionTitle || trigger.dataset.lightboxCaption || imageNode.alt;
      const metaText = trigger.dataset.lightboxCaptionMeta || "";
      const bodyText = trigger.dataset.lightboxCaptionBody || trigger.dataset.lightboxCaption || imageNode.alt;
      if (titleNode) {
        titleNode.textContent = titleText;
      }
      if (metaNode) {
        metaNode.textContent = metaText;
      }
      captionNode.textContent = bodyText;
      if (hintNode) {
        hintNode.textContent = activeGroup.length > 1
          ? "左右滑動、方向鍵切換，點背景或按 Esc 關閉。"
          : "點背景或按 Esc 關閉。";
      }
      if (statusNode) {
        statusNode.textContent = activeGroup.length ? `${index + 1} / ${activeGroup.length}` : "";
      }
      if (prevNode) {
        prevNode.disabled = activeGroup.length <= 1;
      }
      if (nextNode) {
        nextNode.disabled = activeGroup.length <= 1;
      }
    }

    function open(trigger) {
      const groupId = trigger.dataset.lightboxGroup || trigger.dataset.lightboxImage || "";
      lastFocusedTrigger = trigger;
      activeGroup = triggers.filter((item) => {
        const itemGroup = item.dataset.lightboxGroup || item.dataset.lightboxImage || "";
        return itemGroup === groupId;
      });
      activeIndex = activeGroup.indexOf(trigger);
      if (activeIndex === -1) {
        activeGroup = [trigger];
        activeIndex = 0;
      }
      render(activeIndex);
      lightbox.hidden = false;
      document.body.classList.add("lightbox-open");
      closeNode?.focus();
    }

    function close() {
      lightbox.hidden = true;
      document.body.classList.remove("lightbox-open");
      activeGroup = [];
      activeIndex = -1;
      lastFocusedTrigger?.focus();
    }

    function step(delta) {
      if (activeIndex === -1 || !activeGroup.length) {
        return;
      }
      activeIndex = (activeIndex + delta + activeGroup.length) % activeGroup.length;
      render(activeIndex);
    }

    triggers.forEach((trigger) => {
      trigger.addEventListener("click", () => open(trigger));
    });

    closeNode?.addEventListener("click", close);
    prevNode?.addEventListener("click", () => step(-1));
    nextNode?.addEventListener("click", () => step(1));
    lightbox.addEventListener("click", (event) => {
      if (event.target === lightbox) {
        close();
      }
    });
    frameNode?.addEventListener("touchstart", (event) => {
      if (event.touches.length !== 1) {
        return;
      }
      touchStartX = event.touches[0].clientX;
      touchStartY = event.touches[0].clientY;
    }, { passive: true });
    frameNode?.addEventListener("touchend", (event) => {
      if (!event.changedTouches.length) {
        return;
      }
      const touch = event.changedTouches[0];
      const deltaX = touch.clientX - touchStartX;
      const deltaY = touch.clientY - touchStartY;
      if (Math.abs(deltaX) > 48 && Math.abs(deltaX) > Math.abs(deltaY) * 1.2) {
        step(deltaX < 0 ? 1 : -1);
      }
      touchStartX = 0;
      touchStartY = 0;
    }, { passive: true });
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

  function initHomepageToc() {
    const tocNode = document.querySelector(".page-toc");
    if (!tocNode) {
      return;
    }

    const tocCurrentLabel = document.getElementById("tocCurrentLabel");
    const linkNodes = Array.from(tocNode.querySelectorAll("[data-section-link]"));
    const sections = linkNodes.map((linkNode) => {
      const sectionId = linkNode.dataset.sectionLink || "";
      const targetNode = document.getElementById(sectionId);
      if (!sectionId || !targetNode) {
        return null;
      }
      return {
        id: sectionId,
        label: linkNode.dataset.sectionLabel || linkNode.textContent.trim(),
        linkNode,
        targetNode,
      };
    }).filter(Boolean);

    if (!sections.length) {
      return;
    }

    let activeSectionId = "";

    function setActiveSection(sectionId) {
      if (!sectionId) {
        return;
      }
      activeSectionId = sectionId;
      sections.forEach((section) => {
        const isActive = section.id === sectionId;
        section.linkNode.classList.toggle("is-active", isActive);
        if (isActive && tocCurrentLabel) {
          tocCurrentLabel.textContent = section.label;
        }
      });
    }

    const hashedSectionId = window.location.hash.replace(/^#/, "");
    setActiveSection(
      sections.some((section) => section.id === hashedSectionId)
        ? hashedSectionId
        : sections[0].id
    );

    if ("IntersectionObserver" in window) {
      const observer = new IntersectionObserver((entries) => {
        const visibleEntries = entries
          .filter((entry) => entry.isIntersecting)
          .sort((left, right) => {
            const topDelta = Math.abs(left.boundingClientRect.top) - Math.abs(right.boundingClientRect.top);
            if (topDelta !== 0) {
              return topDelta;
            }
            return right.intersectionRatio - left.intersectionRatio;
          });
        const nextEntry = visibleEntries[0];
        if (nextEntry?.target?.id && nextEntry.target.id !== activeSectionId) {
          setActiveSection(nextEntry.target.id);
        }
      }, {
        rootMargin: "-18% 0px -60% 0px",
        threshold: [0.12, 0.35, 0.7],
      });
      sections.forEach((section) => observer.observe(section.targetNode));
    }

    sections.forEach((section) => {
      section.linkNode.addEventListener("click", () => {
        setActiveSection(section.id);
      });
    });

    window.addEventListener("hashchange", () => {
      const nextId = window.location.hash.replace(/^#/, "");
      if (sections.some((section) => section.id === nextId)) {
        setActiveSection(nextId);
      }
    });
  }

  initHomepageToc();

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

  function renderStatusPill(venue) {
    if (!venue.current_status_label) {
      return "";
    }
    return `<span class="status-pill status-pill-${escapeHtml(venue.current_status_tone || "watch")}">${escapeHtml(venue.current_status_label)}</span>`;
  }

  function renderStatusNotice(venue) {
    if (!venue.current_status_headline || !venue.current_status_label) {
      return "";
    }
    const checkedAt = venue.current_status_checked_at
      ? `<p class="status-meta">最後檢查 ${escapeHtml(venue.current_status_checked_at)}</p>`
      : "";
    return `
      <div class="status-inline status-inline-${escapeHtml(venue.current_status_tone || "watch")}">
        ${renderStatusPill(venue)}
        <p class="status-summary">${escapeHtml(venue.current_status_headline)}</p>
        ${checkedAt}
      </div>
    `;
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
      <tr class="compare-row">
        <td class="compare-cell compare-cell-venue" data-column-label="場地">
          <div class="compare-venue">
            <strong>${escapeHtml(venue.name_zh)}</strong>
            <span class="subtle">${escapeHtml(venue.name_en_official)}</span>
          </div>
        </td>
        <td class="compare-cell compare-cell-price" data-column-label="公開入門價">${escapeHtml(venue.public_price_anchor_label)}</td>
        <td class="compare-cell" data-column-label="容量">${escapeHtml(venue.capacity_summary)}</td>
        <td class="compare-cell" data-column-label="雨備">${escapeHtml(venue.rain_backup_label)}</td>
        <td class="compare-cell" data-column-label="交通">${escapeHtml(venue.transport_summary)}</td>
        <td class="compare-cell" data-column-label="住宿">${escapeHtml(venue.accommodation_label)}</td>
        <td class="compare-cell compare-cell-detail" data-column-label="明細"><a class="compare-detail-link" href="venues/${escapeHtml(venue.id)}.html">查看完整檔案</a></td>
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

CURRENT_STATUS_LEVEL_LABELS = {
    "normal": "營運正常",
    "maintenance_notice": "維修／施工中",
    "limited_operations": "部分設施受限",
    "temporarily_closed": "暫停營運",
}

CURRENT_STATUS_LEVEL_TONES = {
    "normal": "ok",
    "maintenance_notice": "watch",
    "limited_operations": "watch",
    "temporarily_closed": "alert",
}

CURRENT_STATUS_RANKS = {
    "normal": 0,
    "maintenance_notice": 1,
    "limited_operations": 2,
    "temporarily_closed": 3,
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

SPACE_PRIVACY_LABELS = {
    "shared": "共享空間",
    "semi-private": "半私密",
    "private": "私密包場",
    "buyout_required": "需先包場",
}

SPACE_EVENT_SCOPE_LABELS = {
    "ceremony_only": "僅儀式",
    "ceremony_and_dinner": "儀式＋晚宴",
    "reception_only": "僅晚宴",
    "buyout_event": "買斷型活動",
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


def _space_type_label(tag: str) -> str:
    return VENUE_TYPE_LABELS.get(tag, _tag_label(tag))


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


def _current_status_label(status: dict[str, Any] | None) -> str | None:
    if not status:
        return None
    return CURRENT_STATUS_LEVEL_LABELS.get(status["level"], status["level"])


def _current_status_tone(status: dict[str, Any] | None) -> str:
    if not status:
        return "ok"
    return CURRENT_STATUS_LEVEL_TONES.get(status["level"], "watch")


def _current_status_rank(status: dict[str, Any] | None) -> int:
    if not status:
        return 0
    return CURRENT_STATUS_RANKS.get(status["level"], 1)


def _render_status_pill(label: str, tone: str) -> str:
    return (
        f'<span class="status-pill status-pill-{escape(tone)}">{escape(label)}</span>'
    )


def _render_entry_status_notice(entry: dict[str, Any]) -> str:
    headline = entry.get("current_status_headline")
    label = entry.get("current_status_label")
    if not headline or not label:
        return ""
    checked_at = entry.get("current_status_checked_at")
    tone = entry.get("current_status_tone", "watch")
    checked_line = (
        f'<p class="status-meta">最後檢查 {escape(str(checked_at))}</p>'
        if checked_at
        else ""
    )
    return (
        f'<div class="status-inline status-inline-{escape(str(tone))}">'
        f"{_render_status_pill(str(label), str(tone))}"
        f'<p class="status-summary">{escape(str(headline))}</p>'
        f"{checked_line}"
        "</div>"
    )


def _render_current_status_section(venue: dict[str, Any]) -> str:
    status = venue.get("current_status")
    if not status:
        return ""
    label = _current_status_label(status) or "營運現況待確認"
    tone = _current_status_tone(status)
    return (
        '<section class="surface" id="current-status">'
        '<div class="section-head"><h2>營運現況</h2>'
        '<p>這類公告會直接影響是否值得放進近期 shortlist，先確認能不能辦，再談風格與價格。</p></div>'
        f'<div class="status-inline status-inline-{escape(tone)}">'
        f"{_render_status_pill(label, tone)}"
        f'<p class="status-summary">{escape(status["headline"])}</p>'
        f'<p class="status-note">{escape(status["summary"])}</p>'
        f'<p class="status-meta">最後檢查 {escape(status["checked_at"])}</p>'
        "</div>"
        '<p class="hint" style="margin-top:12px;">這筆提醒已綁定到來源紀錄，正式詢價前仍建議再做一次最後確認。</p>'
        "</section>"
    )


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
    if entry["authenticity"] == "official_promotional":
        return False
    source = source_lookup.get(entry["source_id"], {})
    return source.get("source_type") != "official"


def _decision_fit_labels(venue: dict[str, Any]) -> list[str]:
    labels = []
    status = venue.get("current_status")
    if venue["supports_ceremony_and_dinner"]:
        labels.append("可辦儀式＋晚宴")
    if venue["supports_buyout"]:
        labels.append("可包場")
    if venue["supports_micro_wedding"]:
        labels.append("適合小型婚禮")
    if venue["has_indoor_backup"]:
        labels.append("有室內雨備")
    status_label = _current_status_label(status)
    if status_label and status and status["level"] != "normal":
        labels.append(status_label)
    return labels


def _decision_fit_lines(venue: dict[str, Any], photo_value_key: str) -> list[tuple[str, str]]:
    lines = [
        ("可只辦儀式", _format_bool(venue["supports_ceremony_only"])),
        ("可辦儀式＋晚宴", _format_bool(venue["supports_ceremony_and_dinner"])),
        ("可整體包場", _format_bool(venue["supports_buyout"])),
        ("適合小型婚禮", _format_bool(venue["supports_micro_wedding"])),
        ("有室內雨備", _format_bool(venue["has_indoor_backup"])),
        ("有遮蔽雨備", _format_bool(venue["has_covered_backup"])),
        ("照片參考深度", PHOTO_VALUE_LABELS[photo_value_key]),
        ("價格風險", RISK_LABELS[venue["price_risk_level"]]),
    ]
    status_label = _current_status_label(venue.get("current_status"))
    if status_label:
        lines.append(("營運現況", status_label))
    return lines


def _render_shortlist_track(title: str, description: str, entries: list[dict[str, Any]]) -> str:
    items = []
    for index, entry in enumerate(entries, start=1):
        status_suffix = ""
        if entry.get("current_status_headline") and entry.get("current_status_label"):
            status_suffix = f" / {entry['current_status_label']}"
        items.append(
            '<li class="shortlist-item">'
            f'<span class="shortlist-index">{index:02d}</span>'
            '<div class="shortlist-item-body">'
            f"<strong>{escape(entry['name_zh'])}</strong>"
            f"<span class=\"subtle\">{escape(entry['public_price_anchor_label'])} / "
            f"{escape(entry['rain_backup_label'])} / {escape(entry['transport_summary'])}"
            f"{escape(status_suffix)}</span>"
            "</div>"
            "</li>"
        )
    return (
        '<article class="shortlist-card">'
        f"<h3>{escape(title)}</h3>"
        f'<p class="subtle">{escape(description)}</p>'
        f'<ol class="shortlist-list">{"".join(items)}</ol>'
        "</article>"
    )


def _rank_shortlists(entries: list[dict[str, Any]]) -> list[tuple[str, str, list[dict[str, Any]]]]:
    logistics = sorted(
        entries,
        key=lambda entry: (
            entry["current_status_rank"],
            entry["airport_drive_time_minutes_estimate"],
            entry["traffic_risk_rank"],
            entry["accommodation_rank"],
            entry["curated_rank"],
        ),
    )[:3]
    rain = sorted(
        entries,
        key=lambda entry: (
            entry["current_status_rank"],
            entry["rain_backup_rank"],
            not entry["has_indoor_backup"],
            entry["curated_rank"],
        ),
    )[:3]
    scale = sorted(
        entries,
        key=lambda entry: (
            entry["current_status_rank"],
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
                entry["current_status_rank"],
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
        '<section class="surface" id="shortlist-section">'
        '<div class="section-head">'
        "<h2>快速初篩路線</h2>"
        '<p>先用最常見的淘汰條件做第一輪：交通、雨備、桌數與公開入門價。</p>'
        "</div>"
        f'<div class="shortlist-grid">{cards}</div>'
        "</section>"
    )


def _render_status_overview(entries: list[dict[str, Any]]) -> str:
    status_entries = [
        entry
        for entry in entries
        if entry.get("current_status_headline") and entry.get("current_status_label")
    ]
    if not status_entries:
        return ""
    status_entries = sorted(
        status_entries,
        key=lambda entry: (
            -entry["current_status_rank"],
            entry["curated_rank"],
        ),
    )
    cards = []
    for entry in status_entries:
        checked_at = (
            f'最後檢查 {escape(str(entry["current_status_checked_at"]))}'
            if entry.get("current_status_checked_at")
            else "最後檢查日期待補"
        )
        cards.append(
            '<article class="status-overview-card">'
            '<div class="status-overview-top">'
            '<div>'
            f'<p class="eyebrow">{escape(entry["region"])} / {escape(entry["recommended_guest_size_band"])}</p>'
            f'<h3>{escape(entry["name_zh"])}</h3>'
            f'<p class="subtle">{escape(entry["name_en_official"])}</p>'
            "</div>"
            f'{_render_status_pill(entry["current_status_label"], entry["current_status_tone"])}'
            "</div>"
            f'<p class="status-summary">{escape(entry["current_status_headline"])}</p>'
            f'<p class="hint">{escape(entry.get("current_status_summary") or entry["price_summary_text"])}</p>'
            '<div class="detail-actions">'
            f'<span class="subtle">{checked_at}</span>'
            f'<a class="link-button secondary" href="venues/{escape(entry["id"])}.html">查看現況與場地檔案</a>'
            "</div>"
            "</article>"
        )
    return (
        '<section class="surface" id="status-overview">'
        '<div class="section-head"><h2>近期營運現況</h2>'
        '<p>像停修、局部限制、重新主打的新空間這類變化，會直接影響這批場地值不值得放進近期 shortlist。</p></div>'
        f'<div class="status-overview-grid">{"".join(cards)}</div>'
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
        cover = (
            _render_preview_media(
                style_entries[0],
                container_class="style-card-media",
                image_class="style-card-image",
                placeholder_class="style-card-media-placeholder",
                alt_text=f'{definition["label"]}代表場地照片',
            )
            if style_entries
            else '<div class="style-card-media style-card-media-placeholder"></div>'
        )
        example_items = "".join(
            f"<li>{escape(entry['name_zh'])}</li>"
            for entry in style_entries[:3]
        ) or "<li>目前尚未歸類到這一型</li>"
        cards.append(
            '<article class="style-card">'
            f"{cover}"
            '<div class="style-card-body">'
            '<div class="style-card-top">'
            f'<p class="eyebrow">{escape(definition["label"])}</p>'
            f'<span class="style-card-count">{len(style_entries)} 個場地</span>'
            "</div>"
            f'<h3>{escape(definition["label"])}</h3>'
            f'<p class="summary">{escape(definition["description"])}</p>'
            '<p class="style-meta">代表場地</p>'
            f'<ul class="style-card-examples">{example_items}</ul>'
            f'<a class="link-button secondary" href="#style-{escape(definition["key"])}">直接看這一類</a>'
            "</div>"
            "</article>"
        )
    return (
        '<section class="surface" id="style-overview">'
        '<div class="section-head"><h2>依場地類型開始挑</h2>'
        '<p>首頁先只回答一件事：你們要的是哪一種畫面。先選類型，再進單一飯店頁看價格、雨備、交通與真實照片。</p></div>'
        f'<div class="style-grid">{"".join(cards)}</div>'
        "</section>"
    )


def _render_index_toc(entries: list[dict[str, Any]]) -> str:
    grouped = _entries_by_style(entries)
    style_nav = "".join(
        '<a class="page-toc-link" '
        f'href="#style-{escape(definition["key"])}" '
        f'data-section-link="style-{escape(definition["key"])}" '
        f'data-section-label="{escape(definition["label"])}">'
        f'{escape(definition["label"])} · {len(grouped.get(definition["key"], []))}'
        "</a>"
        for definition in WEDDING_STYLE_DEFINITIONS
    )
    return (
        '<section class="surface page-toc" id="page-toc">'
        '<div class="page-toc-head">'
        '<div class="page-toc-title">'
        '<p class="eyebrow">Wedding Types</p>'
        "<h2>右側類型導覽</h2>"
        '<p class="summary">先用教堂、叢林、懸崖、水上平台、沙灘等類型定方向，再回頭比價格、雨備與交通。</p>'
        "</div>"
        '<div class="toc-current">'
        '<span class="toc-current-label">目前區塊</span>'
        '<strong id="tocCurrentLabel">教堂</strong>'
        "</div>"
        "</div>"
        '<div class="page-toc-groups">'
        '<div class="toc-group">'
        '<p class="subtle">婚禮類型</p>'
        f'<nav class="page-toc-nav" aria-label="首頁內容目錄">{style_nav}</nav>'
        "</div>"
        "</div>"
        "</section>"
    )


def _render_style_spotlight(entry: dict[str, Any]) -> str:
    cover = _render_preview_media(
        entry,
        container_class="style-venue-media",
        image_class="style-venue-image",
        alt_text=entry["name_zh"],
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
            '<tr class="compare-row">'
            '<td class="compare-cell compare-cell-venue" data-column-label="場地">'
            '<div class="compare-venue">'
            f"<strong>{escape(entry['name_zh'])}</strong>"
            f"<span class=\"subtle\">{escape(entry['name_en_official'])}</span>"
            "</div>"
            "</td>"
            f'<td class="compare-cell compare-cell-price" data-column-label="公開入門價">{escape(entry["public_price_anchor_label"])}</td>'
            f'<td class="compare-cell" data-column-label="容量">{escape(entry["capacity_summary"])}</td>'
            f'<td class="compare-cell" data-column-label="雨備">{escape(entry["rain_backup_label"])}</td>'
            f'<td class="compare-cell" data-column-label="交通">{escape(entry["transport_summary"])}</td>'
            f'<td class="compare-cell" data-column-label="住宿">{escape(entry["accommodation_label"])}</td>'
            f'<td class="compare-cell compare-cell-detail" data-column-label="明細"><a class="compare-detail-link" href="venues/{escape(entry["id"])}.html">查看完整檔案</a></td>'
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
        '<section class="surface" id="decision-fit">'
        '<div class="section-head"><h2>決策適配</h2>'
        '<p>把結構條件攤平看，確認它能不能真的支撐你們想要的婚禮形式。</p></div>'
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


def _render_detail_snapshot(venue: dict[str, Any], photo_value_key: str) -> str:
    public_price_anchor_label, _ = _public_price_anchor(venue)
    concern_text = (
        venue["open_questions"][0]
        if venue["open_questions"]
        else (venue["key_risks"][0] if venue["key_risks"] else "目前沒有整理到額外的阻礙點。")
    )
    cards = [
        ("公開入門價", public_price_anchor_label),
        ("容量輪廓", _capacity_summary(venue)),
        ("雨備結論", f'{RAIN_BACKUP_LABELS[venue["rain_backup_status"]]}｜{venue["backup_space_description"]}'),
        ("交通／住宿", f'{_transport_summary(venue)}｜{ACCOMMODATION_LABELS[venue["accommodation_fit"]]}'),
    ]
    cards_html = "".join(
        '<article class="summary-card">'
        f'<p class="subtle">{escape(label)}</p>'
        f'<p class="summary">{escape(value)}</p>'
        "</article>"
        for label, value in cards
    )
    return (
        '<section class="surface decision-snapshot" id="decision-summary">'
        '<div class="section-head"><h2>決策摘要</h2>'
        '<p>先判斷這間場地有沒有 shortlist 資格，再決定要不要投入時間深查細節與照片。</p></div>'
        f'<div class="snapshot-grid">{cards_html}'
        '<article class="summary-card summary-card-emphasis">'
        '<p class="subtle">第一個要追問的點</p>'
        f'<p class="summary">{escape(concern_text)}</p>'
        f'<p class="hint">照片參考深度：{escape(PHOTO_VALUE_LABELS[photo_value_key])}</p>'
        "</article>"
        "</div>"
        "</section>"
    )


def _render_wedding_spaces(venue: dict[str, Any]) -> str:
    wedding_spaces = venue.get("wedding_spaces", [])
    if not wedding_spaces:
        return ""
    cards = []
    for space in wedding_spaces:
        type_badges = "".join(
            _badge(_space_type_label(tag))
            for tag in space["space_types"]
        )
        cards.append(
            '<article class="space-card">'
            f'<h3>{escape(space["label"])}</h3>'
            f'<div class="chip-row">{_badge(SPACE_PRIVACY_LABELS[space["privacy_level"]], tone="badge")}'
            f'{_badge(SPACE_EVENT_SCOPE_LABELS[space["event_scope"]], tone="badge")}'
            f"{type_badges}</div>"
            '<dl class="space-summary">'
            f'<div><dt>適合規模</dt><dd>{escape(space["capacity_summary_text"])}</dd></div>'
            f'<div><dt>價格輪廓</dt><dd>{escape(space["price_summary_text"])}</dd></div>'
            f'<div><dt>雨備方向</dt><dd>{escape(space["backup_summary_text"])}</dd></div>'
            "</dl>"
            f'<p class="summary">{escape(space["decision_notes"])}</p>'
            "</article>"
        )
    return (
        '<section class="surface">'
        '<div class="section-head"><h2>婚禮空間比較</h2>'
        '<p>同一間飯店內常常同時有公開型、私密型與包場型玩法；這裡先把真正影響決策的空間拆開看。</p></div>'
        f'<div class="space-grid">{"".join(cards)}</div>'
        "</section>"
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
    cover = _render_preview_media(
        entry,
        container_class="card-media",
        image_class="card-image",
        alt_text=entry["name_zh"],
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
        '<div class="chip-row">'
        + "".join(
            _badge(label, tone="badge")
            for label in entry["decision_fit_labels"]
        )
        + "</div>"
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
        '<div class="price-table-wrap"><table class="price-table">'
        "<thead><tr>"
        "<th>方案</th><th>價格</th><th>年份</th><th>包含項目</th><th>可信度</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table></div>"
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


def _index_preview_source(
    photo_entries: list[dict[str, Any]],
    photo_assets_by_entry: dict[str, list[str]],
    source_lookup: dict[str, dict[str, Any]],
) -> tuple[str | None, str | None]:
    for entry in _visible_photo_entries(photo_entries, photo_assets_by_entry, source_lookup):
        source = source_lookup.get(entry["source_id"], {})
        return str(entry["page_url"]), str(source.get("source_name", "照片來源"))
    for source in source_lookup.values():
        return str(source["source_url"]), str(source.get("source_name", "來源頁"))
    return None, None


def _render_preview_media(
    entry: dict[str, Any],
    *,
    container_class: str,
    image_class: str,
    placeholder_class: str = "",
    alt_text: str,
) -> str:
    classes = " ".join(
        part for part in [container_class, placeholder_class, "preview-media-fallback"] if part
    )
    if entry.get("cover_photo_url"):
        return (
            f'<div class="{escape(container_class)}">'
            f'<img class="{escape(image_class)}" src="{escape(str(entry["cover_photo_url"]))}" alt="{escape(alt_text)}" loading="lazy">'
            "</div>"
        )
    actions = []
    if entry.get("preview_source_url"):
        actions.append(
            f'<a class="preview-media-link" href="{escape(str(entry["preview_source_url"]))}" target="_blank" rel="noreferrer">照片來源</a>'
        )
    if entry.get("official_website"):
        actions.append(
            f'<a class="preview-media-link" href="{escape(str(entry["official_website"]))}" target="_blank" rel="noreferrer">官方網站</a>'
        )
    if not actions:
        return f'<div class="{escape(" ".join(part for part in [container_class, placeholder_class] if part))}"></div>'
    source_name = entry.get("preview_source_name")
    note = "目前沒有快取照片，可先看來源頁或官方網站。"
    if source_name:
        note = f"目前沒有快取照片，可先看 {source_name} 或官方網站。"
    return (
        f'<div class="{escape(classes)}">'
        '<div class="preview-media-content">'
        '<p class="preview-media-kicker">Preview</p>'
        f'<p class="preview-media-note">{escape(note)}</p>'
        f'<div class="preview-media-actions">{"".join(actions)}</div>'
        "</div>"
        "</div>"
    )


def _photo_gallery_items(
    photo_entries: list[dict[str, Any]],
    photo_assets_by_entry: dict[str, list[str]],
    source_lookup: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for entry in _visible_photo_entries(photo_entries, photo_assets_by_entry, source_lookup):
        preview_urls = _photo_preview_urls(entry, photo_assets_by_entry)
        source = source_lookup.get(entry["source_id"], {})
        source_name = str(source.get("source_name", entry["photo_entry_id"]))
        source_type_label = SOURCE_TYPE_LABELS.get(
            str(source.get("source_type", "")),
            "來源類型待確認",
        )
        authenticity_label = PHOTO_AUTHENTICITY_LABELS.get(
            entry["authenticity"],
            entry["authenticity"],
        )
        image_type_label = IMAGE_TYPE_LABELS.get(entry["image_type"], entry["image_type"])
        decision_label = DECISION_VALUE_LABELS.get(
            entry["decision_value"],
            entry["decision_value"],
        )
        scene_labels = [_tag_label(tag) for tag in entry["scene_tags"][:3]]
        title = " · ".join(scene_labels[:2]) if scene_labels else source_name
        summary = scene_labels[2] if len(scene_labels) > 2 else image_type_label
        badges = [
            _badge(authenticity_label),
            _badge(image_type_label),
            _badge(source_type_label),
            _badge(decision_label, tone="badge"),
        ] + [_badge(label) for label in scene_labels]
        if not preview_urls:
            items.append(
                {
                    "url": "",
                    "title": title,
                    "summary": "目前缺少本地快取圖，請直接開啟來源頁查看完整相簿。",
                    "meta": f"{authenticity_label} · {image_type_label} · {source_name}",
                    "details": str(entry["decision_notes"]),
                    "badges_html": "".join(badges),
                    "source_link": str(entry["page_url"]),
                    "source_name": source_name,
                    "aria_label": "",
                }
            )
            continue
        for index, url in enumerate(preview_urls, start=1):
            items.append(
                {
                    "url": url,
                    "title": title,
                    "summary": summary,
                    "meta": f"{authenticity_label} · {image_type_label} · {source_name}",
                    "details": str(entry["decision_notes"]),
                    "badges_html": "".join(badges),
                    "source_link": str(entry["page_url"]),
                    "source_name": source_name,
                    "aria_label": (
                        f"{title}，第 {index} 張照片，來源 {source_name}，點擊放大"
                    ),
                }
            )
    return items


def _render_photo_cards(
    photo_entries: list[dict[str, Any]],
    photo_assets_by_entry: dict[str, list[str]],
    source_lookup: dict[str, dict[str, Any]],
) -> str:
    gallery_items = _photo_gallery_items(photo_entries, photo_assets_by_entry, source_lookup)
    if not gallery_items:
        return '<div class="empty-state">目前還沒有整理到可參考的照片來源。</div>'
    has_preview = any(item["url"] for item in gallery_items)
    cards = []
    for item in gallery_items:
        if item["url"]:
            preview = (
                '<button type="button" class="gallery-preview-button" '
                f'data-lightbox-image="{escape(item["url"])}" '
                'data-lightbox-group="venue-gallery" '
                f'data-lightbox-caption="{escape(item["details"])}" '
                f'data-lightbox-caption-title="{escape(item["title"])}" '
                f'data-lightbox-caption-meta="{escape(item["meta"])}" '
                f'data-lightbox-caption-body="{escape(item["details"])}" '
                f'aria-label="{escape(item["aria_label"])}">'
                f'<img class="gallery-preview" src="{escape(item["url"])}" alt="{escape(item["title"])}" loading="lazy">'
                '<span class="gallery-preview-overlay">查看大圖</span>'
                "</button>"
            )
        else:
            preview = (
                f'<a class="gallery-preview-fallback" href="{escape(item["source_link"])}" target="_blank" rel="noreferrer">'
                '<span class="gallery-preview-fallback-kicker">暫無本地預覽</span>'
                '<strong>開啟來源相簿</strong>'
                f'<span>{escape(item["source_name"])}</span>'
                "</a>"
            )
        cards.append(
            '<article class="photo-gallery-item">'
            + preview
            + '<div class="photo-gallery-meta">'
            f'<h3 class="photo-gallery-title">{escape(item["title"])}</h3>'
            f'<p class="photo-gallery-summary-text">{escape(item["summary"])}</p>'
            "</div>"
            '<details class="photo-gallery-details">'
            '<summary class="photo-gallery-summary">查看照片資訊</summary>'
            f'<div class="chip-row">{item["badges_html"]}</div>'
            f'<p>{escape(item["details"])}</p>'
            f'<a class="photo-gallery-link" href="{escape(item["source_link"])}" target="_blank" rel="noreferrer">來源：{escape(item["source_name"])}</a>'
            "</details>"
            "</article>"
        )
    return (
        '<div class="photo-gallery-grid">'
        + "".join(cards)
        + (
            '</div><p class="gallery-preview-hint">點圖可放大；全部照片會放在同一個 lightbox 內左右切換。沒有本地快取圖的來源會直接連到原始相簿。</p>'
            if has_preview
            else '</div><p class="gallery-preview-hint">目前缺少本地快取圖，請直接開啟來源相簿查看照片。</p>'
        )
    )


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
        '<div class="lightbox-status" data-lightbox-target="status"></div>'
        '<figcaption class="lightbox-caption">'
        '<div class="lightbox-caption-top">'
        '<strong class="lightbox-title" data-lightbox-target="title"></strong>'
        '<span class="lightbox-meta" data-lightbox-target="meta"></span>'
        "</div>"
        '<p class="lightbox-copy" data-lightbox-target="caption"></p>'
        '<div class="lightbox-hint" data-lightbox-target="hint"></div>'
        "</figcaption>"
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
    status_nav_link = ""
    if venue.get("current_status"):
        status_nav_link = '<a class="detail-anchor-link" href="#current-status">營運現況</a>'
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
        '<nav class="detail-anchor-nav" aria-label="場地檔案快速跳轉">'
        f"{status_nav_link}"
        '<a class="detail-anchor-link" href="#decision-summary">決策摘要</a>'
        '<a class="detail-anchor-link" href="#decision-fit">決策適配</a>'
        '<a class="detail-anchor-link" href="#detail-scan">快速掃描</a>'
        '<a class="detail-anchor-link" href="#price-breakdown">價格條目</a>'
        '<a class="detail-anchor-link" href="#photo-gallery">照片參考</a>'
        '<a class="detail-anchor-link" href="#restrictions">限制事項</a>'
        "</nav>"
        '<div class="detail-grid">'
        f"{facts_html}"
        "</div>"
        "</section>"
        f"{_render_current_status_section(venue)}"
        f"{_render_detail_snapshot(venue, str(photo_stats['photo_value_key']))}"
        f"{_render_decision_fit(venue, str(photo_stats['photo_value_key']))}"
        '<section class="surface" id="detail-scan">'
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
        f"{_render_wedding_spaces(venue)}"
        '<section class="surface" id="price-breakdown">'
        '<div class="section-head"><h2>價格條目</h2>'
        '<p>先用公開可見的方案底價做比較；下表主欄位已換算台幣，原始幣別保留在同列方便對照。</p></div>'
        f'<p class="hint" style="margin-bottom:16px;">{escape(FX_NOTE_TEXT)}</p>'
        f"{_render_price_table(venue['price_entries'])}"
        "</section>"
        '<section class="surface" id="restrictions">'
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
        '<section class="surface" id="photo-gallery">'
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
    current_status = venue.get("current_status")
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
                *( [current_status["headline"], current_status["summary"]] if current_status else [] ),
                *[
                    part
                    for space in venue.get("wedding_spaces", [])
                    for part in [
                        space["label"],
                        *space["space_types"],
                        space["capacity_summary_text"],
                        space["price_summary_text"],
                        space["decision_notes"],
                    ]
                ],
            ]
        )
    )
    return {
        "id": venue["id"],
        "name_zh": venue["name_zh"],
        "name_en_official": venue["name_en_official"],
        "official_website": venue["official_website"],
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
        "current_status_label": _current_status_label(current_status),
        "current_status_headline": current_status["headline"] if current_status else None,
        "current_status_summary": current_status["summary"] if current_status else None,
        "current_status_checked_at": current_status["checked_at"] if current_status else None,
        "current_status_tone": _current_status_tone(current_status),
        "current_status_rank": _current_status_rank(current_status),
        "curated_rank": curated_rank,
        "search_text": search_text,
        "cover_photo_url": None,
        "preview_source_url": None,
        "preview_source_name": None,
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
        (
            updated["preview_source_url"],
            updated["preview_source_name"],
        ) = _index_preview_source(
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
        '<div class="hero-layout">'
        '<div class="hero-copy">'
        '<p class="eyebrow">Bali Wedding Research</p>'
        "<h1>先從場地類型選，再決定要深挖哪一間飯店</h1>"
        '<p class="lede">首頁先把峇里島婚禮場地拆成教堂、叢林、水上平台、懸崖、沙灘與室內，再進飯店頁看價格、雨備、交通、住宿與真實照片。</p>'
        '<nav class="hero-actions" aria-label="首頁快速跳轉">'
        '<a class="quick-link" href="#style-overview">看場地類型</a>'
        '<a class="quick-link" href="#filter-panel">用條件篩選</a>'
        '<a class="quick-link" href="#compare-section">看全部比較</a>'
        '<a class="quick-link" href="#card-section">看飯店卡片</a>'
        "</nav>"
        "</div>"
        '<aside class="hero-panel">'
        '<p class="eyebrow">首頁使用方式</p>'
        '<ol class="hero-list">'
        '<li>先從場地類型找畫面方向。</li>'
        '<li>再用交通、雨備、住宿與人數條件過濾。</li>'
        '<li>最後進單一飯店頁看空間差異、價格與真實照片。</li>'
        "</ol>"
        '<p class="hint">近期維修與營運提醒會收在各飯店頁，不在首頁另外拉成獨立章節。</p>'
        "</aside>"
        "</div>"
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
        f'<p class="hint hero-rate-note">{escape(FX_NOTE_TEXT)}</p>'
        "</section>"
        '<div class="index-layout">'
        '<div class="index-main">'
        f"{_render_style_nav(entries)}"
        '<section class="surface" id="filter-panel">'
        '<div class="section-head">'
        "<h2>交叉篩選飯店</h2>"
        '<p>先按場地類型選方向，再用區域、人數、雨備與住宿條件交叉過濾，首頁不要一次塞太多判斷。</p>'
        "</div>"
        '<div class="control-grid">'
        '<div class="control"><label for="searchInput">搜尋</label>'
        '<input id="searchInput" type="search" placeholder="可搜飯店名稱、區域、場地類型與適合對象"></div>'
        '<div class="control"><label for="regionFilter">區域</label>'
        f'<select id="regionFilter">{_render_select_options(region_values)}</select></div>'
        '<div class="control"><label for="typeFilter">場地類型</label>'
        f'<select id="typeFilter">{_render_select_options(style_values, labels=WEDDING_STYLE_LABELS)}</select></div>'
        '<div class="control"><label for="guestFilter">適合人數帶</label>'
        f'<select id="guestFilter">{_render_select_options(guest_values)}</select></div>'
        "</div>"
        '<details class="advanced-filters"><summary>更多條件與排序</summary>'
        '<div class="advanced-grid">'
        '<div class="control"><label for="priceFilter">價格級距</label>'
        f'<select id="priceFilter">{_render_select_options(price_values, labels=PRICE_BAND_LABELS)}</select></div>'
        '<div class="control"><label for="rainFilter">雨備能力</label>'
        f'<select id="rainFilter">{_render_select_options(rain_values, labels=RAIN_BACKUP_LABELS)}</select></div>'
        '<div class="control"><label for="stayFilter">住宿整合</label>'
        f'<select id="stayFilter">{_render_select_options(stay_values, labels=ACCOMMODATION_LABELS)}</select></div>'
        '<div class="control"><label for="sortSelect">排序方式</label>'
        '<select id="sortSelect"><option value="curated">編輯排序</option><option value="starting-price">公開入門價最低</option><option value="airport-time">距機場最短</option><option value="dinner-capacity">晚宴容量最大</option><option value="rain-readiness">雨備最強</option><option value="photo-depth">照片線索最多</option></select></div>'
        "</div>"
        '<div class="toggle-grid advanced-toggle-grid">'
        '<label class="toggle-chip" for="dinnerFilter"><input id="dinnerFilter" type="checkbox">只看可辦儀式＋晚宴</label>'
        '<label class="toggle-chip" for="indoorFilter"><input id="indoorFilter" type="checkbox">只看有室內雨備</label>'
        '<label class="toggle-chip" for="buyoutFilter"><input id="buyoutFilter" type="checkbox">只看可包場</label>'
        '<label class="toggle-chip" for="microFilter"><input id="microFilter" type="checkbox">只看適合小型婚禮</label>'
        "</div>"
        "</details>"
        '<div class="results-meta">'
        '<span id="resultCount">'
        f"{len(entries)} / {len(entries)} 個場地顯示中"
        "</span>"
        f'<span>{escape(", ".join(totals["regions"]))}</span>'
        "</div>"
        '</section>'
        '<section class="surface" id="compare-section">'
        '<div class="section-head"><h2>全部場地比較</h2>'
        '<p>這裡只保留最影響 shortlist 的橫向條件，近期現況改放各飯店頁內文專注描述。</p></div>'
        '<div class="compare-scroll"><table class="compare-table"><thead><tr><th>場地</th><th>公開入門價</th><th>容量</th><th>雨備</th><th>交通</th><th>住宿</th><th>明細</th></tr></thead><tbody id="compareBody">'
        f"{compare_rows}"
        '</tbody></table></div>'
        "</section>"
        '<section class="surface" id="card-section">'
        '<div class="section-head"><h2>場地卡片</h2>'
        '<p>這裡再看每間飯店的定位、適合對象與資料密度；真正的維修、限制與空間差異，請進單一飯店頁深看。</p></div>'
        '<div id="results" class="results-grid">'
        f"{card_html}"
        "</div>"
        '<div id="emptyState" class="empty-state" hidden>目前沒有場地符合這組篩選條件。</div>'
        "</section>"
        f"{_render_style_sections(entries)}"
        "</div>"
        '<aside class="index-sidebar">'
        f"{_render_index_toc(entries)}"
        "</aside>"
        "</div>"
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
