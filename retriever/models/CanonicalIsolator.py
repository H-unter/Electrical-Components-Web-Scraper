from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any

@dataclass
class CanonicalIsolator:
    """A unified data structure representing an Electrical Isolator."""
    m_sku: str
    m_brand: str
    m_name: str
    
    # Electrical Specs
    m_i_n: Optional[float] = None
    m_poles: Optional[int] = None
    m_u_n: Dict[str, Optional[str]] = field(default_factory=lambda: {"minimum": None, "maximum": None})
    m_u_prot: Optional[str] = None
    
    # Physical Dimensions
    m_width_mm: Optional[float] = None
    m_height_mm: Optional[float] = None
    m_depth_mm: Optional[float] = None
    m_modular_spacings: Optional[int] = None
    
    # Assets
    datasheet: Optional[str] = None
    img: List[str] = field(default_factory=list)

    m_type: str = "isolator"
    
    def to_dict(self) -> dict:
        return asdict(self)