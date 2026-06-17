
# The registry: Keys are (brand_name, component_type)
from retriever.mappers.AbbMapper import *
from retriever.mappers.HagerMapper import *

_MAPPER_REGISTRY = {
   ("hager", "isolator"): map_hager_to_canonical_isolator,
   ("abb", "isolator"): map_abb_to_canonical_isolator,
   ("hager", "mcb"): map_hager_to_canonical_mcb,
   ("abb", "mcb"): map_abb_to_canonical_mcb,
   ("hager", "mccb"): map_hager_to_canonical_mccb,
   ("abb", "mccb"): map_abb_to_canonical_mccb,
   ("hager", "contactor"): map_hager_to_canonical_contactor,
   ("abb", "contactor"): map_abb_to_canonical_contactor,
   # ("hager", "motor_operator"): map_hager_to_canonical_motor_operator, # not implemented
   ("abb", "motor_operator"): map_abb_to_canonical_motor_operator,
   ("hager", "spreader"): map_hager_to_canonical_spreader,
   ("abb", "spreader"): map_abb_to_canonical_spreader,
}

def map_to(brand: str, component_type: str, raw_data: dict):
    """
    Unified entry point for all mappings.
    """
    key = (brand.lower(), component_type.lower())
    
    if key in _MAPPER_REGISTRY:
        return _MAPPER_REGISTRY[key](raw_data)
    
    # Error handling with introspection
    implemented = [f"{b} -> {t}" for b, t in _MAPPER_REGISTRY.keys()]
    raise NotImplementedError(
        f"Mapping not implemented for '{brand}' as '{component_type}'. "
        f"Implemented mappings: {', '.join(implemented)}"
    )