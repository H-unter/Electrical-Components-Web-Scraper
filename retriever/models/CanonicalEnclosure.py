from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict

@dataclass
class CanonicalEnclosure:
    sku: str
    brand: str = "Rittal"
    display_name: Optional[str] = None

    # Dimensions (mm)
    width_mm: Optional[float] = None
    height_mm: Optional[float] = None
    depth_mm: Optional[float] = None

    # Specifications
    material: Optional[str] = None
    ip_rating: Optional[str] = None
    description: Optional[str] = None
    colour: Optional[str] = None
    surface_finish: Optional[Dict[str, str]] = field(default_factory=dict)
    supply_includes: List[str] = field(default_factory=list)
    
    # Material Thickness (mm)
    material_thickness_mm: Optional[Dict[str, float]] = field(default_factory=dict)
    
    # Mounting Plate
    mounting_plate_dimensions_mm: Optional[Dict[str, float]] = field(default_factory=dict)
    
    # Other
    number_of_doors: Optional[int] = None
    weight_kg: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)