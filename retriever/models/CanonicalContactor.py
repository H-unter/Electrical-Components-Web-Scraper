from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class CanonicalContactor:
    """A unified data structure representing a Contactor."""    
    m_sku: str  
    m_brand: str  
    m_display_name: str  
    m_no_contacts: int  # number of normally open contacts
    m_nc_contacts: int  # number of normally closed contacts
    m_i_ac1: dict[str, float]  
    m_i_ac3: dict[str, float]  
    m_u_n: int  
    m_u_insu: int  
    m_u_imp: int  
    m_height_mm: float  
    m_width_mm: float  
    m_depth_mm: float  

    datasheet: Optional[str] = None  
    img: Optional[list[str]] = None  
    m_poles: Optional[int] = None  
    m_i_n: Optional[float] = None  # depending on the product, this is interchangable with the rated ac1. depends on how big the mccb is they report it differently.
    m_weight_kg: Optional[float] = None  

    m_type: str = "contactor"

    def to_dict(self) -> dict:
        return asdict(self)