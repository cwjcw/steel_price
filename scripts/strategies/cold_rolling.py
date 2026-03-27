from __future__ import annotations

STRATEGY_NAME = "cold_rolling"

FIELD_PROFILE = {
    "product_label": "品名",
    "spec_label": "规格",
    "material_label": "材质",
    "market_label": "市场",
    "mill_labels": ["钢厂", "企业", "钢厂/产地"],
    "price_type_label": "价格类型",
    "extra_groups": {},
    "expandable_groups": ["规格", "材质"],
}


def apply_navigation(page, query, helpers):
    if query.category:
        helpers["click_main_nav"](page, query.category)
    if query.subcategory:
        helpers["click_sub_nav"](page, query.subcategory, nav_index=0)


def field_profile(query):
    return dict(FIELD_PROFILE)
