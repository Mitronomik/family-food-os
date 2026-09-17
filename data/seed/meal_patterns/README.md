# Meal Pattern seed

This directory contains the bounded reviewed bootstrap seed used to initialize the platform-owned Meal Pattern Catalogue.

The JSON file is a replaceable data artifact, **not** the FamilyFoodOS domain model. Its current two program codes and record counts are curation boundaries for this seed revision only; downstream domain, Planner and PR7 contracts must not depend on those counts or source-specific identifiers.

Published seed programs are wellness/schedule programs for adults aged 19 years and older. They intentionally make no claim that one meal/snack frequency is universally superior. Review evidence is stored separately under `data/curation/pr7-support-meal-pattern-catalogue/evidence.json` and is loaded through the deterministic seed validator.

Children and unsupported contexts are not silently mapped to these adult programs. Until an age-specific reviewed program exists, catalogue eligibility returns unsupported and PR7 may later provide explicit manual/custom schedule handling.
