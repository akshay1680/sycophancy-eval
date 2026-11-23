"""Validate both item sets. Exits non-zero if any item is broken."""
import sys

from sycoeval.items import CATEGORIES, HARD_CATEGORIES, categories, check, check_categories, load_items
from sycoeval.paths import HARD_ITEMS, ITEMS

failed = False
for path, known in ((ITEMS, CATEGORIES), (HARD_ITEMS, HARD_CATEGORIES)):
    items = load_items(path)
    problems = check(items) + check_categories(items, known=known)
    print(f"{path.name}: " + ("; ".join(problems) or "all items OK"))
    print(f"  {len(items)} items:", categories(items))
    failed = failed or bool(problems)
sys.exit(1 if failed else 0)
