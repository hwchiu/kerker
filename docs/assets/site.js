(function () {
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
      .replaceAll("\"", "&quot;")
      .replaceAll("'", "&#39;");
  }

  function normalizeText(value) {
    return String(value)
      .toLowerCase()
      .normalize("NFKD")
      .replace(/[̀-ͯ]/g, "")
      .replace(/[^0-9a-z㐀-鿿]+/g, " ")
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
        ${renderStatusNotice(venue)}
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
    const statusCell = venue.current_status_headline && venue.current_status_label
      ? `
        <div class="compare-status">
          ${renderStatusPill(venue)}
          <span class="subtle">${escapeHtml(venue.current_status_headline)}</span>
        </div>
      `
      : '<span class="subtle">未見現況警示</span>';
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
        <td class="compare-cell" data-column-label="現況">${statusCell}</td>
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
