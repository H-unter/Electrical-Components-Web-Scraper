from dataclasses import dataclass, asdict, field
from typing import List, Optional

@dataclass
class CanonicalContactor:
    """A unified data structure representing a Contactor."""
    sku: str  # Unique part identifier number
    brand: str  # Manufacturer (e.g., ABB, Hager)
    display_name: str  # Baseline product designation title
    datasheet_url: Optional[str]  # Direct link to technical product PDF asset
    image_urls: Optional[list[str]]  # List of primary product images
    poles: int  # Pole count configuration (e.g., 3, 4)
    normally_open_contacts: int  # Number of normally open main contacts
    normally_closed_contacts: int  # Number of normally closed main contacts
    voltage_to_rated_ac1_current_a: dict[str, float]  # Mapping of voltage levels to nominal current ratings in Amperes (Ie)
    voltage_to_rated_ac3_current_a: dict[str, float]  # Mapping of voltage levels to nominal current ratings in Amperes (Ie)
    operational_voltage_v: int  # Rated operational voltage in V
    insulation_voltage_v: int  # Rated insulation voltage in V
    impulse_withstand_voltage_v: int  # Rated impulse withstand voltage in V

    height_mm: float  # Physical product structural height parameter
    width_mm: float  # Physical product structural width parameter
    depth_mm: float  # Physical product structural depth profile parameter
    weight_kg: Optional[float] = None  # Physical product mass in kilograms (if available)

    def to_dict(self) -> dict:
        return asdict(self)