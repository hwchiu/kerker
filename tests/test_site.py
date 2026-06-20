import tempfile
import threading
import unittest
from copy import deepcopy
from pathlib import Path
from urllib.request import urlopen

from bali_wedding_research.io import write_json_file
from bali_wedding_research.paths import ensure_workspace_layout, workspace_paths
from bali_wedding_research.site import (
    build_site_server,
    write_pages_site,
    write_static_site,
)
from tests.sample_data import photo_records, source_record, venue_record


class StaticSiteTest(unittest.TestCase):
    def _write_workspace(self, root: Path) -> dict[str, Path]:
        ensure_workspace_layout(root)
        paths = workspace_paths(root)
        source = source_record()
        source["source_type"] = "platform_agency"
        write_json_file(paths["sources"] / "example.json", source)
        write_json_file(paths["photos"] / "example.json", photo_records())
        write_json_file(paths["venues"] / "example.json", venue_record())
        return paths

    def _write_workspace_with_similar_venue(self, root: Path) -> dict[str, Path]:
        ensure_workspace_layout(root)
        paths = workspace_paths(root)
        source_a = source_record()
        source_a["source_type"] = "platform_agency"
        source_b = deepcopy(source_record())
        source_b["source_id"] = "example-garden-official"
        source_b["venue_id"] = "example-garden-resort"
        source_b["source_type"] = "platform_agency"
        source_b["source_name"] = "Example Garden Weddings"
        source_b["source_url"] = "https://example.com/garden/weddings"

        photos_a = photo_records()
        photos_b = deepcopy(photo_records())
        for index, photo in enumerate(photos_b, start=1):
            photo["photo_entry_id"] = f"example-garden-photo-{index}"
            photo["venue_id"] = "example-garden-resort"
            photo["source_id"] = "example-garden-official"
            photo["page_url"] = f"https://example.com/garden/gallery/{index}"
            photo["image_url_or_gallery_url"] = f"https://example.com/garden/images/{index}.jpg"

        venue_a = venue_record()
        venue_a["price_entries"].append(
            {
                "label": "Reception package",
                "currency": "IDR",
                "amount_min": 260000000,
                "amount_max": None,
                "pricing_year": 2020,
                "includes_stay": True,
                "includes_decoration": True,
                "includes_dinner": True,
                "includes_tax_service": False,
                "conditions_text": "Historic package reference",
                "confidence": "low",
            }
        )
        venue_b = deepcopy(venue_record())
        venue_b["id"] = "example-garden-resort"
        venue_b["name_zh"] = "範例花園度假村"
        venue_b["name_en_official"] = "Example Garden Resort"
        venue_b["official_website"] = "https://example.com/garden"
        venue_b["maps_url"] = "https://maps.example.com/garden"
        venue_b["primary_visual_identity"] = "Cliffside garden resort with a softer dinner atmosphere"
        venue_b["venue_types"] = ["cliffside", "garden"]
        venue_b["reception_space_types"] = ["garden", "private-dining"]
        venue_b["price_summary_text"] = "Public ceremony package starts at USD 7,500"
        venue_b["price_entries"][0]["amount_min"] = 7500
        venue_b["price_entries"][0]["label"] = "Garden ceremony package"
        venue_b["price_risk_level"] = "low"
        venue_b["price_band_normalized"] = None
        venue_b["source_ids"] = ["example-garden-official"]
        venue_b["photo_index_id"] = "example-garden-resort"

        write_json_file(paths["sources"] / "records.json", [source_a, source_b])
        write_json_file(paths["photos"] / "records.json", photos_a + photos_b)
        write_json_file(paths["venues"] / "records.json", [venue_a, venue_b])
        return paths

    def test_write_static_site_outputs_search_and_detail_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_workspace_with_similar_venue(root)
            output_dir = root / "site"

            written = write_static_site(root, output_dir)

            self.assertEqual(
                written,
                [
                    output_dir / "index.html",
                    output_dir / "assets" / "site.css",
                    output_dir / "assets" / "site.js",
                    output_dir / "venues" / "example-cliffside-resort.html",
                    output_dir / "venues" / "example-garden-resort.html",
                ],
            )
            index_html = (output_dir / "index.html").read_text(encoding="utf-8")
            detail_html = (
                output_dir / "venues" / "example-cliffside-resort.html"
            ).read_text(encoding="utf-8")

            self.assertIn("範例懸崖度假村", index_html)
            self.assertIn("Example Cliffside Resort", index_html)
            self.assertIn("依場地類型開始挑", index_html)
            self.assertIn('href="#style-chapel"', index_html)
            self.assertIn("教堂", index_html)
            self.assertIn("公開價格已統一換算為台幣", index_html)
            self.assertIn("公開方案約 NT$269,068 起", index_html)
            self.assertNotIn("Public ceremony package starts at USD 8,500", index_html)
            self.assertIn("全部場地比較", index_html)
            self.assertIn("交叉篩選飯店", index_html)
            self.assertIn("sortSelect", index_html)
            self.assertNotIn("近期營運現況", index_html)
            self.assertLess(index_html.index("場地卡片"), index_html.index('id="style-chapel"'))
            self.assertIn("Example Cliffside Weddings", detail_html)
            self.assertIn("https://example.com/cliffside/gallery/1", detail_html)
            self.assertIn("Confirm corkage fees for external alcohol", detail_html)
            self.assertIn("決策摘要", detail_html)
            self.assertIn("決策適配", detail_html)
            self.assertIn("相近替代場地", detail_html)
            self.assertIn("Example Garden Resort", detail_html)
            self.assertIn('class="gallery-preview"', detail_html)
            self.assertIn('data-lightbox-image="https://example.com/images/1.jpg"', detail_html)
            self.assertIn('data-lightbox-group="venue-gallery"', detail_html)
            self.assertIn('id="photoLightbox"', detail_html)
            self.assertIn('data-lightbox-target="status"', detail_html)
            self.assertIn('src="https://example.com/images/1.jpg"', detail_html)
            self.assertIn('class="photo-gallery-details"', detail_html)
            self.assertIn("來源：Example Cliffside Weddings", detail_html)
            self.assertIn("NT$269,068", detail_html)
            self.assertIn("NT$461,500", detail_html)
            self.assertIn("約原幣 USD 8,500", detail_html)
            self.assertIn("約原幣 IDR 260,000,000", detail_html)
            self.assertNotIn("Public ceremony package starts at USD 8,500", detail_html)
            self.assertNotIn("婚禮空間比較", detail_html)

    def test_write_static_site_renders_wedding_spaces_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paths = self._write_workspace(root)
            venue = venue_record()
            venue["wedding_spaces"] = [
                {
                    "space_id": "chapel-main",
                    "label": "寶格麗教堂",
                    "space_types": ["chapel"],
                    "privacy_level": "shared",
                    "event_scope": "ceremony_only",
                    "capacity_summary_text": "儀式最多 90 人",
                    "price_summary_text": "公開教堂方案適合把雨備放在第一順位的新娘",
                    "backup_summary_text": "本身就是室內儀式空間，雨備最穩。",
                    "decision_notes": "重視品牌感與天候穩定時，最容易 shortlist。",
                },
                {
                    "space_id": "mansion-water-stage",
                    "label": "總裁豪宅私人水台",
                    "space_types": ["water-platform", "villa-buyout"],
                    "privacy_level": "private",
                    "event_scope": "buyout_event",
                    "capacity_summary_text": "儀式＋晚宴最多 50 人",
                    "price_summary_text": "需綁豪宅住宿與買斷型預算",
                    "backup_summary_text": "雨天多半改為豪宅室內區域與教堂備案。",
                    "decision_notes": "最私密、最有代表性，但成本與操作門檻也最高。",
                },
            ]
            write_json_file(paths["venues"] / "example.json", venue)

            output_dir = root / "site"
            write_static_site(root, output_dir)
            index_html = (output_dir / "index.html").read_text(encoding="utf-8")
            detail_html = (
                output_dir / "venues" / "example-cliffside-resort.html"
            ).read_text(encoding="utf-8")

            self.assertIn("婚禮空間比較", detail_html)
            self.assertIn("寶格麗教堂", detail_html)
            self.assertIn("總裁豪宅私人水台", detail_html)
            self.assertIn("共享空間", detail_html)
            self.assertIn("私密包場", detail_html)
            self.assertIn("買斷型活動", detail_html)
            self.assertNotIn("婚禮空間比較", index_html)

    def test_write_static_site_emits_mobile_and_gallery_ui_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_workspace_with_similar_venue(root)
            output_dir = root / "site"

            write_static_site(root, output_dir)

            index_html = (output_dir / "index.html").read_text(encoding="utf-8")
            detail_html = (
                output_dir / "venues" / "example-cliffside-resort.html"
            ).read_text(encoding="utf-8")
            site_css = (output_dir / "assets" / "site.css").read_text(encoding="utf-8")
            site_js = (output_dir / "assets" / "site.js").read_text(encoding="utf-8")

            self.assertIn('class="hero-layout"', index_html)
            self.assertIn('class="hero-panel"', index_html)
            self.assertIn('class="style-card-count"', index_html)
            self.assertIn('class="style-card-media"', index_html)
            self.assertIn('class="compare-row"', index_html)
            self.assertIn('class="compare-detail-link"', index_html)
            self.assertIn('class="detail-anchor-nav"', detail_html)
            self.assertIn('href="#decision-summary"', detail_html)
            self.assertIn('id="photo-gallery"', detail_html)
            self.assertIn('class="photo-gallery-grid"', detail_html)
            self.assertIn('class="photo-gallery-summary"', detail_html)
            self.assertIn('class="gallery-preview-hint"', detail_html)
            self.assertIn('data-lightbox-target="meta"', detail_html)
            self.assertIn('data-lightbox-target="hint"', detail_html)
            self.assertIn(".hero-layout", site_css)
            self.assertIn(".hero-panel", site_css)
            self.assertIn(".style-card-count", site_css)
            self.assertIn(".style-card-media", site_css)
            self.assertIn(".compare-row", site_css)
            self.assertIn(".detail-anchor-nav", site_css)
            self.assertIn(".photo-gallery-grid", site_css)
            self.assertIn(".photo-gallery-details", site_css)
            self.assertIn(".gallery-preview-hint", site_css)
            self.assertIn("touchstart", site_js)
            self.assertIn("touchend", site_js)

    def test_write_static_site_emits_homepage_toc_and_section_tracking_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_workspace_with_similar_venue(root)
            output_dir = root / "site"

            write_static_site(root, output_dir)

            index_html = (output_dir / "index.html").read_text(encoding="utf-8")
            site_css = (output_dir / "assets" / "site.css").read_text(encoding="utf-8")
            site_js = (output_dir / "assets" / "site.js").read_text(encoding="utf-8")

            self.assertIn('class="surface page-toc"', index_html)
            self.assertIn('class="index-sidebar"', index_html)
            self.assertIn('id="tocCurrentLabel"', index_html)
            self.assertIn('data-section-link="style-chapel"', index_html)
            self.assertIn('aria-label="首頁內容目錄"', index_html)
            self.assertIn("右側類型導覽", index_html)
            self.assertIn(".page-toc", site_css)
            self.assertIn(".index-layout", site_css)
            self.assertIn(".page-toc-link.is-active", site_css)
            self.assertIn(".toc-current", site_css)
            self.assertIn("IntersectionObserver", site_js)
            self.assertIn("tocCurrentLabel", site_js)
            self.assertIn("data-section-link", site_js)

    def test_write_static_site_renders_current_status_alerts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paths = self._write_workspace(root)
            status_source = {
                "source_id": "example-operational-status",
                "venue_id": "example-cliffside-resort",
                "source_type": "official",
                "source_name": "Example Resort Status",
                "source_url": "https://example.com/cliffside/status",
                "captured_at": "2026-06-20",
                "content_date_if_known": None,
                "language": "en",
                "evidence_categories": ["restrictions"],
                "reliability_notes": "Synthetic official status notice for test coverage",
                "raw_excerpt_summary": "Temporary closure notice",
            }
            venue = venue_record()
            venue["source_ids"] = [
                "example-cliffside-official",
                "example-operational-status",
            ]
            venue["current_status"] = {
                "level": "temporarily_closed",
                "headline": "官方頁面顯示自 2026-02-01 起暫時關閉",
                "summary": "近期婚期必須先確認是否已恢復接單與開館。",
                "checked_at": "2026-06-20",
                "source_ids": ["example-operational-status"],
            }

            write_json_file(paths["sources"] / "example.json", [source_record(), status_source])
            write_json_file(paths["venues"] / "example.json", venue)

            output_dir = root / "site"
            write_static_site(root, output_dir)
            index_html = (output_dir / "index.html").read_text(encoding="utf-8")
            detail_html = (
                output_dir / "venues" / "example-cliffside-resort.html"
            ).read_text(encoding="utf-8")

            self.assertNotIn("近期營運現況", index_html)
            self.assertNotIn("看現況提醒", index_html)
            self.assertNotIn('href="#status-overview"', index_html)
            self.assertIn('href="#current-status"', detail_html)
            self.assertIn('id="current-status"', detail_html)
            self.assertIn("營運現況", detail_html)
            self.assertIn("近期婚期必須先確認是否已恢復接單與開館。", detail_html)

    def test_write_static_site_uses_local_photo_assets_when_manifest_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paths = self._write_workspace(root)
            local_asset = (
                paths["photo_assets"]
                / "example-cliffside-resort"
                / "example-photo-1.jpg"
            )
            local_asset.parent.mkdir(parents=True, exist_ok=True)
            local_asset.write_bytes(b"fake-image-data")
            write_json_file(
                paths["derived"] / "photo-assets.json",
                {
                    "generated_at": "2026-06-19",
                    "items": [
                        {
                            "photo_entry_id": "example-photo-1",
                            "venue_id": "example-cliffside-resort",
                            "source_id": "example-cliffside-official",
                            "asset_paths": [
                                str(local_asset.relative_to(root))
                            ],
                        }
                    ],
                },
            )

            output_dir = root / "site"
            write_static_site(root, output_dir)
            detail_html = (
                output_dir / "venues" / "example-cliffside-resort.html"
            ).read_text(encoding="utf-8")

            self.assertIn(
                'src="../assets/photos/example-cliffside-resort/example-photo-1.jpg"',
                detail_html,
            )
            self.assertTrue(
                (
                    output_dir
                    / "assets"
                    / "photos"
                    / "example-cliffside-resort"
                    / "example-photo-1.jpg"
                ).exists()
            )

    def test_write_static_site_prioritizes_non_official_photos_and_shows_card_cover(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paths = self._write_workspace(root)
            local_asset = (
                paths["photo_assets"]
                / "example-cliffside-resort"
                / "example-photo-1.jpg"
            )
            local_asset.parent.mkdir(parents=True, exist_ok=True)
            local_asset.write_bytes(b"fake-image-data")
            write_json_file(
                paths["derived"] / "photo-assets.json",
                {
                    "generated_at": "2026-06-19",
                    "items": [
                        {
                            "photo_entry_id": "example-photo-1",
                            "venue_id": "example-cliffside-resort",
                            "source_id": "example-cliffside-official",
                            "asset_paths": [
                                str(local_asset.relative_to(root))
                            ],
                        }
                    ],
                },
            )

            output_dir = root / "site"
            write_static_site(root, output_dir)
            index_html = (output_dir / "index.html").read_text(encoding="utf-8")
            detail_html = (
                output_dir / "venues" / "example-cliffside-resort.html"
            ).read_text(encoding="utf-8")

            self.assertIn(
                'src="assets/photos/example-cliffside-resort/example-photo-1.jpg"',
                index_html,
            )
            self.assertIn("Shows full ceremony setup and aisle width", detail_html)
            self.assertNotIn("Single room photo", detail_html)

    def test_write_static_site_removes_stale_copied_photo_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paths = self._write_workspace(root)
            local_asset = (
                paths["photo_assets"]
                / "example-cliffside-resort"
                / "example-photo-1.jpg"
            )
            local_asset.parent.mkdir(parents=True, exist_ok=True)
            local_asset.write_bytes(b"fake-image-data")
            write_json_file(
                paths["derived"] / "photo-assets.json",
                {
                    "generated_at": "2026-06-19",
                    "items": [
                        {
                            "photo_entry_id": "example-photo-1",
                            "venue_id": "example-cliffside-resort",
                            "source_id": "example-cliffside-official",
                            "asset_paths": [
                                str(local_asset.relative_to(root))
                            ],
                        }
                    ],
                },
            )

            output_dir = root / "site"
            stale_asset = (
                output_dir
                / "assets"
                / "photos"
                / "example-cliffside-resort"
                / "stale.jpg"
            )
            stale_asset.parent.mkdir(parents=True, exist_ok=True)
            stale_asset.write_bytes(b"stale-data")

            write_static_site(root, output_dir)

            self.assertFalse(stale_asset.exists())

    def test_build_site_server_serves_generated_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_workspace(root)
            output_dir = root / "site"
            write_static_site(root, output_dir)

            server = build_site_server(output_dir, host="127.0.0.1", port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                port = server.server_address[1]
                response = urlopen(f"http://127.0.0.1:{port}/")
                body = response.read().decode("utf-8")
            finally:
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()

            self.assertEqual(response.status, 200)
            self.assertIn("Example Cliffside Resort", body)

    def test_write_pages_site_writes_docs_site_and_root_redirect(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_workspace(root)

            written = write_pages_site(root)

            docs_dir = root / "docs"
            self.assertEqual(
                written,
                [
                    docs_dir / "index.html",
                    docs_dir / "assets" / "site.css",
                    docs_dir / "assets" / "site.js",
                    docs_dir / "venues" / "example-cliffside-resort.html",
                    docs_dir / ".nojekyll",
                    docs_dir / "docs" / "index.html",
                    docs_dir / "docs" / "venues" / "example-cliffside-resort.html",
                    root / "index.html",
                    root / ".nojekyll",
                ],
            )
            docs_index = (docs_dir / "index.html").read_text(encoding="utf-8")
            legacy_docs_index = (docs_dir / "docs" / "index.html").read_text(encoding="utf-8")
            legacy_venue_index = (
                docs_dir / "docs" / "venues" / "example-cliffside-resort.html"
            ).read_text(encoding="utf-8")
            root_index = (root / "index.html").read_text(encoding="utf-8")

            self.assertIn("範例懸崖度假村", docs_index)
            self.assertIn('content="0; url=../"', legacy_docs_index)
            self.assertIn('content="0; url=../../venues/example-cliffside-resort.html"', legacy_venue_index)
            self.assertIn("window.location.pathname.endsWith", root_index)
            self.assertIn('window.location.replace(`${basePath}docs/`)', root_index)
            self.assertIn('href="docs/"', root_index)
            self.assertEqual((docs_dir / ".nojekyll").read_text(encoding="utf-8"), "")
            self.assertEqual((root / ".nojekyll").read_text(encoding="utf-8"), "")


if __name__ == "__main__":
    unittest.main()
