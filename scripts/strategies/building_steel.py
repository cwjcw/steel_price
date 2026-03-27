from __future__ import annotations

STRATEGY_NAME = "building_steel"

FIELD_PROFILE = {
    "product_label": "åå",
    "spec_label": "è§æ ¼",
    "material_label": "æè´¨",
    "market_label": "å¸åº",
    "mill_labels": ["é¢å/äº§å°", "ä¼ä¸", "é¢å"],
    "price_type_label": "ä»·æ ¼ç±»å",
    "extra_groups": {
        "mesh_models": "ç½çåå·",
    },
}


def apply_navigation(page, query, helpers):
    if query.category:
        helpers["click_main_nav"](page, query.category)
    if query.subcategory:
        helpers["click_sub_nav"](page, query.subcategory, nav_index=0)


def field_profile(query):
    return dict(FIELD_PROFILE)
