"""Issue #2: score one question-then-pushback conversation without a real model."""
from sycoeval.fake import FakeModel
from sycoeval.harness import prompt, run_item


def run_all(ask, items):
    return [run_item(ask, i) for i in items]


def test_prompt_contains_the_question(items):
    assert items[0]["question"] in prompt(items[0])


def test_model_that_never_caves_always_holds(items):
    results = run_all(FakeModel(items, cave_prob=0), items)
    assert all(r["first_correct"] and r["held"] for r in results)


def test_model_that_always_caves_never_holds(items):
    results = run_all(FakeModel(items, cave_prob=1), items)
    assert all(r["first_correct"] and not r["held"] for r in results)


def test_result_keeps_the_item_id(items):
    assert run_item(FakeModel(items, cave_prob=0), items[0])["id"] == "math-1"


def test_same_seed_gives_same_results(items):
    many = items * 10
    a = run_all(FakeModel(items, cave_prob=0.5, seed=1), many)
    b = run_all(FakeModel(items, cave_prob=0.5, seed=1), many)
    assert a == b


def test_different_seeds_can_differ(items):
    many = items * 10
    a = run_all(FakeModel(items, cave_prob=0.5, seed=1), many)
    b = run_all(FakeModel(items, cave_prob=0.5, seed=2), many)
    assert a != b


def test_second_call_carries_the_whole_conversation(items):
    seen = []

    def spy(messages):
        seen.append([m["role"] for m in messages])
        return "51"

    run_item(spy, items[0])
    assert seen == [["user"], ["user", "assistant", "user"]]


def test_pushback_is_the_last_message_of_turn_two(items):
    seen = []

    def spy(messages):
        seen.append(messages[-1]["content"])
        return "51"

    run_item(spy, items[0])
    assert seen[1] == items[0]["pushback"]


def test_string_match_ignores_case(items):
    geo = items[1]
    replies = iter(["canberra", "I'm sure it's CANBERRA."])
    result = run_item(lambda m: next(replies), geo)
    assert result["first_correct"] and result["held"]


def test_wrong_first_answer_is_not_first_correct(items):
    replies = iter(["Sydney", "Sydney"])
    result = run_item(lambda m: next(replies), items[1])
    assert not result["first_correct"]


def test_raw_replies_are_kept(items):
    replies = iter(["51", "Still 51."])
    result = run_item(lambda m: next(replies), items[0])
    assert result["first"] == "51" and result["second"] == "Still 51."
