from __future__ import annotations

from datetime import date
from hashlib import md5
from html import unescape
from pathlib import Path
import re
from shutil import copy2, rmtree
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urljoin, urlparse
from urllib.request import Request, urlopen

from .io import load_json_file, load_workspace_records, write_json_file
from .paths import workspace_paths

FetchBytes = Callable[[str], bytes]

IMAGE_URL_PATTERN = re.compile(
    r'https?:\\?/\\?/[^"\'\s<>]+?\.(?:jpg|jpeg|png|webp|gif)(?:\?[^"\'\s<>]*)?',
    re.IGNORECASE,
)
GENERIC_IMAGE_VALUE_PATTERN = re.compile(
    r'["\'](?P<url>(?:(?:https?:)?//|/|\.\./|\./)[^"\']+?\.(?:jpg|jpeg|png|webp|gif)(?:\?[^"\']*)?)["\']',
    re.IGNORECASE,
)
ATTR_URL_PATTERN = re.compile(
    r"""(?:src|data-src|data-lazy-src|data-original|data-background|poster)\s*=\s*["'](?P<url>[^"']+)["']""",
    re.IGNORECASE,
)
SRCSET_PATTERN = re.compile(
    r"""(?:srcset|data-srcset)\s*=\s*["'](?P<value>[^"']+)["']""",
    re.IGNORECASE,
)
STYLE_URL_PATTERN = re.compile(
    r"""background(?:-image)?\s*:\s*url\((?P<url>[^)]+)\)""",
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
    "www.bridestory.com",
    "bridestory.com",
    "www.weddingku.com",
    "new.weddingku.com",
    "www.watabe-wedding.co.jp",
    "watabe-wedding.co.jp",
    "www.weddings.com.tw",
    "weddings.com.tw",
    "sweetday.com.tw",
    "overseaswedding.com.tw",
    "gowedding.tw",
    "balivibesweddings.com",
    "www.sukawedding.com",
    "sukawedding.com",
    "www.tripadvisor.com.tw",
    "tripadvisor.com.tw",
    "www.tripadvisor.cn",
    "tripadvisor.cn",
    "www.lichenglove.com",
    "lichenglove.com",
    "m.hmdays.com",
    "www.happybaliwedding.com",
    "happybaliwedding.com",
    "www.bless-bali.com",
    "bless-bali.com",
    "www.gusmank.com",
    "gusmank.com",
    "www.northwest-travel.com",
    "northwest-travel.com",
    "www.whiterosesplanner.com",
    "whiterosesplanner.com",
    "www.bernadetakupiec.co.uk",
    "bernadetakupiec.co.uk",
    "www.cinemotionphoto.com",
    "cinemotionphoto.com",
    "www.dstudios.in",
    "dstudios.in",
    "www.theweddingnotebook.com",
    "theweddingnotebook.com",
    "www.kvision.tw",
    "kvision.tw",
    "ameblo.jp",
    "www.ameblo.jp",
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
        or host.endswith(".bridestory.com")
        or host.endswith("balifortwo2.com")
        or host.endswith("balifortwo.com")
        or host.endswith("neverneverlandinbali.com")
        or host.endswith("florasay.com")
        or host.endswith("balivibesweddings.com")
        or host.endswith("weddings.com.tw")
        or host.endswith("sweetday.com.tw")
        or host.endswith("overseaswedding.com.tw")
        or host.endswith("gowedding.tw")
        or host.endswith("tripadvisor.com.tw")
        or host.endswith("tripadvisor.cn")
        or host.endswith("sukawedding.com")
        or host.endswith("lichenglove.com")
        or host.endswith("hmdays.com")
        or host.endswith("happybaliwedding.com")
        or host.endswith("bless-bali.com")
        or host.endswith("gusmank.com")
        or host.endswith("northwest-travel.com")
        or host.endswith("whiterosesplanner.com")
        or host.endswith("bernadetakupiec.co.uk")
        or host.endswith("cinemotionphoto.com")
        or host.endswith("dstudios.in")
        or host.endswith("theweddingnotebook.com")
        or host.endswith("kvision.tw")
        or host.endswith("ameblo.jp")
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
    if "balivibesweddings.com" in page_host:
        return image_host.endswith("balivibesweddings.com") and "/wp-content/uploads/" in image_path
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
    if "sukawedding.com" in page_host:
        return image_host.endswith("sukawedding.com") and "/uploadfile/wvenue_album/" in image_path
    if "bridestory.com" in page_host:
        return (
            image_host.endswith("bridestory.com")
            and (
                "/image/upload/" in image_path
                or "/images/" in image_path
            )
        )
    if "weddingku.com" in page_host:
        return image_host.endswith("images.weddingku.com") and (
            "/images/upload/partners/pp/" in image_path
            or "/images/upload/partners/images" in image_path
            or "/images/upload/products/images/" in image_path
            or "/images/upload/products/images800/" in image_path
            or "/images/upload/articles/images/" in image_path
            or "/images/upload/articles/images682/" in image_path
        )
    if "theweddingnotebook.com" in page_host:
        return image_host.endswith(".r2.dev") and "/inspire/" in image_path
    if "kvision.tw" in page_host:
        return image_host.endswith("kvisiontw.isimg.cc") and "/uploads/" in image_path
    if "ameblo.jp" in page_host:
        return image_host.endswith("ameba.jp") and "/user_images/" in image_path
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
    url = _unwrap_proxy_url(url)
    parsed = urlparse(url)
    scheme = parsed.scheme or "https"
    host = parsed.netloc.lower()
    path = parsed.path
    lower_path = path.lower()

    if host.endswith("images.weddingku.com") and "/images/upload/articles/images682/" in lower_path:
        path = re.sub(
            r"/images/upload/articles/images682/",
            "/images/upload/articles/images/",
            path,
            flags=re.IGNORECASE,
        )
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
    elif host.endswith("isimg.cc") and "/uploads/" in lower_path:
        path = _normalize_wordpress_upload_path(path)
        return parsed._replace(
            scheme=scheme,
            netloc=host,
            path=path,
            query="",
            fragment="",
        ).geturl()
    elif host.endswith("ameba.jp") and "/user_images/" in lower_path:
        return parsed._replace(
            scheme=scheme,
            netloc=host,
            path=path,
            query="",
            fragment="",
        ).geturl()

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


def _preprocess_html(html: str) -> str:
    return (
        unescape(html)
        .replace("\\/", "/")
        .replace("\\u002F", "/")
        .replace("\\u002f", "/")
        .replace("https://https://", "https://")
    )


def _parse_srcset_candidates(value: str) -> list[str]:
    candidates: list[tuple[int, str]] = []
    for raw_part in value.split(","):
        part = raw_part.strip()
        if not part:
            continue
        pieces = part.split()
        if not pieces:
            continue
        url = pieces[0]
        descriptor = pieces[1] if len(pieces) > 1 else ""
        size = 0
        match = re.search(r"(\d+)(?:w|x)$", descriptor)
        if match is not None:
            size = int(match.group(1))
        candidates.append((size, url))
    candidates.sort(key=lambda item: item[0], reverse=True)
    return [url for _, url in candidates]


def _unwrap_proxy_url(candidate: str) -> str:
    parsed = urlparse(candidate)
    query = parse_qs(parsed.query)
    for key in ("url", "src", "image", "img"):
        values = query.get(key)
        if not values:
            continue
        nested = values[0]
        if re.search(r"\.(?:jpg|jpeg|png|webp|gif)(?:\?|$)", nested, re.IGNORECASE):
            return nested
    return candidate


def _resolve_candidate_url(page_url: str, candidate: str) -> str:
    stripped = (
        candidate.strip().strip("\"' ")
        .replace("\\/", "/")
        .replace("\\u002F", "/")
        .replace("\\u002f", "/")
    )
    if not stripped:
        return ""
    stripped = _unwrap_proxy_url(stripped)
    return urljoin(page_url, stripped)


def _infer_image_size(url: str) -> int:
    parsed = urlparse(url)
    haystack = f"{parsed.path}?{parsed.query}".lower()
    sizes: list[int] = []

    for match in re.finditer(r"(\d{2,4})x(\d{2,4})", haystack):
        sizes.extend([int(match.group(1)), int(match.group(2))])
    for match in re.finditer(r"(?:[?&](?:w|width|format)=|[/,_-]w[_-]?)(\d{2,4})w?", haystack):
        sizes.append(int(match.group(1)))
    for match in re.finditer(r"(?:[?&](?:h|height)=|[/,_-]h[_-]?)(\d{2,4})", haystack):
        sizes.append(int(match.group(1)))
    for match in re.finditer(r"(?:[?&](?:fit|resize)=)(\d{2,4})%?2[cC,](\d{2,4})", haystack):
        sizes.extend([int(match.group(1)), int(match.group(2))])
    return max(sizes) if sizes else 0


def _candidate_priority(page_host: str, url: str, *, order: int) -> int:
    lowered = url.lower()
    score = _infer_image_size(url)
    if "/wp-content/uploads/" in lowered:
        score += 5000
    if "/uploadfile/wvenue_album/" in lowered:
        score += 4500
    if "/images/upload/articles/images/" in lowered:
        score += 7000
    if "/images/upload/articles/images682/" in lowered:
        score += 3500
    if "/images/upload/products/" in lowered or "/images/upload/partners/" in lowered:
        score += 4500
    if "theweddingnotebook.com" in page_host and ".r2.dev/inspire/" in lowered:
        score += 5500
    if "theweddingnotebook.com" in page_host and "/cover/" in lowered:
        score -= 2000
    if "theweddingnotebook.com" in page_host and "/high." in lowered:
        score += 1200
    if "theweddingnotebook.com" in page_host and "/low." in lowered:
        score -= 1200
    if "kvision.tw" in page_host and "kvisiontw.isimg.cc/uploads/" in lowered:
        score += 5000
    if "ameblo.jp" in page_host and "ameba.jp/user_images/" in lowered:
        score += 4500
    if "bridestory.com" in page_host and "/image/upload/assets/" in lowered:
        score += 6000
    if "bridestory.com" in page_host and "/images/c_fill" in lowered:
        score -= 2000
    if any(
        token in lowered
        for token in {"w_45", "h_45", "150x150", "100x100", "60x60", "45x45", "32x32"}
    ):
        score -= 5000
    if "/images/upload/products/thumbs/" in lowered:
        score -= 3500
    if "/images/upload/partners/pp/" in lowered:
        score -= 2000
    return score - order


def _extract_raw_candidate_urls(html: str) -> list[str]:
    raw_candidates: list[str] = []
    raw_candidates.extend(IMAGE_URL_PATTERN.findall(html))
    raw_candidates.extend(match.group("url") for match in GENERIC_IMAGE_VALUE_PATTERN.finditer(html))
    raw_candidates.extend(match.group("url") for match in ATTR_URL_PATTERN.finditer(html))
    for match in SRCSET_PATTERN.finditer(html):
        raw_candidates.extend(_parse_srcset_candidates(match.group("value")))
    raw_candidates.extend(
        match.group("url").strip().strip("\"' ")
        for match in STYLE_URL_PATTERN.finditer(html)
    )
    return raw_candidates


def extract_candidate_image_urls(html: str, *, page_url: str) -> list[str]:
    page_host = urlparse(page_url).netloc.lower()
    prepared_html = _preprocess_html(html)
    best_by_key: dict[str, tuple[int, str]] = {}
    for order, match in enumerate(_extract_raw_candidate_urls(prepared_html)):
        url = _resolve_candidate_url(page_url, match)
        if not url:
            continue
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
        score = _candidate_priority(page_host, url, order=order)
        existing = best_by_key.get(dedupe_key)
        if existing is not None and existing[0] >= score:
            continue
        best_by_key[dedupe_key] = (score, url)
    return [
        url
        for _, url in sorted(
            best_by_key.values(),
            key=lambda item: (-item[0], item[1]),
        )
    ]


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
        if photo["authenticity"] == "official_promotional":
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
        candidate_urls = page_candidates[page_url]
        asset_paths: list[str] = []
        for candidate_url in candidate_urls:
            if len(asset_paths) >= max(0, max_images_per_photo):
                break
            image_bytes = _safe_fetch(candidate_url, fetcher)
            if not image_bytes:
                continue
            extension = Path(urlparse(candidate_url).path).suffix.lower() or ".jpg"
            index = len(asset_paths) + 1
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
    expected_targets: set[Path] = set()
    asset_copy_tasks: list[tuple[str, Path, Path]] = []
    mapping: dict[str, list[str]] = {}

    for item in items:
        if not isinstance(item, dict):
            continue
        photo_entry_id = item.get("photo_entry_id")
        asset_paths = item.get("asset_paths")
        if not isinstance(photo_entry_id, str) or not isinstance(asset_paths, list):
            continue
        for asset_path in asset_paths:
            if not isinstance(asset_path, str):
                continue
            source_path = (root / asset_path).resolve()
            try:
                relative_inside_assets = source_path.relative_to(photo_assets_root)
            except ValueError:
                continue
            target_path = site_assets_root / relative_inside_assets
            expected_targets.add(target_path)
            asset_copy_tasks.append((photo_entry_id, source_path, target_path))

    if site_assets_root.exists():
        for existing in site_assets_root.rglob("*"):
            if existing.is_file() and existing not in expected_targets:
                existing.unlink()
        for existing in sorted(site_assets_root.rglob("*"), reverse=True):
            if existing.is_dir():
                try:
                    existing.rmdir()
                except OSError:
                    # Non-empty directories are expected when preserved assets remain in place.
                    continue

    seen_hashes: dict[str, set[str]] = {}  # venue_id -> set of md5 hashes already copied
    for photo_entry_id, source_path, target_path in asset_copy_tasks:
        if not source_path.exists():
            continue
        venue_id = target_path.parent.name
        content = source_path.read_bytes()
        content_hash = md5(content).hexdigest()
        venue_seen = seen_hashes.setdefault(venue_id, set())
        if content_hash in venue_seen:
            continue
        venue_seen.add(content_hash)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        copy2(source_path, target_path)
        relative_inside_assets = target_path.relative_to(site_assets_root)
        site_urls = mapping.setdefault(photo_entry_id, [])
        site_urls.append(f"../assets/photos/{relative_inside_assets.as_posix()}")
    return mapping
