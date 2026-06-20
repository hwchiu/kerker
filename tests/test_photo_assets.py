import os
import tempfile
import unittest
from datetime import date
from pathlib import Path

from bali_wedding_research.io import load_json_file, write_json_file
from bali_wedding_research.paths import ensure_workspace_layout, workspace_paths
from bali_wedding_research.photo_assets import (
    copy_photo_assets_for_site,
    extract_candidate_image_urls,
    write_photo_assets,
)
from tests.sample_data import photo_records, source_record, venue_record


class PhotoAssetsTest(unittest.TestCase):
    def test_extract_candidate_image_urls_prefers_real_media_hosts(self) -> None:
        html = """
        <script>
          "https://ak-d.tripcdn.com/images/a1.jpg"
          "https://pages.trip.com/trip-hotel-app/detail/common_nobg.png"
          "https:\\/\\/ak-d.tripcdn.com\\/images\\/a2.webp"
        </script>
        """

        urls = extract_candidate_image_urls(
            html,
            page_url="https://hk.trip.com/hotels/bali-hotel-detail-1716859/the-ritz-carlton-bali/",
        )

        self.assertEqual(
            urls,
            [
                "https://ak-d.tripcdn.com/images/a1.jpg",
                "https://ak-d.tripcdn.com/images/a2.webp",
            ],
        )

    def test_extract_candidate_image_urls_supports_ctrip_hosts(self) -> None:
        html = """
        <script>
          "https://dimg04.c-ctrip.com/images/a1.jpg"
          "https://webresource.c-ctrip.com/logo.png"
        </script>
        """

        urls = extract_candidate_image_urls(
            html,
            page_url="https://hotels.ctrip.com/hotels/21888559.html",
        )

        self.assertEqual(urls, ["https://dimg04.c-ctrip.com/images/a1.jpg"])

    def test_extract_candidate_image_urls_dedupes_wordpress_resized_variants(self) -> None:
        html = """
        <img src="https://balifortwo2.com/wp-content/uploads/2026/02/UWT08-300x200.jpg">
        <img src="https://balifortwo2.com/wp-content/uploads/2026/02/UWT08-768x512.jpg">
        <img src="https://balifortwo2.com/wp-content/uploads/2026/02/UWT08.jpg">
        """

        urls = extract_candidate_image_urls(
            html,
            page_url="https://balifortwo2.com/eve-at-tirtha-uluwatu-for-chapel-wedding-and-reception-at-glass-house-for-30-guests/",
        )

        self.assertEqual(urls, ["https://balifortwo2.com/wp-content/uploads/2026/02/UWT08.jpg"])

    def test_extract_candidate_image_urls_supports_neverneverland_wordpress_hosts(self) -> None:
        html = """
        <img src="https://neverneverlandinbali.com/wp-content/uploads/2021/02/ch-640x672.jpg">
        <img src="https://neverneverlandinbali.com/wp-content/uploads/2021/02/ch.jpg">
        <img src="https://neverneverlandinbali.com/wp-content/uploads/2021/02/logo.png">
        """

        urls = extract_candidate_image_urls(
            html,
            page_url="https://neverneverlandinbali.com/wedding/16720-2/",
        )

        self.assertEqual(
            urls,
            ["https://neverneverlandinbali.com/wp-content/uploads/2021/02/ch.jpg"],
        )

    def test_extract_candidate_image_urls_supports_weddingku_hosts_and_skips_banners(self) -> None:
        html = """
        <img src="https://images.weddingku.com/images/upload/partners/pp/48115-xdtf83ivu5ws.jpg">
        <img src="https://images.weddingku.com/images/banner/banner-JWF2022-480x100.gif?v=1">
        <img src="https://assets.weddingku.com/images/noimage.jpg">
        """

        urls = extract_candidate_image_urls(
            html,
            page_url="https://www.weddingku.com/wedding-vendors/hotel-ballroom/four-seasons-resort-jimbaran/realwedding",
        )

        self.assertEqual(
            urls,
            ["https://images.weddingku.com/images/upload/partners/pp/48115-xdtf83ivu5ws.jpg"],
        )

    def test_extract_candidate_image_urls_supports_weddingku_real_wedding_images(self) -> None:
        html = """
        <img src="https://images.weddingku.com/images/upload/products/images/42573-b27iam4yxs0v.jpg">
        <img src="https://images.weddingku.com/images/upload/products/images/42573-nriu48xlk2mi.jpg">
        <img src="https://www.weddingku.com/assets/i/wkicon.png">
        """

        urls = extract_candidate_image_urls(
            html,
            page_url="https://www.weddingku.com/real-weddings/ritz-carlton-bali",
        )

        self.assertEqual(
            urls,
            [
                "https://images.weddingku.com/images/upload/products/images/42573-b27iam4yxs0v.jpg",
                "https://images.weddingku.com/images/upload/products/images/42573-nriu48xlk2mi.jpg",
            ],
        )

    def test_extract_candidate_image_urls_supports_weddingku_article_images(self) -> None:
        html = """
        <img src="https://images.weddingku.com/images/upload/articles/images/uyp0sfe66mto42120221630.jpg">
        <img src="https://images.weddingku.com/images/upload/articles/images682/uyp0sfe66mto42120221630.jpg">
        <img src="https://images.weddingku.com/images/noimage-largehorizontal.jpg">
        """

        urls = extract_candidate_image_urls(
            html,
            page_url="https://www.weddingku.com/blog/5-spot-wedding-venue-eksotis-di-six-senses-uluwatu",
        )

        self.assertEqual(
            urls,
            ["https://images.weddingku.com/images/upload/articles/images/uyp0sfe66mto42120221630.jpg"],
        )

    def test_extract_candidate_image_urls_prioritizes_weddingku_fullsize_article_images(self) -> None:
        html = """
        <img src="https://images.weddingku.com/images/upload/articles/images682/sxoa6ed553r442920261338.jpg">
        <img src="https://images.weddingku.com/images/upload/articles/images/sxoa6ed553r442920261338.jpg">
        <img src="https://images.weddingku.com/images/upload/products/thumbs/136827-typ0sfe6qmso.jpg">
        """

        urls = extract_candidate_image_urls(
            html,
            page_url="https://www.weddingku.com/blog/ocean-view-wedding-di-uluwatu-bali-yang-bikin-jatuh-cinta",
        )

        self.assertEqual(
            urls,
            ["https://images.weddingku.com/images/upload/articles/images/sxoa6ed553r442920261338.jpg"],
        )

    def test_extract_candidate_image_urls_supports_balifortwo_squarespace_hosts(self) -> None:
        html = """
        <img src="https://images.squarespace-cdn.com/content/v1/55a710/example/Bali-wedding-easy-Hanging-garden-ubud-01.jpg">
        <img src="https://scontent.cdninstagram.com/t51.2885-19/s150x150/11189993_1142196395796428_325646638_a.jpg">
        <img src="http://passets-ak.pinterest.com/images/user/default_60.png">
        """

        urls = extract_candidate_image_urls(
            html,
            page_url="https://www.balifortwo.com/ubud-wedding/hanging-gardens",
        )

        self.assertEqual(
            urls,
            [
                "https://images.squarespace-cdn.com/content/v1/55a710/example/Bali-wedding-easy-Hanging-garden-ubud-01.jpg"
            ],
        )

    def test_extract_candidate_image_urls_supports_watabe_wedding_pages(self) -> None:
        html = """
        <img data-src="https://www.watabe-wedding.co.jp/resort_wedding/wedding_report/uploads/2025/05/1547083/1547083151.JPG">
        <img data-src="https://www.watabe-wedding.co.jp/resort_wedding/wedding_report/uploads/2025/05/1530033/1530033085.jpg">
        <img src="https://dev.visualwebsiteoptimizer.com/ee.gif?a=">
        """

        urls = extract_candidate_image_urls(
            html,
            page_url="https://www.watabe-wedding.co.jp/bali/chapel_majestic/",
        )

        self.assertEqual(
            urls,
            [
                "https://www.watabe-wedding.co.jp/resort_wedding/wedding_report/uploads/2025/05/1547083/1547083151.JPG",
                "https://www.watabe-wedding.co.jp/resort_wedding/wedding_report/uploads/2025/05/1530033/1530033085.jpg",
            ],
        )

    def test_extract_candidate_image_urls_supports_the_wedding_notebook_r2_assets(self) -> None:
        html = """
        <link rel="preload" href="https://pub-example.r2.dev/inspire/story/1775709975378-cover/crop-4x5-mobile-cover.webp" as="image">
        <img src="https://pub-example.r2.dev/inspire/story/1775709983993-RW-ArlaSharmaineQuanBali44-1024x683/high.webp">
        <img src="https://theweddingnotebook.com/twn-logo.png">
        """

        urls = extract_candidate_image_urls(
            html,
            page_url="https://theweddingnotebook.com/inspire/real-weddings/story/",
        )

        self.assertEqual(
            urls,
            [
                "https://pub-example.r2.dev/inspire/story/1775709983993-RW-ArlaSharmaineQuanBali44-1024x683/high.webp",
                "https://pub-example.r2.dev/inspire/story/1775709975378-cover/crop-4x5-mobile-cover.webp",
            ],
        )

    def test_extract_candidate_image_urls_supports_kvision_assets(self) -> None:
        html = """
        <img src="https://kvisiontw.isimg.cc/uploads/2024/08/0821123935g2PaNqp7-150x150.jpg">
        <img src="https://kvisiontw.isimg.cc/uploads/2024/08/0821123935g2PaNqp7.jpg">
        <img src="https://kvisiontw.isimg.cc/uploads/2024/01/logo.png">
        """

        urls = extract_candidate_image_urls(
            html,
            page_url="https://kvision.tw/gallery/baliwedding_the_edge/",
        )

        self.assertEqual(
            urls,
            ["https://kvisiontw.isimg.cc/uploads/2024/08/0821123935g2PaNqp7.jpg"],
        )

    def test_extract_candidate_image_urls_supports_ameblo_user_images(self) -> None:
        html = """
        <img src="https://stat.ameba.jp/user_images/20231225/01/kenjimovement/90/26/j/o1000075015381138552.jpg?caw=800">
        <img src="https://stat.ameba.jp/user_images/20231225/01/kenjimovement/90/26/j/o1000075015381138552.jpg">
        <img src="https://stat100.ameba.jp/ameblo/pc/img/amebloJp/abema_logo.png">
        """

        urls = extract_candidate_image_urls(
            html,
            page_url="https://ameblo.jp/kenjimovement/entry-12834033508.html",
        )

        self.assertEqual(
            urls,
            ["https://stat.ameba.jp/user_images/20231225/01/kenjimovement/90/26/j/o1000075015381138552.jpg"],
        )

    def test_extract_candidate_image_urls_supports_weddings_com_tw_wordpress(self) -> None:
        html = """
        <img src="https://www.weddings.com.tw/wp-content/uploads/2020/05/JohnnySylvia_wedding_fin-149-拷貝-300x200.jpg">
        <img src="https://www.weddings.com.tw/wp-content/uploads/2020/05/JohnnySylvia_wedding_fin-149-拷貝.jpg">
        <img src="https://www.weddings.com.tw/wp-content/uploads/2020/01/weddings-logo.png">
        """

        urls = extract_candidate_image_urls(
            html,
            page_url="https://www.weddings.com.tw/bali-destination-wedding-guide/",
        )

        self.assertEqual(
            urls,
            ["https://www.weddings.com.tw/wp-content/uploads/2020/05/JohnnySylvia_wedding_fin-149-拷貝.jpg"],
        )

    def test_extract_candidate_image_urls_dedupes_underscore_resized_variants(self) -> None:
        html = """
        <img src="https://sweetday.com.tw/wp-content/uploads/2021/02/sample_140x87.jpg">
        <img src="https://sweetday.com.tw/wp-content/uploads/2021/02/sample_140x87-300x203.jpg">
        <img src="https://sweetday.com.tw/wp-content/uploads/2021/02/sample.jpg">
        """

        urls = extract_candidate_image_urls(
            html,
            page_url="https://sweetday.com.tw/wedding/example/",
        )

        self.assertEqual(
            urls,
            ["https://sweetday.com.tw/wp-content/uploads/2021/02/sample.jpg"],
        )

    def test_extract_candidate_image_urls_keeps_large_dimension_suffix_when_it_is_the_original_name(self) -> None:
        html = """
        <img src="https://sweetday.com.tw/wp-content/uploads/2021/02/Ritz_Bali_00048_galleries_1280x720.jpg">
        """

        urls = extract_candidate_image_urls(
            html,
            page_url="https://sweetday.com.tw/wedding/example/",
        )

        self.assertEqual(
            urls,
            ["https://sweetday.com.tw/wp-content/uploads/2021/02/Ritz_Bali_00048_galleries_1280x720.jpg"],
        )

    def test_extract_candidate_image_urls_prefers_original_sweetday_assets_over_smushcdn(self) -> None:
        html = """
        <img src="https://b4129436.smushcdn.com/4129436/wp-content/uploads/2023/07/bali-1.jpg?size=240x132&lossy=2&strip=1&webp=1">
        <img src="https://b4129436.smushcdn.com/4129436/wp-content/uploads/2023/07/bali-1-1024x563.jpg?lossy=2&strip=1&webp=1">
        <img src="https://sweetday.com.tw/wp-content/uploads/2023/07/bali-1.jpg">
        <img src="https://sweetday.com.tw/wp-content/uploads/2023/07/sweetday.png">
        <img src="https://b4129436.smushcdn.com/4129436/wp-content/uploads/2025/04/sweetday-logo.png?lossy=2&strip=1&webp=1">
        """

        urls = extract_candidate_image_urls(
            html,
            page_url="https://sweetday.com.tw/%E5%B7%B4%E9%87%8C%E5%B3%B6%E5%A9%9A%E7%A6%AE%E5%B3%87%E9%87%8C%E5%B3%B6%E6%95%99%E5%A0%82/",
        )

        self.assertEqual(
            urls,
            ["https://sweetday.com.tw/wp-content/uploads/2023/07/bali-1.jpg"],
        )

    def test_extract_candidate_image_urls_prefers_larger_overseaswedding_cdn_variants(self) -> None:
        html = """
        <img src="https://i0.wp.com/overseaswedding.com.tw/wp-content/uploads/sites/4/2025/02/CHAPEL-1.jpg?fit=100%2C100&ssl=1">
        <img src="https://i0.wp.com/overseaswedding.com.tw/wp-content/uploads/sites/4/2025/02/CHAPEL-1.jpg?fit=1080%2C720&ssl=1">
        <img src="https://overseaswedding.com.tw/wp-content/uploads/sites/4/2017/12/LOGO-OW.jpg">
        <img src="https://overseaswedding.com.tw/wp-content/themes/Divi/includes/builder/styles/images/preloader.gif">
        """

        urls = extract_candidate_image_urls(
            html,
            page_url="https://overseaswedding.com.tw/bali/",
        )

        self.assertEqual(
            urls,
            [
                "https://overseaswedding.com.tw/wp-content/uploads/sites/4/2025/02/CHAPEL-1.jpg"
            ],
        )

    def test_extract_candidate_image_urls_supports_gowedding_cdn_images(self) -> None:
        html = """
        <img src="https://img.gowedding.tw/wp-content/uploads/2017/12/001-2.jpg">
        <img src="https://img.gowedding.tw/wp-content/uploads/2020/12/d679cfb005ce9a732ba09bd005bb7a1e-32x32.png">
        <img src="https://gowedding.tw/wp-content/uploads/2020/07/a3b0e5649eccd06f37e4f5cbddc15fab.png">
        """

        urls = extract_candidate_image_urls(
            html,
            page_url="https://gowedding.tw/%E5%B3%87%E9%87%8C%E5%B3%B6%E6%B5%B7%E5%A4%96%E5%A9%9A%E7%A6%AE6%E9%96%93%E7%86%B1%E9%96%80%E6%95%99%E5%A0%82%E6%8E%A8%E8%96%A6/",
        )

        self.assertEqual(
            urls,
            ["https://img.gowedding.tw/wp-content/uploads/2017/12/001-2.jpg"],
        )

    def test_extract_candidate_image_urls_resolves_relative_wordpress_lazy_urls(self) -> None:
        html = """
        <img data-src="/wp-content/uploads/2026/01/bvlgari-villa-300x200.jpg">
        <img data-lazy-src="/wp-content/uploads/2026/01/bvlgari-villa.jpg">
        """

        urls = extract_candidate_image_urls(
            html,
            page_url="https://balivibesweddings.com/bvlgari-resort-bali/",
        )

        self.assertEqual(
            urls,
            ["https://balivibesweddings.com/wp-content/uploads/2026/01/bvlgari-villa.jpg"],
        )

    def test_extract_candidate_image_urls_prefers_largest_squarespace_srcset_candidate(self) -> None:
        html = """
        <img
          srcset="
            https://images.squarespace-cdn.com/content/v1/55a710/example/Bali-wedding-easy-Hanging-garden-ubud-01.jpg?format=500w 500w,
            https://images.squarespace-cdn.com/content/v1/55a710/example/Bali-wedding-easy-Hanging-garden-ubud-01.jpg?format=1500w 1500w
          "
        >
        """

        urls = extract_candidate_image_urls(
            html,
            page_url="https://www.balifortwo.com/ubud-wedding/hanging-gardens",
        )

        self.assertEqual(
            urls,
            [
                "https://images.squarespace-cdn.com/content/v1/55a710/example/Bali-wedding-easy-Hanging-garden-ubud-01.jpg?format=1500w"
            ],
        )

    def test_extract_candidate_image_urls_reads_image_urls_from_json_ld(self) -> None:
        html = """
        <script type="application/ld+json">
          {"image":["\\/wp-content\\/uploads\\/2026\\/01\\/bali-villa-300x200.jpg","\\/wp-content\\/uploads\\/2026\\/01\\/bali-villa.jpg"]}
        </script>
        """

        urls = extract_candidate_image_urls(
            html,
            page_url="https://balivibesweddings.com/bvlgari-resort-bali/",
        )

        self.assertEqual(
            urls,
            ["https://balivibesweddings.com/wp-content/uploads/2026/01/bali-villa.jpg"],
        )

    def test_extract_candidate_image_urls_reads_relative_background_images(self) -> None:
        html = """
        <div class="gallery-item" style="background-image:url('/UploadFile/WVenue_Album/SukaWedding-Album-20181009114702_82321.png')"></div>
        <div class="gallery-item" style="background-image:url('/UploadFile/WVenue_Album/SukaWedding-Album-20181009114717_18714.png')"></div>
        """

        urls = extract_candidate_image_urls(
            html,
            page_url="https://www.sukawedding.com/Wedding_Venue_Detail.asp?ViD=75786C6EA39F36913801B160D0B95D1A",
        )

        self.assertEqual(
            urls,
            [
                "https://www.sukawedding.com/UploadFile/WVenue_Album/SukaWedding-Album-20181009114702_82321.png",
                "https://www.sukawedding.com/UploadFile/WVenue_Album/SukaWedding-Album-20181009114717_18714.png",
            ],
        )

    def test_write_photo_assets_downloads_non_official_sources_and_writes_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            ensure_workspace_layout(root)
            paths = workspace_paths(root)

            venue = venue_record()
            official_source = source_record()
            platform_source = {
                **source_record(),
                "source_id": "example-tripcom",
                "source_type": "platform_agency",
                "source_name": "Example Trip.com",
                "source_url": "https://hk.trip.com/hotels/example",
                "language": "zh",
            }
            platform_photo = {
                **photo_records()[0],
                "source_id": "example-tripcom",
                "page_url": "https://hk.trip.com/hotels/example",
                "image_url_or_gallery_url": "https://hk.trip.com/hotels/example",
            }

            venue["source_ids"] = [official_source["source_id"], platform_source["source_id"]]

            write_json_file(paths["venues"] / "example.json", venue)
            write_json_file(
                paths["sources"] / "example.json",
                [official_source, platform_source],
            )
            write_json_file(
                paths["photos"] / "example.json",
                [photo_records()[1], platform_photo],
            )

            def fetcher(url: str) -> bytes:
                if url == "https://hk.trip.com/hotels/example":
                    return (
                        b'"https://ak-d.tripcdn.com/images/example-1.jpg" '
                        b'"https://pages.trip.com/trip-hotel-app/detail/common_nobg.png"'
                    )
                if url == "https://ak-d.tripcdn.com/images/example-1.jpg":
                    return b"fake-image-data"
                raise AssertionError(url)

            manifest_path = write_photo_assets(root, max_images_per_photo=4, fetcher=fetcher)
            manifest = load_json_file(manifest_path)

            self.assertEqual(manifest["generated_at"], date.today().isoformat())
            self.assertEqual(len(manifest["items"]), 1)
            self.assertEqual(manifest["items"][0]["photo_entry_id"], platform_photo["photo_entry_id"])
            asset_path = root / manifest["items"][0]["asset_paths"][0]
            self.assertTrue(asset_path.exists())
            self.assertEqual(asset_path.read_bytes(), b"fake-image-data")

    def test_write_photo_assets_skips_official_promotional_photo_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            ensure_workspace_layout(root)
            paths = workspace_paths(root)

            venue = venue_record()
            venue["source_ids"] = [
                "example-bridestory-real",
                "example-tripcom-official-promo",
            ]
            real_source = {
                **source_record(),
                "source_id": "example-bridestory-real",
                "source_type": "platform_agency",
                "source_name": "Example Bridestory Real Wedding",
                "source_url": "https://www.bridestory.com/example/projects/test-wedding",
            }
            promo_source = {
                **source_record(),
                "source_id": "example-tripcom-official-promo",
                "source_type": "platform_agency",
                "source_name": "Example Trip.com Listing",
                "source_url": "https://hk.trip.com/hotels/example",
            }
            real_photo = {
                **photo_records()[0],
                "photo_entry_id": "example-bridestory-real-photo",
                "source_id": "example-bridestory-real",
                "page_url": "https://www.bridestory.com/example/projects/test-wedding",
                "image_url_or_gallery_url": "https://www.bridestory.com/example/projects/test-wedding",
                "authenticity": "real_wedding",
            }
            promo_photo = {
                **photo_records()[1],
                "photo_entry_id": "example-tripcom-official-promo-photo",
                "source_id": "example-tripcom-official-promo",
                "page_url": "https://hk.trip.com/hotels/example",
                "image_url_or_gallery_url": "https://hk.trip.com/hotels/example",
                "image_type": "platform_listing_gallery",
                "authenticity": "official_promotional",
            }

            write_json_file(paths["venues"] / "example.json", venue)
            write_json_file(paths["sources"] / "example.json", [real_source, promo_source])
            write_json_file(paths["photos"] / "example.json", [real_photo, promo_photo])

            def fetcher(url: str) -> bytes:
                if url == "https://www.bridestory.com/example/projects/test-wedding":
                    return (
                        b'<img src="https://images.bridestory.com/image/upload/assets/test-real-image.jpg">'
                    )
                if url == "https://images.bridestory.com/image/upload/assets/test-real-image.jpg":
                    return b"real-image-data"
                if url == "https://hk.trip.com/hotels/example":
                    return b'"https://ak-d.tripcdn.com/images/official-promo.jpg"'
                if url == "https://ak-d.tripcdn.com/images/official-promo.jpg":
                    return b"promo-image-data"
                raise AssertionError(url)

            manifest_path = write_photo_assets(root, max_images_per_photo=4, fetcher=fetcher)
            manifest = load_json_file(manifest_path)

            self.assertEqual(
                [item["photo_entry_id"] for item in manifest["items"]],
                ["example-bridestory-real-photo"],
            )
            asset_path = root / manifest["items"][0]["asset_paths"][0]
            self.assertTrue(asset_path.exists())
            self.assertEqual(asset_path.read_bytes(), b"real-image-data")

    def test_copy_photo_assets_for_site_supports_relative_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = Path.cwd()
            os.chdir(tmpdir)
            try:
                root = Path("workspace")
                ensure_workspace_layout(root)
                paths = workspace_paths(root)
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
                                "source_id": "example-source",
                                "asset_paths": [
                                    str(local_asset.relative_to(root.resolve()))
                                ],
                            }
                        ],
                    },
                )

                output_dir = root / "site"
                mapping = copy_photo_assets_for_site(root, output_dir)

                self.assertEqual(
                    mapping,
                    {
                        "example-photo-1": [
                            "../assets/photos/example-cliffside-resort/example-photo-1.jpg"
                        ]
                    },
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
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()
