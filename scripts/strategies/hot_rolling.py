from __future__ import annotations

STRATEGY_NAME = "hot_rolling"

FIELD_PROFILE = {
    "product_label": "品种",
    "spec_label": "规格",
    "material_label": "材质",
    "market_label": "市场",
    "mill_labels": ["企业", "钢厂", "钢厂/产地"],
    "price_type_label": "",
    "extra_groups": {
        "diameters": "口径",
    },
    "expandable_groups": ["规格", "材质", "企业"],
}


def apply_navigation(page, query, helpers):
    if query.category:
        helpers["click_main_nav"](page, query.category)
    if query.subcategory:
        helpers["click_sub_nav"](page, query.subcategory, nav_index=0)


def field_profile(query):
    return dict(FIELD_PROFILE)
