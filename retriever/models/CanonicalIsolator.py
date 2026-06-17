from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any

@dataclass
class CanonicalIsolator:
    """A unified data structure representing an Electrical Isolator."""
    sku: str
    brand: str
    display_name: str
    
    # Electrical Specs
    rated_current_a: Optional[float] = None
    number_of_poles: Optional[int] = None
    operational_voltage: Dict[str, Optional[str]] = field(default_factory=lambda: {"minimum": None, "maximum": None})
    voltage_protection_level: Optional[str] = None
    
    # Physical Dimensions
    width_mm: Optional[float] = None
    height_mm: Optional[float] = None
    depth_mm: Optional[float] = None
    modular_spacings: Optional[int] = None
    
    # Assets
    datasheet_url: Optional[str] = None
    image_urls: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return asdict(self)