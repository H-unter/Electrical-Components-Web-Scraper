from dataclasses import dataclass, asdict, field
from typing import List, Optional

@dataclass
class CanonicalMCCB:
    """A unified data structure representing a Moulded Case Circuit Breaker."""
    m_sku: str  # Unique part identifier number
    m_brand: str  # Manufacturer (e.g., ABB, Hager)
    m_name: str  # Baseline product designation title
    datasheet: Optional[str]  # Direct link to technical product PDF asset
    img: Optional[list[str]]  # List of primary product images
    m_poles: int  # Pole count configuration (e.g., 3, 4)
    m_i_n: float  # Nominal current rating in Amperes (In)
    m_f_n: Optional[float | list[float]]  # Rated frequency or frequencies/ranges in hz
    m_u_imp: float  # Rated impulse withstand voltage in kV
    m_u_insu: float  # Rated insulation voltage in V
    m_u_n: float  # Rated operational voltage in V
    m_trip_type: str  # Trip unit classification (e.g., LSI, TMD, TM)
    m_i_sc: dict[str, float]  # Mapping of voltage levels to short-circuit breaking capacities (e.g., {"400VAC": 25.0, "415VAC": 25.0})
    m_i_cu: dict[str, float]  # Mapping of voltage levels to ultimate short-circuit breaking capacities (e.g., {"400VAC": 25.0, "415VAC": 25.0})
    m_height_mm: float  # Physical product structural height parameter
    m_width_mm: float  # Physical product structural width parameter
    m_depth_mm: float  # Physical product structural depth profile parameter
    m_weight_kg: Optional[float] = None  # Physical product mass in kilograms (if available)

    m_type: str = "mccb"
    
    # method to convert to dictionary
    def to_dict(self) -> dict:
        return asdict(self)