"""Stdlib test runner (no pytest needed): python run_tests.py"""
import traceback

from tests.test_worker import (
    test_invoice_books_and_verifies,
    test_idempotent_rebook,
    test_overdue_summary_generalizes,
)

CASES = [
    ("invoice books + verifies", test_invoice_books_and_verifies),
    ("idempotent rebook", test_idempotent_rebook),
    ("overdue summary generalizes", test_overdue_summary_generalizes),
]

def main():
    passed, failed = 0, 0
    for name, fn in CASES:
        try:
            fn()
            print(f"PASS: {name}")
            passed += 1
        except Exception:
            failed += 1
            print(f"FAIL: {name}")
            traceback.print_exc()
    print(f"{passed} passed, {failed} failed")
    raise SystemExit(1 if failed else 0)

if __name__ == "__main__":
    main()
