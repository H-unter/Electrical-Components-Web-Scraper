from dataclasses import dataclass, asdict, field
from typing import Any, List, Dict, Optional

@dataclass
class CanonicalMotorOperator:
    """A unified data structure representing a Motor Operator."""
    sku: str
    brand: str
    display_name: str
    description: Optional[str] = None
    ean: Optional[str] = None
    
    # Updated: Stores structured voltage data
    voltage_range_ac: List[Dict[str, Any]] = field(default_factory=list) 
    voltage_range_dc: List[Dict[str, Any]] = field(default_factory=list)
    
    current_type: Optional[str] = None
    suitable_for_breakers: List[str] = field(default_factory=list)
    product_class: Optional[str] = None
    configuration_type: Optional[str] = None
    is_auto_reset: bool = False
    standards: List[str] = field(default_factory=list)
    etim_class: Optional[str] = None
    image_urls: List[str] = field(default_factory=list)
    document_urls: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)