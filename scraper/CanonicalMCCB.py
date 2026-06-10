from dataclasses import dataclass, asdict, field
from typing import List, Optional

@dataclass
class CanonicalMCCB:
    """A unified data structure representing a Moulded Case Circuit Breaker."""
    sku: str  # Unique part identifier number
    brand: str  # Manufacturer (e.g., ABB, Hager)
    display_name: str  # Baseline product designation title
    datasheet_url: Optional[str]  # Direct link to technical product PDF asset
    image_urls: Optional[list[str]]  # List of primary product images
    poles: int  # Pole count configuration (e.g., 3, 4)
    rated_current_a: float  # Nominal current rating in Amperes (In)
    rated_frequency_hz: Optional[float | list[float]]  # Rated frequency or frequencies/ranges in hz
    u_imp: float  # Rated impulse withstand voltage in kV
    u_insulation: float  # Rated insulation voltage in V
    u_operational: float  # Rated operational voltage in V
    trip_type: str  # Trip unit classification (e.g., LSI, TMD, TM)
    voltage_to_short_circuit_breaking_capacity_ka: dict[str, float]  # Mapping of voltage levels to short-circuit breaking capacities (e.g., {"400VAC": 25.0, "415VAC": 25.0})
    voltage_to_ultimate_short_circuit_breaking_capacity_ka: dict[str, float]  # Mapping of voltage levels to ultimate short-circuit breaking capacities (e.g., {"400VAC": 25.0, "415VAC": 25.0})
    height_mm: float  # Physical product structural height parameter
    width_mm: float  # Physical product structural width parameter
    depth_mm: float  # Physical product structural depth profile parameter
    weight_kg: Optional[float] = None  # Physical product mass in kilograms (if available)
    # method to convert to dictionary
    def to_dict(self) -> dict:
        return asdict(self)
