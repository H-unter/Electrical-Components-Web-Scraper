import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from ..BrandScraper import BrandScraper
from ..utils import get_html_soup
from ..CanonicalMCCB import CanonicalMCCB
from ..CanonicalContactor import CanonicalContactor



# Cache file lives alongside this source file so it travels with the project
_CACHE_PATH = Path(__file__).parent / "abb_sitemap_cache.json"
_CACHE_MAX_AGE_DAYS = 7   # re-fetch after this many days


class AbbScraper(BrandScraper):
    """Scraper for ABB product pages at new.abb.com/products.

    URL resolution strategy
    -----------------------
    ABB product URLs have the form:
        https://new.abb.com/products/{ARTICLE_NUMBER}/{slug}

    The article number (e.g. 1SBL367201R1300) cannot be derived from a type
    designation (e.g. AF52400013), so we resolve it via a slug → full-URL
    lookup table built from ABB's product sitemaps.

    The lookup table is persisted to ``scraper/brands/abb_sitemap_cache.json``
    so the 27 sitemaps are only fetched once and reused across runs.
    The cache is automatically refreshed when it is older than
    ``_CACHE_MAX_AGE_DAYS`` days, or when ``force_refresh=True`` is passed
    to the constructor.

    Constructor parameters
    ----------------------
    force_refresh : bool
        Pass ``True`` to ignore any existing cache and re-download all
        sitemaps immediately.  Useful after a large ABB catalog update.
    """

    BASE_URL         = "https://new.abb.com/products"
    SITEMAP_BASE_URL = "https://new.abb.com/pissitemap"

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    # In-process cache — shared across all instances within one Python session
    _slug_to_url: dict[str, str] = {}
    _in_memory_loaded: bool = False

    def __init__(self, force_refresh: bool = False) -> None:
        self._force_refresh = force_refresh

    # ------------------------------------------------------------------
    # BrandScraper interface
    # ------------------------------------------------------------------

    def get_soup(self, sku: str) -> BeautifulSoup | None:
        """Resolve the canonical product URL for *sku* and return its soup."""
        clean_sku = sku.strip().strip("/")

        # Warm the in-process cache (reads disk cache or fetches from web)
        if not AbbScraper._in_memory_loaded or self._force_refresh:
            self._ensure_cache_loaded()

        # 1. Derive slug and look it up
        slug = self._derive_slug(clean_sku)
        cached_url = AbbScraper._slug_to_url.get(slug)
        if cached_url:
            soup = get_html_soup(cached_url)
            if soup:
                return soup

        # 2. Fallback — direct URLs (MCCBs whose article number = URL segment)
        for url in (
            f"{self.BASE_URL}/{clean_sku.upper()}",
            f"{self.BASE_URL}/{clean_sku.lower()}",
        ):
            soup = get_html_soup(url)
            if soup:
                return soup

        print(f"Could not retrieve page for SKU '{sku}'.")
        return None

    def extract_product_info(self, soup: BeautifulSoup) -> dict:
        """Parses the embedded JS `model` variable and returns a nested dict."""
        viewmodel = self._extract_viewmodel(soup)
        if not viewmodel:
            return {}
        return self._parse_viewmodel(viewmodel)

    # ------------------------------------------------------------------
    # Slug derivation
    # ------------------------------------------------------------------

    @staticmethod
    def _derive_slug(sku: str) -> str:
        """Convert a compact ABB type designation into its URL slug form.

        Rules
        -----
        * Already has dashes → lowercase only.
          ESB63-22N-06  →  esb63-22n-06
        * Pure letter-prefix + 8+ digit body (AF contactors):
          Last 6 digits = 3 × 2-digit config codes; rest = frame size.
          AF52400013  →  af52-40-00-13
          AF145300013 →  af145-30-00-13
        * Anything else (MCCB article numbers like 1SDA067416R1) → lowercase.
          The sitemap cache will still match it if ABB uses it as a slug.
        """
        sku = sku.strip()

        if "-" in sku:
            return sku.lower()

        m = re.match(r'^([A-Za-z]+)(\d+)$', sku)
        if m:
            letters = m.group(1).lower()
            digits  = m.group(2)
            if len(digits) >= 8:
                frame  = digits[:-6]
                config = digits[-6:]
                pairs  = [config[i:i+2] for i in range(0, 6, 2)]
                return "-".join([letters + frame] + pairs)

        return sku.lower()

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------

    def _ensure_cache_loaded(self) -> None:
        """Load slug → URL table from disk cache, or rebuild it from the web.

        Decision logic:
          1. If force_refresh=True                    → fetch from web, save
          2. Disk cache exists and is fresh enough    → load from disk
          3. Disk cache missing or stale              → fetch from web, save
        """
        if self._force_refresh:
            print("force_refresh=True — rebuilding ABB sitemap cache from web…")
            self._fetch_and_save_cache()
            return

        if _CACHE_PATH.exists():
            age_days = self._cache_age_days()
            if age_days <= _CACHE_MAX_AGE_DAYS:
                self._load_from_disk()
                return
            else:
                print(
                    f"ABB sitemap cache is {age_days:.1f} days old "
                    f"(limit {_CACHE_MAX_AGE_DAYS}d) — refreshing…"
                )

        self._fetch_and_save_cache()

    def _cache_age_days(self) -> float:
        """Return how many days old the on-disk cache is."""
        try:
            data = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
            saved_at = datetime.fromisoformat(data["saved_at"])
            now = datetime.now(timezone.utc)
            # Make saved_at timezone-aware if it isn't already
            if saved_at.tzinfo is None:
                saved_at = saved_at.replace(tzinfo=timezone.utc)
            return (now - saved_at).total_seconds() / 86400
        except Exception:
            return float("inf")   # treat unreadable cache as infinitely old

    def _load_from_disk(self) -> None:
        """Deserialise the JSON cache file into the in-process dict."""
        try:
            data = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
            AbbScraper._slug_to_url = data["slug_to_url"]
            AbbScraper._in_memory_loaded = True
            print(
                f"ABB sitemap cache loaded from disk "
                f"({len(AbbScraper._slug_to_url):,} URLs, "
                f"saved {data.get('saved_at', 'unknown')[:10]})."
            )
        except Exception as e:
            print(f"Failed to read ABB cache from disk: {e} — rebuilding…")
            self._fetch_and_save_cache()

    def _fetch_and_save_cache(self) -> None:
        """Download all sitemaps, build the slug → URL dict, write to disk.

        Rather than trusting the sitemap index (which only lists 4 of the 27
        actual files), we probe sitemap1.xml, sitemap2.xml, … in order and
        stop as soon as a request returns a 404 or yields zero product URLs.
        """
        slug_to_url: dict[str, str] = {}
        base = "https://new.abb.com/pissitemap"

        print("Fetching ABB sitemaps — this runs once then is cached to disk…")
        t0 = time.monotonic()

        for n in range(1, 1000):           # upper bound is a safety rail only
            url   = f"{base}/sitemap{n}.xml"
            count = self._fetch_sub_sitemap_into(url, slug_to_url)
            print(f"  sitemap{n}.xml: {count:,} URLs")
            if count == 0:                 # 404 or empty page — we're done
                break

        elapsed = time.monotonic() - t0
        print(f"  Done — {len(slug_to_url):,} total URLs in {elapsed:.1f}s")

        # Persist to disk
        cache_data = {
            "saved_at":   datetime.now(timezone.utc).isoformat(),
            "slug_to_url": slug_to_url,
        }
        try:
            _CACHE_PATH.write_text(
                json.dumps(cache_data, separators=(",", ":")),
                encoding="utf-8",
            )
            print(f"  Cache saved to {_CACHE_PATH}")
        except Exception as e:
            print(f"  Warning: could not save cache to disk: {e}")

        AbbScraper._slug_to_url      = slug_to_url
        AbbScraper._in_memory_loaded = True
        self._force_refresh          = False   # don't repeat within same session

    def _fetch_sub_sitemap_into(self, url: str, target: dict) -> int:
        """Fetch one sub-sitemap and insert slug → URL pairs into *target*.

        Returns the number of product URLs added.  Returns 0 (without printing
        an error) on a 404, since that is the expected signal that we have
        iterated past the last sitemap file.  Other HTTP errors are reported.
        """
        try:
            resp = requests.get(url, headers=self.HEADERS, timeout=30)
            if resp.status_code == 404:
                return 0          # clean stop signal — not an error
            resp.raise_for_status()
            soup  = BeautifulSoup(resp.text, "xml")
            count = 0
            for loc in soup.find_all("loc"):
                full_url = loc.text.strip()
                if not full_url or "/products/" not in full_url:
                    continue
                slug = full_url.rstrip("/").split("/")[-1].lower()
                if slug:
                    target[slug] = full_url
                    count += 1
            return count
        except Exception as e:
            print(f"  Failed to parse {url}: {e}")
            return 0

    # ------------------------------------------------------------------
    # Viewmodel extraction (unchanged)
    # ------------------------------------------------------------------

    def _extract_viewmodel(self, soup: BeautifulSoup) -> dict | None:
        for script in soup.find_all("script"):
            if script.string and "var model =" in script.string:
                match = re.search(
                    r"var model\s*=\s*(\{.*?\}*?\});\s*jsLibs\.push",
                    script.string,
                    re.DOTALL,
                )
                if match:
                    try:
                        return json.loads(match.group(1))
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse ABB model JSON: {e}")
                        return None
        print("Could not find 'var model' block in ABB page HTML.")
        return None

    def _parse_viewmodel(self, model: dict) -> dict:
        product_info = model.get("ProductViewModel", {}).get("Product", {})
        image_list = (
            product_info.get("productDetails", {})
            .get("item", {})
            .get("images", [])
        )
        urls = [img["url"] for img in image_list if "url" in img]

        result = {
            "General Information": {
                "Display Name":       model.get("DisplayName", ""),
                "Short Name":         model.get("ShortName", ""),
                "Product URL Suffix": model.get("ProductURLSuffix", ""),
                "Meta Description":   model.get("MetaDescription", ""),
                "Global ID":          model.get("GlobalId", ""),
                "Images":             urls if len(urls) > 1 else (urls[0] if urls else ""),
            }
        }

        attribute_groups = product_info.get("attributeGroups", {}).get("items", [])
        for i, group in enumerate(attribute_groups):
            group_name = group.get("description", f"Group {i}")
            result[group_name] = {}
            for attr_key, attr_data in group.get("attributes", {}).items():
                attr_name = attr_data.get("attributeName", attr_key)
                values = [v["text"] for v in attr_data.get("values", []) if "text" in v]
                result[group_name][attr_name] = (
                    "" if not values else values[0] if len(values) == 1 else values
                )

        return result


def map_abb_to_canonical_mccb(raw: dict | None) -> CanonicalMCCB | None:
    """Transforms raw parsed ABB dictionary structures into a CanonicalMCCB instance."""
    if not raw:
        return None
    gen   = raw.get("General Information", {})
    tech  = raw.get("Technical", {})
    dims  = raw.get("Dimensions", {})
    certs = raw.get("Certificates and Declarations", {})

    def _num(val) -> float:
        s = val[0] if isinstance(val, list) and val else val
        return float(re.sub(r"[^\d.]", "", str(s).replace(",", "."))) if s else 0.0

    def _find_val(d: dict, pattern: str):
        return next((v for k, v in d.items() if pattern in k), None)

    def _parse_capacity(raw_val) -> dict[str, float]:
        lines = raw_val if isinstance(raw_val, list) else ([raw_val] if raw_val else [])
        pairs = [
            re.search(r"\((.*?)\)\s*([\d.]+)", str(line))
            for line in lines if "(" in str(line)
        ]
        return {m.group(1).replace(" ", ""): float(m.group(2)) for m in pairs if m}

    freq_str = tech.get("Rated Frequency (f)", "50 / 60 Hz")
    freq = (
        [float(x) for x in re.findall(r"\d+", str(freq_str))]
        if "/" in str(freq_str) or "-" in str(freq_str)
        else _num(freq_str)
    )

    u_op_str   = _find_val(tech, "Rated Operational Voltage") or ""
    u_op_clean = u_op_str[0] if isinstance(u_op_str, list) and u_op_str else u_op_str
    u_op = (
        _num(str(u_op_clean).split("V AC")[0])
        if "V AC" in str(u_op_clean)
        else _num(u_op_clean)
    )

    doc_list = certs.get("Data Sheet, Technical Information", [])
    doc_id   = doc_list[0] if isinstance(doc_list, list) and doc_list else None

    return CanonicalMCCB(
        sku=gen.get("Global ID", ""),
        brand="ABB",
        display_name=gen.get("Display Name", ""),
        datasheet_url=(
            f"https://search.abb.com/library/Download.aspx?DocumentID={doc_id}"
            f"&LanguageCode=en&DocumentPartId=&Action=Launch"
            if doc_id else None
        ),
        image_urls=gen.get("Images", []) if isinstance(gen.get("Images"), list) else [],
        poles=int(str(_find_val(tech, "Number of Poles") or "3").replace("P", "")),
        rated_current_a=_num(_find_val(tech, "Rated Current")),
        rated_frequency_hz=freq,
        u_imp=_num(_find_val(tech, "Rated Impulse Withstand")),
        u_insulation=_num(_find_val(tech, "Rated Insulation Voltage")),
        u_operational=u_op,
        trip_type=tech.get("Release Type", "TM"),
        voltage_to_short_circuit_breaking_capacity_ka=_parse_capacity(
            _find_val(tech, "Rated Service Short-Circuit")
        ),
        voltage_to_ultimate_short_circuit_breaking_capacity_ka=_parse_capacity(
            _find_val(tech, "Rated Ultimate Short-Circuit")
        ),
        height_mm=_num(dims.get("Product Net Height", "0")),
        width_mm=_num(dims.get("Product Net Width", "0")),
        depth_mm=_num(dims.get("Product Net Depth / Length", "0")),
        weight_kg=_num(dims.get("Product Net Weight", "0")) or None,
    )


def map_abb_to_canonical_contactor(raw: dict | None) -> CanonicalContactor | None:
    """Transforms a raw parsed ABB contactor dictionary into a CanonicalContactor instance.

    Handles both power contactors (AF series, e.g. AF52-40-00-13) and
    installation contactors (ESB series, e.g. ESB63-22N-06), whose field
    shapes differ in several places:

    - operational_voltage: AF series → single string "Main Circuit 690 V";
      ESB series → list including DC entries — AC maximum is taken.
    - insulation_voltage: may be a list of IEC/UL values — IEC value preferred.
    - impulse_withstand_voltage: stored as "6 kV" — converted to 6000 V.
    - AC-1/AC-3 current maps: AF series keyed by voltage+temperature rows;
      ESB series keyed by contact type (NO/NC) or voltage. Highest amperage
      wins when multiple rows share the same voltage key.
    - datasheet ID lives in 'Popular Downloads', not 'Certificates'.
    """
    if not raw:
        return None

    gen  = raw.get("General Information", {})
    tech = raw.get("Technical", {})
    dims = raw.get("Dimensions", {})
    docs = raw.get("Popular Downloads", {})

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _num(val) -> float:
        s = val[0] if isinstance(val, list) and val else val
        return float(re.sub(r"[^\d.]", "", str(s).replace(",", "."))) if s else 0.0

    def _parse_operational_voltage(raw_val) -> int:
        """Return the highest AC voltage found; DC entries are ignored."""
        lines = raw_val if isinstance(raw_val, list) else [raw_val]
        best = 0
        for line in lines:
            if "DC" in str(line):
                continue
            m = re.search(r"(\d+)\s*V", str(line))
            if m:
                best = max(best, int(m.group(1)))
        return best

    def _parse_insulation_voltage(raw_val) -> int:
        """Return IEC-rated insulation voltage; fall back to first numeric value."""
        lines = raw_val if isinstance(raw_val, list) else [raw_val]
        iec_val, first_val = None, None
        for line in lines:
            m = re.search(r"(\d+)\s*V", str(line))
            if not m:
                continue
            v = int(m.group(1))
            if first_val is None:
                first_val = v
            if "IEC" in str(line) and iec_val is None:
                iec_val = v
        return iec_val or first_val or 0

    def _parse_impulse_voltage(raw_val) -> int:
        """Convert '6 kV' → 6000 or '6000 V' → 6000."""
        m = re.search(r"([\d.]+)\s*(kV|V)", str(raw_val), re.IGNORECASE)
        if m:
            val = float(m.group(1))
            return int(val * 1000 if m.group(2).lower() == "kv" else val)
        return 0

    def _parse_current_map(raw_val) -> dict[str, float]:
        """Parse AC current entries into a {key: amps} dict.

        Voltage+temperature rows like '(690 V) 40 °C 100 A' → {'690V@40C': 100.0}
        Slash-voltage rows '(380 / 400 V) 60 °C 53 A'       → {'400V@60C': 53.0}
        Voltage-only rows '(230 V) Single Phase, NO 30 A'    → {'230V': 30.0}
        Contact-type rows '(NO) 63 A'                        → {'NO': 63.0}
        """
        lines = raw_val if isinstance(raw_val, list) else ([raw_val] if raw_val else [])
        result: dict[str, float] = {}
        for line in lines:
            s = str(line)
            parens = re.search(r"\(([^)]+)\)", s)
            if not parens:
                continue
            amp_m = re.search(r"([\d.]+)\s*A\s*$", s)
            if not amp_m:
                continue
            amps    = float(amp_m.group(1))
            key_raw = parens.group(1).strip()
            if re.search(r"\d+\s*V", key_raw):
                voltages    = re.findall(r"(\d+)\s*V", key_raw)
                voltage_key = voltages[-1] + "V"          # last voltage in slash list
                temp_m      = re.search(r"(\d+)\s*°C", s)
                key         = f"{voltage_key}@{temp_m.group(1)}C" if temp_m else voltage_key
            else:
                key = key_raw                             # e.g. 'NO', 'NC'
            result[key] = amps
        return result

    # ------------------------------------------------------------------
    # Field extraction
    # ------------------------------------------------------------------

    doc_id       = docs.get("Data Sheet, Technical Information")
    datasheet_url = (
        f"https://search.abb.com/library/Download.aspx?DocumentID={doc_id}"
        f"&LanguageCode=en&DocumentPartId=&Action=Launch"
        if doc_id else None
    )

    images_raw = gen.get("Images", "")
    image_urls = images_raw if isinstance(images_raw, list) else ([images_raw] if images_raw else [])

    poles_raw = str(tech.get("Number of Poles", "4")).replace("P", "").strip()
    poles     = int(poles_raw) if poles_raw.isdigit() else 4

    return CanonicalContactor(
        sku=gen.get("Global ID", ""),
        brand="ABB",
        display_name=gen.get("Display Name", ""),
        datasheet_url=datasheet_url,
        image_urls=image_urls,
        poles=poles,
        normally_open_contacts=int(_num(tech.get("Number of Main Contacts NO", "0"))),
        normally_closed_contacts=int(_num(tech.get("Number of Main Contacts NC", "0"))),
        voltage_to_rated_ac1_current_a=_parse_current_map(
            tech.get("Rated Operational Current AC-1 (I<sub>e</sub>)", [])
        ),
        voltage_to_rated_ac3_current_a=_parse_current_map(
            tech.get("Rated Operational Current AC-3 (I<sub>e</sub>)", [])
        ),
        operational_voltage_v=_parse_operational_voltage(
            tech.get("Rated Operational Voltage", "0")
        ),
        insulation_voltage_v=_parse_insulation_voltage(
            tech.get("Rated Insulation Voltage (U<sub>i</sub>)", "0")
        ),
        impulse_withstand_voltage_v=_parse_impulse_voltage(
            tech.get("Rated Impulse Withstand Voltage (U<sub>imp</sub>)", "0")
        ),
        height_mm=_num(dims.get("Product Net Height", "0")),
        width_mm=_num(dims.get("Product Net Width", "0")),
        depth_mm=_num(dims.get("Product Net Depth / Length", "0")),
        weight_kg=_num(dims.get("Product Net Weight", "0")) or None,
    )