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
            self.assertIn("依婚禮風格開始挑", index_html)
            self.assertIn('href="#style-chapel"', index_html)
            self.assertIn("教堂", index_html)
            self.assertIn("公開價格已統一換算為台幣", index_html)
            self.assertIn("公開方案約 NT$269,068 起", index_html)
            self.assertNotIn("Public ceremony package starts at USD 8,500", index_html)
            self.assertIn("快速初篩路線", index_html)
            self.assertIn("全部場地比較", index_html)
            self.assertIn("sortSelect", index_html)
            self.assertIn("Example Cliffside Weddings", detail_html)
            self.assertIn("https://example.com/cliffside/gallery/1", detail_html)
            self.assertIn("Confirm corkage fees for external alcohol", detail_html)
            self.assertIn("決策適配", detail_html)
            self.assertIn("相近替代場地", detail_html)
            self.assertIn("Example Garden Resort", detail_html)
            self.assertIn('class="gallery-preview"', detail_html)
            self.assertIn('data-lightbox-image="https://example.com/images/1.jpg"', detail_html)
            self.assertIn('id="photoLightbox"', detail_html)
            self.assertIn('src="https://example.com/images/1.jpg"', detail_html)
            self.assertIn("NT$269,068", detail_html)
            self.assertIn("NT$461,500", detail_html)
            self.assertIn("約原幣 USD 8,500", detail_html)
            self.assertIn("約原幣 IDR 260,000,000", detail_html)
            self.assertNotIn("Public ceremony package starts at USD 8,500", detail_html)

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
