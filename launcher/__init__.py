"""Local runtime launcher foundation for FamilyFoodOS."""

# Bootstrap-safe launcher projections of the canonical identity in
# backend/app/identity.py. They must match it: the launcher package loads before
# runtime establishes the backend import path, so app.identity is unavailable here.
APP_SLUG = "family-food-os"
PRODUCT_NAME = "FamilyFoodOS"
