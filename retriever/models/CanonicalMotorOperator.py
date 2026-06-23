from dataclasses import dataclass, asdict, field
from typing import Any, List, Dict, Optional

@dataclass
class CanonicalMotorOperator:
    """A unified data structure representing a Motor Operator."""
    m_sku: str
    m_brand: str
    m_name: str
    m_description: Optional[str] = None
    ean: Optional[str] = None # TODO: remove
    
    m_u_ac_range: List[Dict[str, Any]] = field(default_factory=list) 
    m_u_dc_range: List[Dict[str, Any]] = field(default_factory=list)
    m_u_n: Dict[str, Optional[str]] = field(default_factory=lambda: {"minimum": None, "maximum": None})
    m_u_prot: Optional[str] = None
    datasheet: Optional[str] = None
    m_current_type: Optional[str] = None
    m_suitable_for: List[str] = field(default_factory=list)
    m_product_class: Optional[str] = None
    m_config_type: Optional[str] = None
    m_is_auto_reset: bool = False
    m_standards: List[str] = field(default_factory=list)
    m_etim_class: Optional[str] = None
    img: List[str] = field(default_factory=list)
    m_document_urls: List[str] = field(default_factory=list)

    m_type: str = "motor_operator"

    def to_dict(self) -> dict:
        return asdict(self)