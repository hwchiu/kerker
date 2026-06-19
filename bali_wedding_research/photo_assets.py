from __future__ import annotations

from datetime import date
from pathlib import Path
import re
from shutil import copy2, rmtree
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .io import load_json_file, load_workspace_records, write_json_file
from .paths import workspace_paths

FetchBytes = Callable[[str], bytes]

IMAGE_URL_PATTERN = re.compile(
    r'https?:\\?/\\?/[^"\'\s<>]+?\.(?:jpg|jpeg|png|webp|gif)(?:\?[^"\'\s<>]*)?',
    re.IGNORECASE,
)

SKIP_IMAGE_KEYWORDS = {
    "logo",
    "icon",
    "sprite",
    "avatar",
    "banner",
    "favicon",
    "mask",
    "noimage",
    "placeholder",
    "nobg",
    "assist.png",
    "star5",
    "default_60",
    "wkicon",
    "wesurvey",
    "logoapp",
    "popup",
    "dark/common",
    "ee.gif",
    "preloader",
    "sweetday.png",
    "visualwebsiteoptimizer",
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
SUPPORTED_PAGE_HOSTS = {
    "hk.trip.com",
    "hotels.ctrip.com",
    "www.weddingku.com",
    "new.weddingku.com",
    "www.watabe-wedding.co.jp",
    "watabe-wedding.co.jp",
    "www.weddings.com.tw",
    "weddings.com.tw",
    "sweetday.com.tw",
    "overseaswedding.com.tw",
    "gowedding.tw",
}


def _default_fetcher(url: str) -> bytes:
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            )
        },
    )
    with urlopen(request, timeout=12) as response:
        return response.read()


def _is_supported_page_host(host: str) -> bool:
    return (
        host in SUPPORTED_PAGE_HOSTS
        or host.endswith(".weddingku.com")
        or host.endswith("balifortwo2.com")
        or host.endswith("balifortwo.com")
        or host.endswith("neverneverlandinbali.com")
        or host.endswith("florasay.com")
        or host.endswith("weddings.com.tw")
        or host.endswith("sweetday.com.tw")
        or host.endswith("overseaswedding.com.tw")
        or host.endswith("gowedding.tw")
    )


def _is_supported_image_host(page_host: str, image_host: str, image_path: str) -> bool:
    if "ctrip.com" in page_host:
        return image_host.endswith(".c-ctrip.com") and "/images/" in image_path
    if "trip.com" in page_host:
        return image_host.endswith("tripcdn.com") and "/images/" in image_path
    if "tripadvisor" in page_host:
        return "tripadvisor" in image_host and (
            "/media/photo" in image_path or "photo-o" in image_path
        )
    if "balifortwo2.com" in page_host:
        return image_host.endswith("balifortwo2.com") and "/wp-content/uploads/" in image_path
    if "balifortwo.com" in page_host:
        return image_host.endswith("squarespace-cdn.com") and "/content/" in image_path
    if "neverneverlandinbali.com" in page_host:
        return image_host.endswith("neverneverlandinbali.com") and "/wp-content/uploads/" in image_path
    if "florasay.com" in page_host:
        return image_host.endswith("florasay.com") and "/wp-content/uploads/" in image_path
    if "weddings.com.tw" in page_host:
        return image_host.endswith("weddings.com.tw") and "/wp-content/uploads/" in image_path
    if "sweetday.com.tw" in page_host:
        return (
            (
                image_host.endswith("sweetday.com.tw")
                or image_host.endswith("smushcdn.com")
            )
            and "/wp-content/uploads/" in image_path
            and Path(image_path).suffix.lower() in {".jpg", ".jpeg", ".webp"}
        )
    if "overseaswedding.com.tw" in page_host:
        return (
            (
                image_host.endswith("overseaswedding.com.tw")
                and "/wp-content/uploads/sites/4/" in image_path
            )
            or (
                image_host.endswith(".wp.com")
                and "/overseaswedding.com.tw/wp-content/uploads/sites/4/" in image_path
            )
        )
    if "gowedding.tw" in page_host:
        return (
            image_host == "img.gowedding.tw"
            and "/wp-content/uploads/" in image_path
            and Path(image_path).suffix.lower() in {".jpg", ".jpeg", ".webp"}
        )
    if "weddingku.com" in page_host:
        return image_host.endswith("images.weddingku.com") and (
            "/images/upload/partners/" in image_path
            or "/images/upload/products/" in image_path
        )
    if "watabe-wedding.co.jp" in page_host:
        return image_host.endswith("watabe-wedding.co.jp") and (
            "/resort_wedding/wedding_report/uploads/" in image_path
        )
    return True


def _normalize_wordpress_upload_path(path: str) -> str:
    suffix = Path(path).suffix
    stem = Path(path).stem
    normalized_stem = stem
    while True:
        match = re.search(r"(?P<separator>[-_])(?P<width>\d+)x(?P<height>\d+)$", normalized_stem)
        if match is None:
            break
        separator = match.group("separator")
        width = int(match.group("width"))
        height = int(match.group("height"))
        if separator == "_" and max(width, height) > 400:
            break
        normalized_stem = normalized_stem[: match.start()]
    return str(Path(path).with_name(f"{normalized_stem}{suffix}"))


def _normalize_image_url(page_host: str, url: str) -> str:
    parsed = urlparse(url)
    scheme = parsed.scheme or "https"
    host = parsed.netloc.lower()
    path = parsed.path
    lower_path = path.lower()

    if host.endswith(".wp.com"):
        stripped = path.lstrip("/")
        site_host, _, remainder = stripped.partition("/")
        if "." in site_host and remainder.startswith("wp-content/uploads/"):
            host = site_host.lower()
            path = f"/{remainder}"
            lower_path = path.lower()
    elif host.endswith("smushcdn.com") and "/wp-content/uploads/" in lower_path:
        upload_index = lower_path.find("/wp-content/uploads/")
        host = page_host
        path = path[upload_index:]
        lower_path = path.lower()

    if "/wp-content/uploads/" in lower_path:
        path = _normalize_wordpress_upload_path(path)
        return parsed._replace(
            scheme=scheme,
            netloc=host,
            path=path,
            query="",
            fragment="",
        ).geturl()

    return parsed._replace(
        scheme=scheme,
        netloc=host,
        path=path,
        fragment="",
    ).geturl()


def _canonical_image_key(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path
    return f"{parsed.netloc.lower()}{path}"


def extract_candidate_image_urls(html: str, *, page_url: str) -> list[str]:
    page_host = urlparse(page_url).netloc.lower()
    matches = IMAGE_URL_PATTERN.findall(html)
    urls: list[str] = []
    seen: set[str] = set()
    for match in matches:
        url = match.replace("\\/", "/").replace("&amp;", "&")
        parsed = urlparse(url)
        image_host = parsed.netloc.lower()
        image_path = parsed.path.lower()
        if Path(image_path).suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        if any(keyword in url.lower() for keyword in SKIP_IMAGE_KEYWORDS):
            continue
        if not _is_supported_image_host(page_host, image_host, image_path):
            continue
        url = _normalize_image_url(page_host, url)
        if any(keyword in url.lower() for keyword in SKIP_IMAGE_KEYWORDS):
            continue
        dedupe_key = _canonical_image_key(url)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        urls.append(url)
    return urls


def _safe_fetch(url: str, fetcher: FetchBytes) -> bytes | None:
    try:
        return fetcher(url)
    except (HTTPError, URLError, TimeoutError, ValueError):
        return None


def write_photo_assets(
    root: Path,
    *,
    max_images_per_photo: int = 6,
    fetcher: FetchBytes | None = None,
) -> Path:
    if fetcher is None:
        fetcher = _default_fetcher
    paths = workspace_paths(root)
    if paths["photo_assets"].exists():
        rmtree(paths["photo_assets"])
    paths["photo_assets"].mkdir(parents=True, exist_ok=True)
    _, sources, photos = load_workspace_records(root)
    sources_by_id = {source["source_id"]: source for source in sources}
    page_candidates: dict[str, list[str]] = {}
    manifest_items: list[dict[str, object]] = []

    for photo in photos:
        source = sources_by_id[photo["source_id"]]
        if source["source_type"] == "official":
            continue
        if photo["image_type"] in {"official_hotel_gallery", "official_wedding_gallery"}:
            continue
        page_url = photo["page_url"]
        if not _is_supported_page_host(urlparse(page_url).netloc.lower()):
            continue
        if page_url not in page_candidates:
            page_bytes = _safe_fetch(page_url, fetcher)
            if page_bytes is None:
                page_candidates[page_url] = []
            else:
                page_candidates[page_url] = extract_candidate_image_urls(
                    page_bytes.decode("utf-8", errors="ignore"),
                    page_url=page_url,
                )
        candidate_urls = page_candidates[page_url][: max(0, max_images_per_photo)]
        asset_paths: list[str] = []
        for index, candidate_url in enumerate(candidate_urls, start=1):
            image_bytes = _safe_fetch(candidate_url, fetcher)
            if not image_bytes:
                continue
            extension = Path(urlparse(candidate_url).path).suffix.lower() or ".jpg"
            relative_path = (
                Path("data")
                / "photo-assets"
                / photo["venue_id"]
                / f"{photo['photo_entry_id']}-{index:02d}{extension}"
            )
            destination = root / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(image_bytes)
            asset_paths.append(relative_path.as_posix())
        if asset_paths:
            manifest_items.append(
                {
                    "photo_entry_id": photo["photo_entry_id"],
                    "venue_id": photo["venue_id"],
                    "source_id": photo["source_id"],
                    "asset_paths": asset_paths,
                }
            )

    manifest_path = paths["derived"] / "photo-assets.json"
    write_json_file(
        manifest_path,
        {
            "generated_at": date.today().isoformat(),
            "items": manifest_items,
        },
    )
    return manifest_path


def copy_photo_assets_for_site(root: Path, output_dir: Path) -> dict[str, list[str]]:
    root = root.resolve()
    manifest_path = workspace_paths(root)["derived"] / "photo-assets.json"
    if not manifest_path.exists():
        return {}
    payload = load_json_file(manifest_path)
    if not isinstance(payload, dict):
        return {}
    items = payload.get("items", [])
    if not isinstance(items, list):
        return {}

    photo_assets_root = workspace_paths(root)["photo_assets"]
    site_assets_root = output_dir / "assets" / "photos"
    if site_assets_root.exists():
        rmtree(site_assets_root)
    mapping: dict[str, list[str]] = {}

    for item in items:
        if not isinstance(item, dict):
            continue
        photo_entry_id = item.get("photo_entry_id")
        asset_paths = item.get("asset_paths")
        if not isinstance(photo_entry_id, str) or not isinstance(asset_paths, list):
            continue
        site_urls: list[str] = []
        for asset_path in asset_paths:
            if not isinstance(asset_path, str):
                continue
            source_path = (root / asset_path).resolve()
            if not source_path.exists():
                continue
            try:
                relative_inside_assets = source_path.relative_to(photo_assets_root)
            except ValueError:
                continue
            target_path = site_assets_root / relative_inside_assets
            target_path.parent.mkdir(parents=True, exist_ok=True)
            copy2(source_path, target_path)
            site_urls.append(f"../assets/photos/{relative_inside_assets.as_posix()}")
        if site_urls:
            mapping[photo_entry_id] = site_urls
    return mapping
