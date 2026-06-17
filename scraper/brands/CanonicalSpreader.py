"""Represents a canonical spreader tag or bar"""
from dataclasses import asdict, dataclass, field
from typing import List, Optional

@dataclass
class CanonicalSpreader:
    """A unified data structure representing a Spreader Bar or a Spreader Terminal."""
    sku: str
    brand: str
    display_name: str
    description: Optional[str] = None
    datasheet_url: Optional[str] = None
    
    # New Fields
    weight_kg: Optional[float] = None
    configuration_type: Optional[str] = None
    number_of_poles: Optional[str] = None
    order_multiple: Optional[str] = None
    
    suitable_for: List[str] = field(default_factory=list)
    image_urls: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)