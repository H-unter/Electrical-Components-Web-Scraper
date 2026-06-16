from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class CanonicalContactor:
    """A unified data structure representing a Contactor."""
    
    # --- REQUIRED PARAMETERS (Must be provided, no defaults) ---
    sku: str  
    brand: str  
    display_name: str  
    normally_open_contacts: int  
    normally_closed_contacts: int  
    voltage_to_rated_ac1_current_a: dict[str, float]  
    voltage_to_rated_ac3_current_a: dict[str, float]  
    operational_voltage_v: int  
    insulation_voltage_v: int  
    impulse_withstand_voltage_v: int  
    height_mm: float  
    width_mm: float  
    depth_mm: float  

    datasheet_url: Optional[str] = None  
    image_urls: Optional[list[str]] = None  
    poles: Optional[int] = None  
    rated_current_a: Optional[float] = None  # depending on the product, this is interchangable with the rated ac1. depends on how big the mccb is they report it differently.
    weight_kg: Optional[float] = None  

    def to_dict(self) -> dict:
        return asdict(self)