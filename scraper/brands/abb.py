import json
import re

from bs4 import BeautifulSoup
from typing import List, Optional, Dict, Any


from ..BrandScraper import BrandScraper
from ..utils import get_html_soup, write_json
from ..CanonicalMCCB import CanonicalMCCB
from ..CanonicalMCB import CanonicalMCB
from ..CanonicalContactor import CanonicalContactor
from ..CanonicalMotorOperator import CanonicalMotorOperator
from ..CanonicalIsolator import CanonicalIsolator
from ..CanonicalSpreader import CanonicalSpreader

class AbbScraper(BrandScraper):
    """Scraper for ABB product pages at new.abb.com/products."""

    def return_dictionary_content(self, data=None, url: str | None = None, export_json: bool = False, export_path: str | None = None) -> dict | None:
        source_data = data
        is_fetch_required = source_data is None and url is not None
        
        if is_fetch_required:
            source_data = self.return_html_content(url)
            
        if not source_data:
            return None

        viewmodel = source_data if isinstance(source_data, dict) else self._extract_viewmodel(source_data)
        if not viewmodel:
            return None
            
        result = self._parse_viewmodel(viewmodel)
        
        is_export_requested = export_json and export_path and result
        if is_export_requested:
            write_json(result, export_path)
            
        return result

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

def map_abb_to_canonical_mcb(raw_dictionary: dict | None) -> CanonicalMCB | None:
    """Transforms raw parsed ABB product JSON into a CanonicalMCB instance."""
    if not raw_dictionary:
        return None

    # ABB data can either be nested inside a 'ProductViewModel' or already flattened into categories.
    attr_map = {}
    pvm = raw_dictionary.get("ProductViewModel", {})
    groups = pvm.get("Groups", []) if pvm else raw_dictionary.get("Groups", [])

    if not groups:
        # If the data was already scraped and grouped by AbbScraper.extract_product_info
        for category, attrs in raw_dictionary.items():
            if isinstance(attrs, dict):
                for k, v in attrs.items():
                    clean_k = re.sub(r'<[^>]+>', '', k).strip() # Strip HTML like <sub>n</sub>
                    attr_map[clean_k] = v
    else:
        # If raw JSON from the ViewModel API
        for group in groups:
            for attr in group.get("Attributes", []):
                name = attr.get("Name", "")
                value = attr.get("Value", "")
                clean_name = re.sub(r'<[^>]+>', '', name).strip()
                attr_map[clean_name] = value

    # --- Helpers ---
    def _extract_string(key: str) -> str:
        # Looks for exact matches first, then falls back to partial matches
        if key in attr_map:
            return str(attr_map[key])
        for k, v in attr_map.items():
            if key.lower() in k.lower():
                return str(v)
        return ""

    def _float(val: str) -> float:
        if not val: return 0.0
        cleaned = re.search(r"([\d.,]+)", val)
        if cleaned:
            return float(cleaned.group(1).replace(",", "."))
        return 0.0

    def _int(val: str) -> int:
        if not val: return 0
        cleaned = re.search(r"(\d+)", val)
        return int(cleaned.group(1)) if cleaned else 0

    def _parse_capacity(val: str) -> dict[str, float]:
        """Parses strings like '(230 V AC) 10 kA' or '["(AC) 6 kA", "(400 V AC) 6 kA"]' into a dict."""
        caps = {}
        if not val: return caps
        
        matches = re.finditer(r"\((.*?)\)\s*([\d.,]+)\s*kA", val)
        found_specific_voltage = False
        generic_caps = {}
        
        for m in matches:
            voltage_str = m.group(1).strip()
            ka_val = float(m.group(2).replace(',', '.'))
            
            # Check if the parenthesis actually contains numbers (e.g., "400 V AC")
            if any(char.isdigit() for char in voltage_str):
                caps[voltage_str] = ka_val
                found_specific_voltage = True
            else:
                # Store non-voltage qualifiers (like "AC" or "DC") temporarily
                generic_caps[f"Default {voltage_str}"] = ka_val
                
        # If specific voltages were found, ignore the generics to keep the keys clean.
        # If NO specific voltages were found, append the generic ones (e.g., "Default AC")
        if not found_specific_voltage and generic_caps:
            caps.update(generic_caps)
            
        # Fallback if no parenthesis format was used at all (e.g., just "10 kA")
        if not caps and not generic_caps:
            fallback = re.search(r"([\d.,]+)\s*kA", val)
            if fallback:
                caps["Default"] = float(fallback.group(1).replace(',', '.'))
                
        return caps

    def _parse_frequency(val: str) -> Optional[float | list[float]]:
        if not val: return None
        matches = re.findall(r"([\d.,]+)", val)
        floats = [float(m.replace(',', '.')) for m in matches]
        if not floats: return None
        return floats[0] if len(floats) == 1 else floats

    # --- Core Properties ---
    display_name = raw_dictionary.get("DisplayName") or attr_map.get("Display Name", attr_map.get("Product ID", ""))
    sku = attr_map.get("Global ID", attr_map.get("Order Code", attr_map.get("Product ID", display_name)))
    
    # --- Images ---
    image_urls = []
    if pvm and "Images" in pvm:
        for img in pvm["Images"]:
            url = img.get("PublicUrl") or img.get("Url", "")
            if url:
                if url.startswith("//"): url = "https:" + url
                image_urls.append(url)
    else:
        images_val = attr_map.get("Images", [])
        if isinstance(images_val, list):
            for img in images_val:
                url = img if isinstance(img, str) else img.get("PublicUrl", img.get("Url", ""))
                if url:
                    if url.startswith("//"): url = "https:" + url
                    image_urls.append(url)

    # --- Documents ---
    doc_id = attr_map.get("Data Sheet, Technical Information")
    if doc_id:
        datasheet_url = f"https://search.abb.com/library/Download.aspx?DocumentID={doc_id}&LanguageCode=en&DocumentPartId=&Action=Launch"
    else:
        product_id = attr_map.get("Product ID", sku)
        datasheet_url = f"https://search.abb.com/library/Download.aspx?DocumentID={product_id}&LanguageCode=en&DocumentPartId=&Action=Launch" if product_id else None

    # --- Capacities (with Ics -> Icn fallback) ---
    ics_str = _extract_string("Rated Service Short-Circuit Breaking Capacity")
    icn_str = _extract_string("Rated Short-Circuit Capacity")
    icu_str = _extract_string("Rated Ultimate Short-Circuit Breaking Capacity")

    # Parse Ics first. If the dictionary is empty (meaning no Ics data exists), parse Icn instead.
    ics_dict = _parse_capacity(ics_str)
    if not ics_dict:
        ics_dict = _parse_capacity(icn_str)
        
    icu_dict = _parse_capacity(icu_str)

    # --- Weight Handling (Convert grams to kg if necessary) ---
    weight_str = _extract_string("Product Net Weight")
    weight_kg = _float(weight_str)
    if weight_kg and "g" in weight_str.lower() and "kg" not in weight_str.lower():
        weight_kg = weight_kg / 1000.0

    return CanonicalMCB(
        sku=sku,
        brand="ABB",
        display_name=display_name,
        poles=_int(_extract_string("Number of Poles")),
        protected_poles=_int(_extract_string("Number of Protected Poles")),
        rated_current_a=_float(_extract_string("Rated Current (In)")),
        tripping_characteristic=_extract_string("Tripping Characteristic"),
        voltage_to_service_short_circuit_breaking_capacity_ka=ics_dict,
        voltage_to_ultimate_short_circuit_breaking_capacity_ka=icu_dict,
        height_mm=_float(_extract_string("Product Net Height")),
        width_mm=_float(_extract_string("Product Net Width")),
        depth_mm=_float(_extract_string("Product Net Depth")),
        datasheet_url=datasheet_url,
        image_urls=image_urls if image_urls else None,
        rated_frequency_hz=_parse_frequency(_extract_string("Rated Frequency (f)")),
        weight_kg=weight_kg if weight_kg else None
    )

def extract_voltage_range(raw_list: List[str]) -> Dict[str, Optional[str]]:
    """Helper to convert list strings into min/max dictionary."""
    if not raw_list:
        return {"minimum": None, "maximum": None}
    
    # Simple regex to grab numbers from the first entry
    vals = re.findall(r'\d+', raw_list[0])
    return {
        "minimum": f"{vals[0]}V AC" if len(vals) > 0 else None,
        "maximum": f"{vals[1]}V AC" if len(vals) > 1 else None
    }

def _parse_voltage_string(v_str: str) -> Dict[str, Any]:
    """
    Parses strings like '220\u2026250 V AC' or '220 ... 250 V AC'
    into {'min': 220, 'max': 250, 'unit': 'V'}
    """
    # Regex: Capture number1, separator(s), number2, and then the unit
    pattern = r'(\d+)\s*[…\.]+\s*(\d+)\s*([a-zA-Z]+)'
    match = re.search(pattern, v_str)
    if match:
        return {
            "minimum": float(match.group(1)),
            "maximum": float(match.group(2)),
            "unit": match.group(3)
        }
    return {"minimum": None, "maximum": None, "unit": None}

def get_datasheet_url(certs: Dict[str, Any]) -> Optional[str]:
    """Helper to extract the first available technical datasheet URL."""
    ds_list = certs.get("Data Sheet, Technical Information", [])
    if isinstance(ds_list, list) and ds_list:
        return f"https://search.abb.com/library/Download.aspx?DocumentID={ds_list[0]}&LanguageCode=en"
    return None

def extract_operational_voltage(tech_info: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """Parses Rated Voltage to the new operational_voltage structure."""
    raw_voltages = tech_info.get("Rated Voltage (U<sub>r</sub>)", [])
    if not raw_voltages:
        return {"minimum": None, "maximum": None}
    
    # Use the regex parser you already have to get numbers
    vals = re.findall(r'\d+', str(raw_voltages[0]))
    return {
        "minimum": f"{vals[0]}V" if len(vals) > 0 else None,
        "maximum": f"{vals[1]}V" if len(vals) > 1 else vals[0] + "V" # Handle single voltage
    }

def map_abb_to_canonical_motor_operator(raw_data: Dict[str, Any]) -> CanonicalMotorOperator:
    gen_info = raw_data.get("General Information", {})
    tech_info = raw_data.get("Technical", {})
    add_info = raw_data.get("Additional Information", {})
    certs = raw_data.get("Certificates and Declarations", {})
    
    return CanonicalMotorOperator(
        sku=gen_info.get("Global ID"),
        brand="ABB",
        display_name=gen_info.get("Display Name"),
        description=gen_info.get("Meta Description"),
        ean=raw_data.get("Classification", {}).get("Level 1 EAN"),
        # New Fields
        operational_voltage=extract_operational_voltage(tech_info),
        voltage_protection_level=tech_info.get("Impulse Withstand Voltage (U<sub>imp</sub>)"),
        datasheet_url=get_datasheet_url(certs),
        # Existing Fields
        voltage_range_ac=[_parse_voltage_string(v) for v in tech_info.get("Rated Voltage (U<sub>r</sub>)", []) if "AC" in v.upper()],
        voltage_range_dc=[_parse_voltage_string(v) for v in tech_info.get("Rated Voltage (U<sub>r</sub>)", []) if "DC" in v.upper()],
        current_type=tech_info.get("Current Type"),
        suitable_for_breakers=[add_info.get("Suitable For", "")],
        product_class=add_info.get("Suitable for Product Class"),
        configuration_type=tech_info.get("Configuration Type"),
        is_auto_reset="Auto-Reset" in gen_info.get("Display Name", ""),
        standards=tech_info.get("Standards", []),
        image_urls=gen_info.get("Images", [])
    )

def map_abb_to_canonical_isolator(raw_data: Dict[str, Any]) -> CanonicalIsolator:
    """
    Maps ABB Isolator raw JSON to a CanonicalIsolator object, 
    correctly targeting Electrical and Popular Downloads metadata.
    """
    gen_info = raw_data.get("General Information", {})
    dims = raw_data.get("Dimensions", {})
    elec = raw_data.get("Electrical", {})
    downloads = raw_data.get("Popular Downloads", {})
    
    # 1. Extract basic identity
    short_name = gen_info.get("Short Name", "")
    poles_match = re.search(r'(\d+)P', short_name)
    current_match = re.search(r'(\d+)A', short_name)
    
    # 2. Extract and parse operational voltage
    # Looks for strings containing "Minimum" or "Maximum" in the Electrical section
    ops_volt = elec.get("Operational Voltage", [])
    operational_voltage = {
        "minimum": next((v.replace("Minimum ", "") for v in ops_volt if "Minimum" in v), None),
        "maximum": next((v.replace("Maximum ", "") for v in ops_volt if "Maximum" in v), None)
    }
    
    # 3. Extract datasheet from Popular Downloads
    ds_id = downloads.get("Data Sheet, Technical Information")
    datasheet_url = f"https://search.abb.com/library/Download.aspx?DocumentID={ds_id}&LanguageCode=en" if ds_id else None

    # 4. Helper for dimensions
    def parse_dim(key):
        val = dims.get(key, "0")
        match = re.search(r'\d+(\.\d+)?', str(val))
        return float(match.group()) if match else None

    return CanonicalIsolator(
        sku=gen_info.get("Global ID"),
        brand="ABB",
        display_name=gen_info.get("Display Name"),
        rated_current_a=float(current_match.group(1)) if current_match else None,
        number_of_poles=int(poles_match.group(1)) if poles_match else None,
        operational_voltage=operational_voltage,
        voltage_protection_level=elec.get("Voltage Protection Level ( Up)"),
        datasheet_url=datasheet_url,
        width_mm=parse_dim("Product Net Width"),
        height_mm=parse_dim("Product Net Height"),
        depth_mm=parse_dim("Product Net Depth / Length"),
        modular_spacings=int(dims.get("Width in Number of Modular Spacings", 0)),
        image_urls=gen_info.get("Images", [])
    )


def map_abb_to_canonical_spreader(raw_data: Dict[str, Any]) -> CanonicalSpreader:
    gen_info = raw_data.get("General Information", {})
    add_info = raw_data.get("Additional Information", {})
    tech = raw_data.get("Technical", {})
    order = raw_data.get("Ordering", {})
    dims = raw_data.get("Dimensions", {})  # Added Dimensions
    certs = raw_data.get("Certificates and Declarations", {})
    
    # 1. Look for 'Product Net Weight' in Dimensions first
    # 2. Fallback to 'Package Level 1 Gross Weight' if not found
    weight_str = dims.get("Product Net Weight") or dims.get("Package Level 1 Gross Weight", "0")
    
    # Extract numeric value
    weight_match = re.search(r'[\d\.]+', str(weight_str))
    weight_val = float(weight_match.group()) if weight_match else None

    # Handle suitable for (ensure it's a list)
    suitable = add_info.get("Suitable For", [])
    suitable_list = [suitable] if isinstance(suitable, str) else suitable

    return CanonicalSpreader(
        sku=gen_info.get("Global ID"),
        brand="ABB",
        display_name=gen_info.get("Display Name"),
        description=gen_info.get("Meta Description"),
        datasheet_url=get_datasheet_url(certs),
        weight_kg=weight_val,
        configuration_type=tech.get("Configuration Type"),
        number_of_poles=tech.get("Number of Poles"),
        order_multiple=tech.get("Order Multiple"),
        suitable_for=suitable_list,
        image_urls=gen_info.get("Images", [])
    )