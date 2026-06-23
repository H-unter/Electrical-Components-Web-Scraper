from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict

@dataclass
class CanonicalEnclosure:
    m_sku: str
    m_brand: str = "Rittal"
    m_name: Optional[str] = None

    # Dimensions (mm)
    m_width_mm: Optional[float] = None
    m_height_mm: Optional[float] = None
    m_depth_mm: Optional[float] = None

    # Specifications
    m_material: Optional[str] = None
    m_ip_rating: Optional[str] = None
    m_description: Optional[str] = None
    m_colour: Optional[str] = None
    m_surface_finish: Optional[Dict[str, str]] = field(default_factory=dict)
    m_supply_includes: List[str] = field(default_factory=list)
    
    # Material Thickness (mm)
    m_material_thickness_mm: Optional[Dict[str, float]] = field(default_factory=dict)
    
    # Mounting Plate
    m_mounting_plate_dimensions_mm: Optional[Dict[str, float]] = field(default_factory=dict)
    
    # Other
    m_door_count: Optional[int] = None
    m_weight_kg: Optional[float] = None

    m_type: str = "enclosure"

    def to_dict(self) -> dict|None:
        return asdict(self)