"""Validate data/items.jsonl. Exits non-zero if any item is broken."""
import sys

from sycoeval.items import categories, check, check_categories, load_items

items = load_items()
problems = check(items) + check_categories(items)
print("\n".join(problems) or "all items OK")
print(f"{len(items)} items:", categories(items))
sys.exit(1 if problems else 0)
