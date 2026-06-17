"""Represents a canonical spreader tag or bar"""
from dataclasses import asdict, dataclass, field
from typing import List, Optional

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class CanonicalSpreader:
    sku: str
    brand: str
    display_name: str
    description: str
    suitable_for: List[str]
    image_urls: List[str]
    categories: List[str] = field(default_factory=list)
    rated_current: Optional[str] = None
    number_of_poles: Optional[str] = None
    datasheet_url: Optional[str] = None
    weight_kg: Optional[float] = None
    configuration_type: Optional[str] = None
    order_multiple: Optional[int] = None
    
    def to_dict(self) -> dict:
        return asdict(self)