import re
from retriever.models.CanonicalEnclosure import CanonicalEnclosure

def _parse_dimensions(dim_string: str) -> dict:
    """Parses 'Width: 800 mm Height: 1,200 mm Depth: 300 mm'."""
    pattern = r"Width:\s*([\d,.]+)\s*mm\s*Height:\s*([\d,.]+)\s*mm\s*Depth:\s*([\d,.]+)\s*mm"
    match = re.search(pattern, dim_string)
    if match:
        return {
            "width": float(match.group(1).replace(",", "")),
            "height": float(match.group(2).replace(",", "")),
            "depth": float(match.group(3).replace(",", ""))
        }
    return {}

def _parse_thickness(value: str) -> float:
    """Parses '2 mm' to 2.0."""
    return float(value.replace(" mm", "").replace(",", ""))

def map_rittal_to_canonical_enclosure(raw_data: dict) -> CanonicalEnclosure:
    dims = _parse_dimensions(raw_data.get("Dimensions", ""))
    raw_supply = raw_data.get("Supply includes", "")
    pattern = r"(Enclosure.*?construction|Gland plate.*?base|Mounting plate|Lock:.*?bit|3-point lock system)"
    items = re.findall(pattern, raw_supply)
    if not items:
        items = [raw_supply.strip()]
    clean_supply = [item.strip() for item in items if item.strip()]
    # Extract mounting plate dimensions
    mp_dim_raw = raw_data.get("Dimensions mounting plate (W x H)", "")
    mp_dims = {}
    if "x" in mp_dim_raw:
        parts = mp_dim_raw.split("x")
        mp_dims = {
            "width": float(parts[0].replace(" mm", "").replace(",", "")),
            "height": float(parts[1].replace(" mm", "").replace(",", ""))
        }

    return CanonicalEnclosure(
        m_sku=raw_data.get("article_no", "").replace("AE ", ""),
        m_brand="Rittal",
        m_name=raw_data.get("title"),
        m_width_mm=dims.get("width"),
        m_height_mm=dims.get("height"),
        m_depth_mm=dims.get("depth"),
        m_material=raw_data.get("Basic material"),
        m_ip_rating=raw_data.get("Protection category to IEC 60 529"),
        m_description=raw_data.get("description"),
        m_colour=raw_data.get("Colour"),
        m_surface_finish={
            "description": raw_data.get("Surface finish") or ""
        },
        m_supply_includes=items,
        m_material_thickness_mm={
            "door": _parse_thickness(raw_data.get("Material thickness - door", "0")),
            "enclosure": _parse_thickness(raw_data.get("Material thickness - enclosure", "0")),
            "mounting_plate": _parse_thickness(raw_data.get("Material thickness of mounting plate", "0")),
        },
        m_mounting_plate_dimensions_mm=mp_dims,
        m_door_count=int(raw_data.get("Number of doors", 0)),
        m_weight_kg=float(raw_data.get("Gross weight", "0").replace(" kg", ""))
    )