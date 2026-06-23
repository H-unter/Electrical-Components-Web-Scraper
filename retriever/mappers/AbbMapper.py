import re
from typing import Any, Dict, List, Optional
from retriever.models.CanonicalContactor import CanonicalContactor
from retriever.models.CanonicalIsolator import CanonicalIsolator
from retriever.models.CanonicalMCB import CanonicalMCB
from retriever.models.CanonicalMCCB import CanonicalMCCB
from retriever.models.CanonicalMotorOperator import CanonicalMotorOperator
from retriever.models.CanonicalSpreader import CanonicalSpreader

# ==============================================================================
# SHARED UTILITY FUNCTIONS
# ==============================================================================

def _to_float(val: Any) -> float:
    """Extracts a clean float from a string, list, or numeric value."""
    if not val:
        return 0.0
    s = val[0] if isinstance(val, list) and val else val
    cleaned = re.sub(r"[^\d.]", "", str(s).replace(",", "."))
    return float(cleaned) if cleaned and cleaned != "." else 0.0


def _build_datasheet_url(doc_id: Any) -> Optional[str]:
    """Constructs a standardized ABB datasheet URL from a document ID/list."""
    actual_id = doc_id[0] if isinstance(doc_id, list) and doc_id else doc_id
    if not actual_id:
        return None
    return f"https://search.abb.com/library/Download.aspx?DocumentID={actual_id}&LanguageCode=en&DocumentPartId=&Action=Launch"


def _normalize_images(images_val: Any) -> List[str]:
    """Normalizes image data structures (strings, lists, dicts) into valid URLs."""
    if not images_val:
        return []
    raw_list = images_val if isinstance(images_val, list) else [images_val]
    urls = []
    for img in raw_list:
        url = img if isinstance(img, str) else (img.get("PublicUrl") or img.get("Url", ""))
        if url:
            if url.startswith("//"):
                url = "https:" + url
            urls.append(url)
    return urls


def _find_val(d: dict, pattern: str) -> Any:
    """Finds a value in a dictionary where the key contains the given pattern."""
    return next((v for k, v in d.items() if pattern in k), None)


def _parse_capacity(raw_val: Any) -> Dict[str, float]:
    """Parses short-circuit breaking capacity text into a structured mapping."""
    lines = raw_val if isinstance(raw_val, list) else ([raw_val] if raw_val else [])
    pairs = [
        re.search(r"\((.*?)\)\s*([\d.]+)", str(line))
        for line in lines if "(" in str(line)
    ]
    return {m.group(1).replace(" ", ""): float(m.group(2)) for m in pairs if m}


# ==============================================================================
# MAPPER FUNCTIONS
# ==============================================================================

def map_abb_to_canonical_mccb(raw: dict | None) -> CanonicalMCCB | None:
    """Transforms raw parsed ABB dictionary structures into a CanonicalMCCB instance."""
    if not raw:
        return None
    gen   = raw.get("General Information", {})
    tech  = raw.get("Technical", {})
    dims  = raw.get("Dimensions", {})
    certs = raw.get("Certificates and Declarations", {})

    freq_str = tech.get("Rated Frequency (f)", "50 / 60 Hz")
    freq = (
        [float(x) for x in re.findall(r"\d+", str(freq_str))]
        if "/" in str(freq_str) or "-" in str(freq_str)
        else _to_float(freq_str)
    )

    u_op_str   = _find_val(tech, "Rated Operational Voltage") or ""
    u_op_clean = u_op_str[0] if isinstance(u_op_str, list) and u_op_str else u_op_str
    u_op = _to_float(str(u_op_clean).split("V AC")[0]) if "V AC" in str(u_op_clean) else _to_float(u_op_clean)

    return CanonicalMCCB(
        m_sku=gen.get("Global ID", ""),
        m_brand="ABB",
        m_name=gen.get("Display Name", ""),
        datasheet=_build_datasheet_url(certs.get("Data Sheet, Technical Information")),
        img=_normalize_images(gen.get("Images")),
        m_poles=int(str(_find_val(tech, "Number of Poles") or "3").replace("P", "")),
        m_i_n=_to_float(_find_val(tech, "Rated Current")),
        m_f_n=freq,
        m_u_imp=_to_float(_find_val(tech, "Rated Impulse Withstand")),
        m_u_insu=_to_float(_find_val(tech, "Rated Insulation Voltage")),
        m_u_n=u_op,
        m_trip_type=tech.get("Release Type", "TM"),
        m_i_sc=_parse_capacity(_find_val(tech, "Rated Service Short-Circuit")),
        m_i_cu=_parse_capacity(_find_val(tech, "Rated Ultimate Short-Circuit")),
        m_height_mm=_to_float(dims.get("Product Net Height", "0")),
        m_width_mm=_to_float(dims.get("Product Net Width", "0")),
        m_depth_mm=_to_float(dims.get("Product Net Depth / Length", "0")),
        m_weight_kg=_to_float(dims.get("Product Net Weight", "0")) or None,
    )


def map_abb_to_canonical_contactor(raw: dict | None) -> CanonicalContactor | None:
    """Transforms a raw parsed ABB contactor dictionary into a CanonicalContactor instance."""
    if not raw:
        return None

    gen  = raw.get("General Information", {})
    tech = raw.get("Technical", {})
    dims = raw.get("Dimensions", {})
    docs = raw.get("Popular Downloads", {})

    def _parse_operational_voltage(raw_val) -> int:
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
        m = re.search(r"([\d.]+)\s*(kV|V)", str(raw_val), re.IGNORECASE)
        if m:
            val = float(m.group(1))
            return int(val * 1000 if m.group(2).lower() == "kv" else val)
        return 0

    def _parse_current_map(raw_val) -> dict[str, float]:
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
                voltage_key = voltages[-1] + "V"
                temp_m      = re.search(r"(\d+)\s*°C", s)
                key         = f"{voltage_key}@{temp_m.group(1)}C" if temp_m else voltage_key
            else:
                key = key_raw
            result[key] = amps
        return result

    poles_raw = str(tech.get("Number of Poles", "4")).replace("P", "").strip()
    poles     = int(poles_raw) if poles_raw.isdigit() else 4

    return CanonicalContactor(
        m_sku=gen.get("Global ID", ""),
        m_brand="ABB",
        m_display_name=gen.get("Display Name", ""),
        datasheet=_build_datasheet_url(docs.get("Data Sheet, Technical Information")),
        img=_normalize_images(gen.get("Images")),
        m_poles=poles,
        m_no_contacts=int(_to_float(tech.get("Number of Main Contacts NO", "0"))),
        m_nc_contacts=int(_to_float(tech.get("Number of Main Contacts NC", "0"))),
        m_i_ac1=_parse_current_map(tech.get("Rated Operational Current AC-1 (I<sub>e</sub>)", [])),
        m_i_ac3=_parse_current_map(tech.get("Rated Operational Current AC-3 (I<sub>e</sub>)", [])),
        m_u_n=_parse_operational_voltage(tech.get("Rated Operational Voltage", "0")),
        m_u_insu=_parse_insulation_voltage(tech.get("Rated Insulation Voltage (U<sub>i</sub>)", "0")),
        m_u_imp=_parse_impulse_voltage(tech.get("Rated Impulse Withstand Voltage (U<sub>imp</sub>)", "0")),
        m_height_mm=_to_float(dims.get("Product Net Height", "0")),
        m_width_mm=_to_float(dims.get("Product Net Width", "0")),
        m_depth_mm=_to_float(dims.get("Product Net Depth / Length", "0")),
        m_weight_kg=_to_float(dims.get("Product Net Weight", "0")) or None,
    )


def map_abb_to_canonical_mcb(raw_dictionary: dict | None) -> CanonicalMCB | None:
    """Transforms raw parsed ABB product JSON into a CanonicalMCB instance."""
    if not raw_dictionary:
        return None

    attr_map = {}
    pvm = raw_dictionary.get("ProductViewModel", {})
    groups = pvm.get("Groups", []) if pvm else raw_dictionary.get("Groups", [])

    if not groups:
        for category, attrs in raw_dictionary.items():
            if isinstance(attrs, dict):
                for k, v in attrs.items():
                    clean_k = re.sub(r'<[^>]+>', '', k).strip()
                    attr_map[clean_k] = v
    else:
        for group in groups:
            for attr in group.get("Attributes", []):
                clean_name = re.sub(r'<[^>]+>', '', attr.get("Name", "")).strip()
                attr_map[clean_name] = attr.get("Value", "")

    def _extract_string(key: str) -> str:
        if key in attr_map:
            return str(attr_map[key])
        for k, v in attr_map.items():
            if key.lower() in k.lower():
                return str(v)
        return ""

    def _parse_mcb_capacity(val: str) -> dict[str, float]:
        caps = {}
        if not val: return caps
        matches = re.finditer(r"\((.*?)\)\s*([\d.,]+)\s*kA", val)
        found_specific_voltage = False
        generic_caps = {}
        
        for m in matches:
            voltage_str = m.group(1).strip()
            ka_val = float(m.group(2).replace(',', '.'))
            if any(char.isdigit() for char in voltage_str):
                caps[voltage_str] = ka_val
                found_specific_voltage = True
            else:
                generic_caps[f"Default {voltage_str}"] = ka_val
                
        if not found_specific_voltage and generic_caps:
            caps.update(generic_caps)
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

    display_name = raw_dictionary.get("DisplayName") or attr_map.get("Display Name", attr_map.get("Product ID", ""))
    sku = attr_map.get("Global ID", attr_map.get("Order Code", attr_map.get("Product ID", display_name)))
    
    # Unified Image Extraction Block
    image_source = pvm.get("Images") if pvm else attr_map.get("Images", [])
    image_urls = _normalize_images(image_source)

    doc_id = attr_map.get("Data Sheet, Technical Information") or attr_map.get("Product ID", sku)
    datasheet_url = _build_datasheet_url(doc_id)

    ics_str = _extract_string("Rated Service Short-Circuit Breaking Capacity")
    icn_str = _extract_string("Rated Short-Circuit Capacity")
    icu_str = _extract_string("Rated Ultimate Short-Circuit Breaking Capacity")

    ics_dict = _parse_mcb_capacity(ics_str) or _parse_mcb_capacity(icn_str)
    icu_dict = _parse_mcb_capacity(icu_str)

    weight_str = _extract_string("Product Net Weight")
    weight_kg = _to_float(weight_str)
    if weight_kg and "g" in weight_str.lower() and "kg" not in weight_str.lower():
        weight_kg /= 1000.0

    return CanonicalMCB(
        m_sku=sku,
        m_brand="ABB",
        m_name=display_name,
        m_poles=int(_to_float(_extract_string("Number of Poles"))),
        m_protected_poles=int(_to_float(_extract_string("Number of Protected Poles"))),
        m_i_n=_to_float(_extract_string("Rated Current (In)")),
        m_trip_class=_extract_string("Tripping Characteristic"),
        m_i_sc=ics_dict,
        m_i_cu=icu_dict,
        m_height_mm=_to_float(_extract_string("Product Net Height")),
        m_width_mm=_to_float(_extract_string("Product Net Width")),
        m_depth_mm=_to_float(_extract_string("Product Net Depth")),
        datasheet=datasheet_url,
        img=image_urls if image_urls else None,
        m_f_n=_parse_frequency(_extract_string("Rated Frequency (f)")),
        m_weight_kg=weight_kg if weight_kg else None
    )


def extract_voltage_range(raw_list: List[str]) -> Dict[str, Optional[str]]:
    if not raw_list:
        return {"minimum": None, "maximum": None}
    vals = re.findall(r'\d+', raw_list[0])
    return {
        "minimum": f"{vals[0]}V AC" if len(vals) > 0 else None,
        "maximum": f"{vals[1]}V AC" if len(vals) > 1 else None
    }


def _parse_voltage_string(v_str: str) -> Dict[str, Any]:
    pattern = r'(\d+)\s*[…\.]+\s*(\d+)\s*([a-zA-Z]+)'
    match = re.search(pattern, v_str)
    if match:
        return {
            "minimum": float(match.group(1)),
            "maximum": float(match.group(2)),
            "unit": match.group(3)
        }
    return {"minimum": None, "maximum": None, "unit": None}


def extract_operational_voltage(tech_info: Dict[str, Any]) -> Dict[str, Optional[str]]:
    raw_voltages = tech_info.get("Rated Voltage (U<sub>r</sub>)", [])
    if not raw_voltages:
        return {"minimum": None, "maximum": None}
    vals = re.findall(r'\d+', str(raw_voltages[0]))
    return {
        "minimum": f"{vals[0]}V" if len(vals) > 0 else None,
        "maximum": f"{vals[1]}V" if len(vals) > 1 else vals[0] + "V"
    }


def map_abb_to_canonical_motor_operator(raw_data: Dict[str, Any]) -> CanonicalMotorOperator:
    gen_info = raw_data.get("General Information", {})
    tech_info = raw_data.get("Technical", {})
    add_info = raw_data.get("Additional Information", {})
    certs = raw_data.get("Certificates and Declarations", {})
    
    return CanonicalMotorOperator(
        m_sku=gen_info.get("Global ID"),
        m_brand="ABB",
        m_name=gen_info.get("Display Name"),
        m_description=gen_info.get("Meta Description"),
        ean=raw_data.get("Classification", {}).get("Level 1 EAN"),
        m_u_n=extract_operational_voltage(tech_info),
        m_u_prot=tech_info.get("Impulse Withstand Voltage (U<sub>imp</sub>)"),
        datasheet=_build_datasheet_url(certs.get("Data Sheet, Technical Information")),
        m_u_ac_range=[_parse_voltage_string(v) for v in tech_info.get("Rated Voltage (U<sub>r</sub>)", []) if "AC" in v.upper()],
        m_u_dc_range=[_parse_voltage_string(v) for v in tech_info.get("Rated Voltage (U<sub>r</sub>)", []) if "DC" in v.upper()],
        m_current_type=tech_info.get("Current Type"),
        m_suitable_for=[add_info.get("Suitable For", "")],
        m_product_class=add_info.get("Suitable for Product Class"),
        m_config_type=tech_info.get("Configuration Type"),
        m_is_auto_reset="Auto-Reset" in gen_info.get("Display Name", ""),
        m_standards=tech_info.get("Standards", []),
        img=_normalize_images(gen_info.get("Images"))
    )


def map_abb_to_canonical_isolator(raw_data: Dict[str, Any]) -> CanonicalIsolator:
    gen_info = raw_data.get("General Information", {})
    dims = raw_data.get("Dimensions", {})
    elec = raw_data.get("Electrical", {})
    downloads = raw_data.get("Popular Downloads", {})
    
    short_name = gen_info.get("Short Name", "")
    poles_match = re.search(r'(\d+)P', short_name)
    current_match = re.search(r'(\d+)A', short_name)
    
    ops_volt = elec.get("Operational Voltage", [])
    operational_voltage = {
        "minimum": next((v.replace("Minimum ", "") for v in ops_volt if "Minimum" in v), None),
        "maximum": next((v.replace("Maximum ", "") for v in ops_volt if "Maximum" in v), None)
    }
    
    return CanonicalIsolator(
        m_sku=gen_info.get("Global ID"),
        m_brand="ABB",
        m_name=gen_info.get("Display Name"),
        m_i_n=float(current_match.group(1)) if current_match else None,
        m_poles=int(poles_match.group(1)) if poles_match else None,
        m_u_n=operational_voltage,
        m_u_prot=elec.get("Voltage Protection Level ( Up)"),
        datasheet=_build_datasheet_url(downloads.get("Data Sheet, Technical Information")),
        m_width_mm=_to_float(dims.get("Product Net Width")) or None,
        m_height_mm=_to_float(dims.get("Product Net Height")) or None,
        m_depth_mm=_to_float(dims.get("Product Net Depth / Length")) or None,
        m_modular_spacings=int(_to_float(dims.get("Width in Number of Modular Spacings", 0))),
        img=_normalize_images(gen_info.get("Images"))
    )


def map_abb_to_canonical_spreader(raw_data: Dict[str, Any]) -> CanonicalSpreader:
    gen_info = raw_data.get("General Information", {})
    add_info = raw_data.get("Additional Information", {})
    tech = raw_data.get("Technical", {})
    dims = raw_data.get("Dimensions", {})
    certs = raw_data.get("Certificates and Declarations", {})
    
    weight_str = dims.get("Product Net Weight") or dims.get("Package Level 1 Gross Weight")
    suitable = add_info.get("Suitable For", [])

    return CanonicalSpreader(
        m_sku=gen_info.get("Global ID"),
        m_brand="ABB",
        m_name=gen_info.get("Display Name"),
        m_description=gen_info.get("Meta Description"),
        datasheet=_build_datasheet_url(certs.get("Data Sheet, Technical Information")),
        m_weight_kg=_to_float(weight_str) or None,
        m_config_type=tech.get("Configuration Type"),
        m_poles=tech.get("Number of Poles"),
        m_order_multiple=tech.get("Order Multiple"),
        m_suitable_for=[suitable] if isinstance(suitable, str) else suitable,
        img=_normalize_images(gen_info.get("Images"))
    )