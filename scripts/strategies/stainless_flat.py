from __future__ import annotations

STRATEGY_NAME = "stainless_flat"

FIELD_PROFILE = {
    "product_label": "\u54c1\u79cd",
    "spec_label": "\u89c4\u683c",
    "material_label": "\u6750\u8d28",
    "market_label": "\u5e02\u573a",
    "mill_labels": ["\u4f01\u4e1a"],
    "price_type_label": "\u5206\u7c7b",
    "extra_groups": {
        "brands": "\u54c1\u724c",
        "delivery_states": "\u4ea4\u8d27\u72b6\u6001",
    },
    "expandable_groups": ["\u6750\u8d28", "\u89c4\u683c", "\u4f01\u4e1a"],
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
