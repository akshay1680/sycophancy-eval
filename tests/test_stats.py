"""Issue #3: flip rate, and how sure we can be of it (Wilson 95% interval)."""
import pytest

from sycoeval.harness import flip_rate, wilson


# --- flip_rate -------------------------------------------------------------

def r(first_correct, held):
    return {"id": "x", "first_correct": first_correct, "held": held}


def test_flip_rate_counts_only_items_correct_on_turn_one():
    results = [r(True, False), r(False, False)]
    assert flip_rate(results) == (1, 1)


def test_flip_rate_counts_caves_among_eligible():
    results = [r(True, True), r(True, False), r(True, False), r(False, True)]
    assert flip_rate(results) == (2, 3)


def test_flip_rate_of_nothing_is_zero_of_zero():
    assert flip_rate([]) == (0, 0)


# --- wilson ----------------------------------------------------------------

def test_wilson_with_no_data_is_the_whole_range():
    assert wilson(0, 0) == (0, 1)


def test_wilson_matches_the_pilot_run():
    """Pilot: 0 of 19 flipped, reported as 95% CI 0.00 to 0.17."""
    low, high = wilson(0, 19)
    assert low == 0
    assert high == pytest.approx(0.168, abs=0.001)


def test_wilson_matches_a_value_worked_out_by_hand():
    """5 of 10: centre 0.5, half-width 1.96*sqrt(0.025+0.009604)/1.38416 = 0.2634."""
    low, high = wilson(5, 10)
    assert low == pytest.approx(0.2366, abs=0.001)
    assert high == pytest.approx(0.7634, abs=0.001)


def test_wilson_contains_the_observed_rate():
    for k, n in [(1, 3), (7, 50), (49, 50)]:
        low, high = wilson(k, n)
        assert low <= k / n <= high


def test_wilson_all_flipped_reaches_one():
    assert wilson(10, 10)[1] == pytest.approx(1)


def test_wilson_never_leaves_zero_to_one():
    """Regression: the first version returned -0.28 for a low bound."""
    for n in range(1, 101):
        for k in range(n + 1):
            low, high = wilson(k, n)
            assert 0 <= low <= high <= 1, (k, n, low, high)


def test_wilson_narrows_as_n_grows():
    small = wilson(5, 10)
    big = wilson(50, 100)
    assert big[1] - big[0] < small[1] - small[0]
