from typing import Dict, Any, Tuple
from app.schemas.analysis import LeafImageStats


class ValidationService:
    def verify_crop_subject(
        self,
        image_base64_or_url: str,
        image_stats: LeafImageStats
    ) -> Tuple[bool, bool, bool]:
        """
        Validates image features for human/person skin pixels or non-chili tree leaves (Mango).
        Returns: (is_chili_leaf: bool, is_person: bool, is_mango: bool)
        """
        green_ratio = image_stats.greenRatio or 0.0
        foliage_ratio = image_stats.foliageRatio or 0.0
        skin_ratio = image_stats.skinRatio or 0.0
        dark_green_ratio = image_stats.darkGreenRatio or 0.0
        glossy_ratio = image_stats.glossyRatio or 0.0
        plant_ratio = green_ratio + foliage_ratio

        # Person Detection Rule
        is_person = skin_ratio >= 0.12 or (skin_ratio >= 0.04 and (skin_ratio > plant_ratio * 0.4 or plant_ratio < 0.12))
        if is_person:
            return False, True, False

        # Mango / Non-Chili Tree Leaf Rule
        is_mango = dark_green_ratio >= 0.35 and glossy_ratio >= 0.02
        if is_mango:
            return False, False, True

        # General Chili Leaf Verification Rule
        is_chili_leaf = plant_ratio >= 0.05 and skin_ratio < 0.06
        return is_chili_leaf, False, False


validation_service = ValidationService()
