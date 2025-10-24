"""Service to load and manage heat pump models from JSON data files."""

import json
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class HeatPumpModelsService:
    """Service to load and manage heat pump models from bundled JSON data."""

    def __init__(self):
        self._models = None
        self._models_by_brand = None
        self._load_models()

    def _load_models(self):
        """Load heat pump models from bundled JSON file."""
        try:
            # Path: services -> heatpump_mcp_server -> data
            data_file = Path(__file__).parent.parent / "data" / "hpmodels.json"

            logger.info(f"Loading heat pump models from: {data_file}")

            if not data_file.exists():
                logger.warning(f"Heat pump models file not found: {data_file}")
                self._use_fallback_models()
                return

            with open(data_file, "r") as f:
                data = json.load(f)

            self._process_models_data(data)
            logger.info(f"✅ Loaded {len(self._models)} heat pump models from bundled data")

        except Exception as e:
            logger.error(f"❌ Failed to load heat pump models: {e}")
            self._use_fallback_models()

    def _process_models_data(self, data: Dict):
        """Process raw models data into internal format."""
        # Extract models from the research data
        raw_models = data.get("new_models", [])
        logger.info(f"Found {len(raw_models)} raw models in JSON")

        # Convert to our standard format
        self._models = []
        for i, model in enumerate(raw_models):
            try:
                self._models.append(
                    {
                        "brand": model["brand"],
                        "model": model["model"],
                        "btu_capacity": model["btu_capacity"],
                        "hspf2": model["hspf2"],
                        "price_range": model["price_range"],
                    }
                )
            except KeyError as e:
                logger.error(f"Missing key in model {i}: {e}")

        # Group by brand
        self._group_models_by_brand()

    def _use_fallback_models(self):
        """Use a minimal set of fallback models if JSON loading fails."""
        logger.info("Using fallback heat pump models")
        self._models = [
            {
                "brand": "Mitsubishi",
                "model": "MXZ-2C20NAHZ",
                "btu_capacity": 20000,
                "hspf2": 12.0,
                "price_range": "$2,800-$3,800",
            },
            {
                "brand": "Mitsubishi",
                "model": "MXZ-3C24NA",
                "btu_capacity": 24000,
                "hspf2": 11.5,
                "price_range": "$3,000-$4,000",
            },
            {
                "brand": "Mitsubishi",
                "model": "MXZ-3C30NA",
                "btu_capacity": 30000,
                "hspf2": 11.0,
                "price_range": "$3,500-$4,500",
            },
            {
                "brand": "Daikin",
                "model": "2MXS18NMVJU",
                "btu_capacity": 18000,
                "hspf2": 11.0,
                "price_range": "$2,500-$3,500",
            },
            {
                "brand": "Daikin",
                "model": "3MXS24NMVJU",
                "btu_capacity": 24000,
                "hspf2": 10.5,
                "price_range": "$3,000-$4,000",
            },
            {
                "brand": "Fujitsu",
                "model": "AOU18RLXFZ",
                "btu_capacity": 18000,
                "hspf2": 12.5,
                "price_range": "$2,800-$3,800",
            },
            {
                "brand": "Fujitsu",
                "model": "AOU24RLXFZ",
                "btu_capacity": 24000,
                "hspf2": 12.0,
                "price_range": "$3,200-$4,200",
            },
            {
                "brand": "LG",
                "model": "LMU180HHV",
                "btu_capacity": 18000,
                "hspf2": 10.5,
                "price_range": "$2,400-$3,400",
            },
            {
                "brand": "Samsung",
                "model": "AM018JNMDEH",
                "btu_capacity": 18000,
                "hspf2": 11.2,
                "price_range": "$2,600-$3,600",
            },
            {
                "brand": "Carrier",
                "model": "25HPA524A003",
                "btu_capacity": 24000,
                "hspf2": 10.0,
                "price_range": "$3,500-$4,500",
            },
        ]
        self._group_models_by_brand()

    def _group_models_by_brand(self):
        """Group models by brand for easy access."""
        self._models_by_brand = {}
        for model in self._models:
            brand = model["brand"]
            if brand not in self._models_by_brand:
                self._models_by_brand[brand] = []
            self._models_by_brand[brand].append(model)

        # Sort models within each brand by BTU capacity
        for brand in self._models_by_brand:
            self._models_by_brand[brand].sort(key=lambda x: x["btu_capacity"])

    def get_all_models(self) -> List[Dict]:
        """Get all heat pump models."""
        return self._models.copy()

    def get_models_by_brand(self) -> Dict[str, List[Dict]]:
        """Get models grouped by brand."""
        return self._models_by_brand.copy()

    def get_brands(self) -> List[str]:
        """Get list of all available brands."""
        return sorted(self._models_by_brand.keys())

    def get_models_for_brand(self, brand: str) -> List[Dict]:
        """Get all models for a specific brand."""
        return self._models_by_brand.get(brand, []).copy()

    def find_model(self, brand: str, model: str) -> Optional[Dict]:
        """Find a specific model by brand and model name."""
        for m in self._models:
            if m["brand"].lower() == brand.lower() and m["model"].lower() == model.lower():
                return m.copy()
        return None

    def find_model_by_combined_name(self, combined_name: str) -> Optional[Dict]:
        """Find a model by combined name like 'Mitsubishi MXZ-3C24NA'."""
        parts = combined_name.strip().split(" ", 1)
        if len(parts) >= 2:
            brand = parts[0]
            model = parts[1]
            return self.find_model(brand, model)
        return None

    def get_recommended_models(self, target_btu: int, count: int = 3) -> List[Dict]:
        """Get recommended models near the target BTU capacity."""
        # Sort all models by how close they are to target BTU
        sorted_models = sorted(self._models, key=lambda x: abs(x["btu_capacity"] - target_btu))

        # Return top matches
        return [m.copy() for m in sorted_models[:count]]

    def reload_models(self):
        """Reload models from JSON file (useful for development/testing)."""
        self._load_models()


# Singleton instance
heat_pump_models_service = HeatPumpModelsService()
