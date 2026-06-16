from dataclasses import dataclass, asdict, field
from typing import List, Optional

@dataclass
class CanonicalMCB:
    """A unified data structure representing a Miniature Circuit Breaker."""
    sku: str  # Unique part identifier number
    brand: str  # Manufacturer (e.g., ABB, Hager)
    display_name: str  # Baseline product designation title
    poles: int  # Pole count configuration (e.g., 1, 2, 3, 4)
    protected_poles: int  # Number of poles that are protected
    rated_current_a: float  # Nominal current rating in Amperes (In)
    tripping_characteristic: str  # Tripping characteristic classification (e.g., B, C, D)
    voltage_to_service_short_circuit_breaking_capacity_ka: dict[str, float]  # Mapping of voltages to Ics
    voltage_to_ultimate_short_circuit_breaking_capacity_ka: dict[str, float]  # Mapping of voltages to Icu
    height_mm: float  # Physical product structural height parameter
    width_mm: float  # Physical product structural width parameter
    depth_mm: float  # Physical product structural depth profile parameter

    # --- OPTIONAL PARAMETERS (With Defaults, MUST be at bottom) ---
    datasheet_url: Optional[str] = None  # Direct link to technical product PDF asset
    image_urls: Optional[list[str]] = None  # List of primary product images
    rated_frequency_hz: Optional[float | list[float]] = None  # Rated frequency or frequencies/ranges in hz
    weight_kg: Optional[float] = None  # Physical product mass in kilograms (if available)

    def to_dict(self) -> dict:
        return asdict(self)