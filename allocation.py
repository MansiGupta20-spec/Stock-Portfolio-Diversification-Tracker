"""
allocation.py
Thin re-export shim.

app.py (Member C's frontend, and the team docs like CODE_REUSE_GUIDE.md /
PROJECT_BLUEPRINT.md) refer to this module as "allocation.py". Member B's
actual implementation lives in calculations.py (kept under that name for
consistency with earlier work — see the docstring there).

Rather than rename calculations.py (which would break pipeline_test.py,
backend_pipeline.py, and test_backend_unit.py, all of which import from
calculations), this file just re-exports the same two functions under
the name app.py expects. One source of truth, two import paths.
"""

from calculations import calculate_allocation, calculate_sector_allocation

__all__ = ["calculate_allocation", "calculate_sector_allocation"]
