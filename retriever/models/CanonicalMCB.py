from dataclasses import dataclass, asdict, field
from typing import List, Optional

@dataclass
class CanonicalMCB:
    """A unified data structure representing a Miniature Circuit Breaker."""
    m_sku: str  # Unique part identifier number
    m_brand: str  # Manufacturer (e.g., ABB, Hager)
    m_name: str  # Baseline product designation title
    m_poles: int  # Pole count configuration (e.g., 1, 2, 3, 4)
    m_protected_poles: int  # Number of poles that are protected
    m_i_n: float  # Nominal current rating in Amperes (In)
    m_trip_class: str  # Tripping characteristic classification (e.g., B, C, D)
    m_i_sc: dict[str, float]  # Mapping of voltages to Ics
    m_i_cu: dict[str, float]  # Mapping of voltages to Icu
    m_height_mm: float  # Physical product structural height parameter
    m_width_mm: float  # Physical product structural width parameter
    m_depth_mm: float  # Physical product structural depth profile parameter

    # --- OPTIONAL PARAMETERS (With Defaults, MUST be at bottom) ---
    datasheet: Optional[str] = None  # Direct link to technical product PDF asset
    img: Optional[list[str]] = None  # List of primary product images
    m_f_n: Optional[float | list[float]] = None  # Rated frequency or frequencies/ranges in hz
    m_weight_kg: Optional[float] = None  # Physical product mass in kilograms (if available)
    
    
    m_type: str = "mcb"

    def to_dict(self) -> dict:
        return asdict(self)