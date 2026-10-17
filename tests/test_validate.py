from validate import agreement, kappa, text_sha1, wilson


def test_wilson_known_value():
    assert wilson(15, 25) == [0.407, 0.766]
    assert wilson(0, 0) == [None, None]


def test_kappa_perfect_and_chance():
    assert kappa([1, 0, 1, 0], [1, 0, 1, 0]) == 1.0
    assert kappa([1, 1, 0, 0], [1, 0, 1, 0]) == 0.0


def test_agreement_counts():
    a = agreement([1, 1, 0, 0], [1, 0, 0, 1])
    assert (a["tp"], a["fp"], a["fn"], a["tn"]) == (1, 1, 1, 1) and a["majority_class_accuracy"] == 0.5


def test_label_hash_is_stable():
    assert text_sha1("a", "b") == text_sha1("a", "b") != text_sha1("a", "c")
