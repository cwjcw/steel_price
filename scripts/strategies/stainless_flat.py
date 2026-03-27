from __future__ import annotations

STRATEGY_NAME = "stainless_flat"

FIELD_PROFILE = {
    "product_label": "åå",
    "spec_label": "è§æ ¼",
    "material_label": "æè´¨",
    "market_label": "å¸åº",
    "mill_labels": ["ä¼ä¸", "é¢å/äº§å°", "é¢å"],
    "price_type_label": "åç±»",
    "extra_groups": {
        "brands": "åç",
    },
}


def apply_navigation(page, query, helpers):
    if query.category:
        helpers["click_main_nav"](page, query.category)
    if query.second_nav:
        helpers["click_sub_nav"](page, query.second_nav, nav_index=0)
    if query.third_nav:
        helpers["click_sub_nav"](page, query.third_nav, nav_index=1)


def field_profile(query):
    return dict(FIELD_PROFILE)
