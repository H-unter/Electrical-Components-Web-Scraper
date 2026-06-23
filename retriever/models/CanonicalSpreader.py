"""Represents a canonical spreader tag or bar"""
from dataclasses import asdict, dataclass, field
from typing import List, Optional

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class CanonicalSpreader:
    m_sku: str
    m_brand: str
    m_name: str
    m_description: str
    m_suitable_for: List[str]
    img: List[str]
    m_categories: List[str] = field(default_factory=list)
    m_i_n: Optional[str] = None
    m_poles: Optional[str] = None
    datasheet: Optional[str] = None
    m_weight_kg: Optional[float] = None
    m_config_type: Optional[str] = None
    m_order_multiple: Optional[int] = None

    m_type: str = "spreader"
    
    def to_dict(self) -> dict:
        return asdict(self)