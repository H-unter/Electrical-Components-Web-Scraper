

from retriever.models.CanonicalMCCB import CanonicalMCCB
from retriever.models.CanonicalMCB import CanonicalMCB
from retriever.models.CanonicalContactor import CanonicalContactor
from retriever.models.CanonicalIsolator import CanonicalIsolator
from retriever.models.CanonicalSpreader import CanonicalSpreader

import re
from typing import Optional, Dict, Any



def map_hager_to_canonical_mccb(raw_dictionary: dict|None) -> CanonicalMCCB|None:
    """Transforms raw parsed Hager dictionary structures into a CanonicalMCCB instance."""
    if not raw_dictionary: return None  # Fast escape if raw data extraction was unsuccessful

    general_info = raw_dictionary.get("General Information", {})  # Target general metadata blocks
    electric_current = raw_dictionary.get("Electric current", {})  # Target power performance attributes
    dimensions = raw_dictionary.get("Dimensions", {})  # Target layout sizing measurements
    documents = raw_dictionary.get("Documents", {})  # Extract the nested documents block safely

    def _num(value) -> float:
        string_value = value[0] if isinstance(value, list) and value else value  # Clean array layers down to string
        return float(re.sub(r"[^\d.]", "", str(string_value).replace(",", "."))) if string_value else 0.0  # Safe float cast

    short_circuit_breaking_capacity = {}  # Allocate mapping block for service capacities
    ultimate_short_circuit_breaking_capacity = {}  # Allocate mapping block for ultimate capacities
    for key, value in electric_current.items():
        string_value = value[0] if isinstance(value, list) and value else value  # Normalize lists down to single string element
        cleaned_value = float(str(string_value).split()[0].replace(",", ".")) if string_value else 0.0  # Snatch leading float digits
        if "Ics under" in key:  # Check pattern matches service criteria
            match = re.search(r"under\s+(\d+\s*V\s*AC)", key)  # Isolate specific voltage string token
            if match: short_circuit_breaking_capacity[match.group(1).replace(" ", "")] = cleaned_value  # Map voltage pair cleanly
        elif "Icu under" in key:  # Check pattern matches ultimate criteria
            match = re.search(r"under\s+(\d+\s*V\s*AC)", key)  # Isolate specific voltage string token
            if match: ultimate_short_circuit_breaking_capacity[match.group(1).replace(" ", "")] = cleaned_value  # Map voltage pair cleanly

    operational_voltage_string = raw_dictionary.get("Voltage", {}).get("Rated operational voltage Ue", "0")  # Extract baseline bounds
    operational_voltage_clean = operational_voltage_string[0] if isinstance(operational_voltage_string, list) and operational_voltage_string else operational_voltage_string  # Extract list item string safely
    operational_voltage = _num(str(operational_voltage_clean).split("-")[-1]) if "-" in str(operational_voltage_clean) else _num(operational_voltage_clean)  # Snatch the maximum range bound

    frequency_string = str(raw_dictionary.get("Frequency", {}).get("Frequency", "50 - 60 Hz"))  # Safe string conversion cast
    rated_frequency_hz = [float(extracted_number) for extracted_number in re.findall(r"\d+", frequency_string)] if "-" in frequency_string else _num(frequency_string)  # Capture frequency spans

    datasheet_list = []  # Initialize core file document stack array
    if isinstance(documents, dict): datasheet_list = documents.get("Product datasheet", []) or documents.get("Datasheet", [])  # Retrieve from direct subcategory keys
    if not datasheet_list and isinstance(documents, dict):  # Fallback: scan through inner document categories
        for key, value in documents.items():  # Loop keys looking for structural matches
            if "datasheet" in key.lower() and isinstance(value, list):  # If name fits structure
                datasheet_list = value  # Set target array layout
                break  # Exit traversal loop
    if not datasheet_list:  # Fallback: scan root keys directly
        for key, value in raw_dictionary.items():  # Traverse root dictionary structure
            if "datasheet" in key.lower() and isinstance(value, list):  # Check key pattern match criteria
                datasheet_list = value  # Set target array layout
                break  # Exit traversal loop
    datasheet_url = datasheet_list[0].get("url") if isinstance(datasheet_list, list) and datasheet_list else None  # Grab first available PDF asset link

    image_urls = []  # Allocate target listing placeholder array structure
    images_raw_value = general_info.get("Images", "")  # Pull general image asset strings
    if images_raw_value: image_urls = images_raw_value if isinstance(images_raw_value, list) else [images_raw_value]  # Push element natively or convert to single entry list
    if not image_urls and isinstance(documents, dict) and "Product image" in documents:  # Fallback to secondary asset gallery arrays
        product_images_documents = documents.get("Product image", [])  # Gather document lists
        if isinstance(product_images_documents, list): image_urls = [item.get("url") for item in product_images_documents if item.get("url")]  # Compile image URLs cleanly

    raw_impulse_voltage = _num(raw_dictionary.get("Voltage", {}).get("Rated impulse withstand voltage Uimp", "0"))  # Pull raw parameter metric
    u_imp = raw_impulse_voltage / 1000.0 if raw_impulse_voltage > 100.0 else raw_impulse_voltage  # Standardize thousands value string boundary directly down to kV scale units

    return CanonicalMCCB(
        m_sku=general_info.get("SKU", ""),
        m_brand="Hager",
        m_name=general_info.get("Display Name", ""),
        m_poles=int(str(raw_dictionary.get("Architecture", {}).get("Number of poles", "3"))),
        m_i_n=_num(electric_current.get("Rated current", "0")),
        m_f_n=rated_frequency_hz,
        m_u_imp=u_imp,
        m_u_insu=_num(raw_dictionary.get("Voltage", {}).get("Rated insulation voltage Ui", "0")),
        m_u_n=operational_voltage,
        m_trip_type=raw_dictionary.get("Functions", {}).get("Trip unit", "TM"),
        m_i_sc=short_circuit_breaking_capacity,
        m_i_cu=ultimate_short_circuit_breaking_capacity,
        m_height_mm=_num(dimensions.get("Height", "0")),
        m_width_mm=_num(dimensions.get("Width", "0")),
        m_depth_mm=_num(dimensions.get("Depth", "0")),
        m_weight_kg=None,
        datasheet=datasheet_url,
        img=image_urls
    )

def map_hager_to_canonical_contactor(raw_dictionary: dict | None) -> CanonicalContactor | None:
    """Transforms raw parsed Hager contactor dictionary structures into a CanonicalContactor instance."""
    if not raw_dictionary:
        return None

    general_info = raw_dictionary.get("General Information", {})
    electric_current = raw_dictionary.get("Electric current", {})
    voltage = raw_dictionary.get("Voltage", {})
    dimensions = raw_dictionary.get("Dimensions", {})
    equipment = raw_dictionary.get("Equipment", {})
    connection = raw_dictionary.get("Connection", {})
    architecture = raw_dictionary.get("Architecture", {})
    documents = raw_dictionary.get("Documents", {})

    # --- Helpers ---
    def _extract_string(value) -> str:
        return str(value[0] if isinstance(value, list) and value else value)

    def _num(value) -> float:
        string_value = _extract_string(value)
        if not string_value or string_value.lower() == 'none':
            return 0.0
        cleaned = re.sub(r"[^\d.]", "", string_value.replace(",", "."))
        return float(cleaned) if cleaned else 0.0

    def _int(value) -> int:
        string_value = _extract_string(value)
        match = re.search(r"(\d+)", string_value)
        return int(match.group(1)) if match else 0

    # --- Contacts Processing ---
    no_contacts = _int(equipment.get("Number of NO contacts", "0"))
    nc_contacts = _int(equipment.get("Number of NC contacts", "0"))

    if no_contacts == 0 and nc_contacts == 0:
        contact_type = _extract_string(connection.get("Type of contacts", ""))
        no_match = re.search(r"(\d+)\s*NO", contact_type)
        nc_match = re.search(r"(\d+)\s*NC", contact_type)
        if no_match: no_contacts = int(no_match.group(1))
        if nc_match: nc_contacts = int(nc_match.group(1))

    # --- Poles Processing (Strict Read) ---
    poles_str = _extract_string(architecture.get("Number of poles", ""))
    poles = _int(poles_str) if poles_str else None

    # --- Voltages Processing ---
    ue_str = _extract_string(voltage.get("Rated operational voltage Ue", "0"))
    ue_matches = re.findall(r"(\d+)", ue_str)
    operational_voltage = int(ue_matches[-1]) if ue_matches else 0

    insulation_voltage = _int(voltage.get("Rated insulation voltage Ui", "0"))
    impulse_withstand_voltage = _int(voltage.get("Rated impulse withstand voltage Uimp", "0"))

    # --- Current Processing ---
    rated_current = _num(electric_current.get("Rated current", "0"))
    
    ac1_currents = {}
    if operational_voltage > 0 and rated_current > 0:
        ac1_currents[f"{operational_voltage}V"] = rated_current

    # --- Documents & Images ---
    datasheet_list = documents.get("Product datasheet", []) or documents.get("Product data sheet", [])
    datasheet_url = datasheet_list[0].get("url") if isinstance(datasheet_list, list) and datasheet_list else None

    images_raw_value = general_info.get("Images", "")
    if images_raw_value:
        image_urls = images_raw_value if isinstance(images_raw_value, list) else [images_raw_value]
    else:
        product_images_documents = documents.get("Product image", [])
        image_urls = [item.get("url") for item in product_images_documents if isinstance(item, dict) and item.get("url")]

    return CanonicalContactor(
        m_sku=general_info.get("SKU", general_info.get("Display Name", "")),
        m_brand="Hager",
        m_display_name=general_info.get("Display Name", ""),
        datasheet=datasheet_url,
        img=image_urls,
        m_poles=poles,
        m_no_contacts=no_contacts,
        m_nc_contacts=nc_contacts,
        m_i_n=rated_current if rated_current > 0 else None,
        m_i_ac1=ac1_currents,
        m_i_ac3={},
        m_u_n=operational_voltage,
        m_u_insu=insulation_voltage,
        m_u_imp=impulse_withstand_voltage,
        m_height_mm=_num(dimensions.get("Height", "0")),
        m_width_mm=_num(dimensions.get("Width", "0")),
        m_depth_mm=_num(dimensions.get("Depth", "0")),
        m_weight_kg=None
    )

def map_hager_to_canonical_mcb(raw_dictionary: dict | None) -> CanonicalMCB | None:
    """Transforms raw parsed Hager MCB dictionary structures into a CanonicalMCB instance."""
    if not raw_dictionary:
        return None

    general_info = raw_dictionary.get("General Information", {})
    electric_current = raw_dictionary.get("Electric current", {})
    architecture = raw_dictionary.get("Architecture", {})
    main_elec = raw_dictionary.get("Main electrical attributes", {})
    dimensions = raw_dictionary.get("Dimensions", {})
    frequency = raw_dictionary.get("Frequency", {})
    documents = raw_dictionary.get("Documents", {})

    # --- Helpers ---
    def _extract_string(value) -> str:
        return str(value[0] if isinstance(value, list) and value else value)

    def _num(value) -> float:
        string_value = _extract_string(value)
        if not string_value or string_value.lower() == 'none':
            return 0.0
        # Replace European commas with dots and strip non-numerics
        cleaned = re.sub(r"[^\d.,]", "", string_value.replace(",", "."))
        try:
            match = re.search(r"([\d.]+)", cleaned)
            return float(match.group(1)) if match else 0.0
        except ValueError:
            return 0.0

    def _int(value) -> int:
        string_value = _extract_string(value)
        match = re.search(r"(\d+)", string_value)
        return int(match.group(1)) if match else 0

    def _parse_capacity(target_type: str) -> dict[str, float]:
        """
        Searches keys for 'Icn' or 'Icu' and dynamically extracts 
        the voltage rating from the key string (e.g., 'under 400 V AC').
        """
        caps = {}
        # Hager distributes these capacities across two different dictionaries
        sources = {**main_elec, **electric_current}
        
        for key, value in sources.items():
            if target_type.lower() in key.lower():
                ka_val = _num(value)
                if ka_val > 0:
                    # Extract the voltage mentioned in the text key
                    volt_match = re.search(r"(\d+\s*V\s*(?:AC|DC)?)", key, re.IGNORECASE)
                    if volt_match:
                        # Clean up formatting, e.g., "400 V AC"
                        caps[volt_match.group(1).upper()] = ka_val
                    else:
                        caps["Default"] = ka_val
        return caps

    def _parse_frequency(val: str) -> Optional[float | list[float]]:
        if not val: return None
        string_value = _extract_string(val)
        matches = re.findall(r"(\d+)", string_value)
        if not matches: return None
        floats = [float(m) for m in matches]
        return floats[0] if len(floats) == 1 else floats

    # --- Core Properties ---
    display_name = general_info.get("Display Name", "")
    sku = general_info.get("SKU", display_name)
    
    poles_str = _extract_string(architecture.get("Type of pole", ""))
    poles = _int(poles_str)
    
    # Infer protected poles: Assume all are protected unless a neutral is specified
    protected_poles = poles if poles > 0 else 0
    if "N" in poles_str.upper() and poles > 1:
        protected_poles = poles - 1

    rated_current = _num(electric_current.get("Rated current", "0"))
    tripping_characteristic = _extract_string(architecture.get("Curve", ""))

    # --- Capacities ---
    # Since Hager lacks explicit Ics, we parse Icn to use as our service fallback
    icn_dict = _parse_capacity("Icn")
    icu_dict = _parse_capacity("Icu")

    # --- Dimensions ---
    height = _num(dimensions.get("Height", "0"))
    width = _num(dimensions.get("Width", "0"))
    depth = _num(dimensions.get("Depth", "0"))

    # --- Frequency ---
    freq_str = _extract_string(frequency.get("Frequency", ""))
    rated_frequency = _parse_frequency(freq_str)

    # --- Documents & Images ---
    datasheet_list = documents.get("Product datasheet", []) or documents.get("Product data sheet", [])
    datasheet_url = datasheet_list[0].get("url") if isinstance(datasheet_list, list) and datasheet_list else None

    images_raw = general_info.get("Images", "")
    image_urls = []
    if images_raw:
        image_urls = images_raw if isinstance(images_raw, list) else [images_raw]
    else:
        product_images_documents = documents.get("Product image", [])
        image_urls = [item.get("url") for item in product_images_documents if isinstance(item, dict) and item.get("url")]

    return CanonicalMCB(
        m_sku=sku,
        m_brand="Hager",
        m_name=display_name,
        m_poles=poles,
        m_protected_poles=protected_poles,
        m_i_n=rated_current,
        m_trip_class=tripping_characteristic,
        m_i_sc=icn_dict,
        m_i_cu=icu_dict,
        m_height_mm=height,
        m_width_mm=width,
        m_depth_mm=depth,
        datasheet=datasheet_url,
        img=image_urls if image_urls else None,
        m_f_n=rated_frequency,
        m_weight_kg=None
    )


def map_hager_to_canonical_isolator(raw_data: Dict[str, Any]) -> CanonicalIsolator:
    """
    Maps Hager Isolator raw JSON to a CanonicalIsolator object.
    """
    gen_info = raw_data.get("General Information", {})
    arch = raw_data.get("Architecture", {})
    elec = raw_data.get("Electric current", {})
    volt = raw_data.get("Voltage", {})
    dims = raw_data.get("Dimensions", {})

    # Helper to clean and parse numeric values from strings like "80 A" or "17,50 mm"
    def parse_float(val: Any) -> Optional[float]:
        if not val: return None
        # Replace comma with dot for European/Hager format, then find number
        clean_val = str(val).replace(',', '.')
        match = re.search(r'\d+(\.\d+)?', clean_val)
        return float(match.group()) if match else None

    return CanonicalIsolator(
        m_sku=gen_info.get("SKU"),
        m_brand="Hager",
        m_name=gen_info.get("Display Name"),
        m_i_n=parse_float(elec.get("Rated current")),
        m_poles=int(arch.get("Number of poles", 0)),
        # Mapping Hager's "Rated operational voltage Ue" to canonical structure
        m_u_n={
            "minimum": volt.get("Rated operational voltage Ue", "N/A").split("-")[0].strip(),
            "maximum": volt.get("Rated operational voltage Ue", "N/A").split("-")[-1].strip()
        },
        m_u_prot=None, # Hager structure differs; check "Rated insulation voltage Ui"
        datasheet=gen_info.get("Product URL"),
        m_width_mm=parse_float(dims.get("Width")),
        m_height_mm=parse_float(dims.get("Height")),
        m_depth_mm=parse_float(dims.get("Depth")),
        img=[gen_info.get("Images")] if gen_info.get("Images") else []
    )


def get_compatible_skus(self, modal_soup):
    """
    Extracts all compatible SKUs from the 'Suitable with' modal.
    """
    # Locates all spans with the specific class and pulls the text
    compatible_skus = [
        item.get_text(strip=True) 
        for item in modal_soup.select(".product-list__name")
    ]
    return compatible_skus

def map_hager_to_canonical_spreader(raw_dictionary: dict) -> CanonicalSpreader:
    """
    Transforms Hager raw data into a CanonicalSpreader instance.
    """
    gen = raw_dictionary.get("General Information", {})
    elec = raw_dictionary.get("Electric current", {})
    arch = raw_dictionary.get("Architecture", {})

    return CanonicalSpreader(
        m_sku=gen.get("SKU"),
        m_brand="Hager",
        m_name=gen.get("Display Name"),
        m_description=gen.get("Description"),
        # Added new fields
        m_categories=[gen.get("Category 1"), gen.get("Category 2"), gen.get("Category 3")],
        m_i_n=elec.get("Rated current"),
        m_poles=arch.get("Type of pole"), # "3P"
        # Existing fields
        m_suitable_for=raw_dictionary.get("Compatible Products", []),
        img=[gen.get("Images")] if gen.get("Images") else [],
        datasheet=None, # Update if scraping logic is added
        m_weight_kg=None,
        m_config_type=None,
        m_order_multiple=None
    )