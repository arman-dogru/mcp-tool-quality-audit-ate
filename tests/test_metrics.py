import math

from metrics import n_words, score


def test_empty_and_short():
    assert score("get_x", "")["is_empty"] and score("get_x", "")["underspecified"]
    assert score("ping", "Pings it.")["too_short"]


def test_bad_inputs_are_coerced():
    for name, desc in [(math.nan, "x"), ("x", math.nan), ("x", 123), (None, None)]:
        f = score(name, desc)
        assert isinstance(f["n_words"], int)
    assert score("x", None)["is_empty"]


def test_overclaim_pruned_neutral_words():
    assert score("search", "The best, state-of-the-art search, guaranteed.")["overclaim"]
    assert not score("get_status", "Returns any errors")["overclaim"]
    assert not score("x", "Returns the complete list of every comprehensive report.")["overclaim"]


def test_io_spec_word_boundary():
    assert not score("get_weather", "Get the weather forecast for a city. Takes a city name and returns JSON.")["no_io_spec"]
    assert score("search", "Search arguments in Argentina takeover paramount stringify")["no_io_spec"] is False  # 'arguments' is a real hit
    assert score("search", "Search Argentina takeover paramount stringify news headlines")["no_io_spec"]


def test_name_echo_guard_empty_tokens():
    assert score("get_user_profile", "Get user profile")["name_echo"]
    assert not score("get_user_profile", "Fetch a user's profile by id, returning name and email.")["name_echo"]
    assert not score("ls", "List files")["name_echo"]


def test_vague_underspecified():
    f = score("files", "Handles files and various other things for your project needs here.")
    assert f["vague"] and f["no_io_spec"] and f["underspecified"] and f["underspecified_content"]


def test_destructive_inflections_and_split():
    assert score("tool", "Deletes the specified file.")["destructive"]
    assert score("tool", "Dropped tables are gone.")["destructive"]
    f = score("tool", "Creates a new issue.")
    assert f["mutating"] and not f["destructive"]
    assert not score("add", "Add two numbers.")["mutating"]


def test_destructive_trigger_field_and_cue():
    f = score("delete_repo", "")
    assert f["destructive"] and not f["destructive_desc"] and f["destructive_no_safety_cue"]
    assert score("delete_repo", "Delete a repository by name.")["destructive_no_safety_cue"]
    assert not score("delete_repo", "Deletes a repository. This cannot be undone; requires confirmation.")["destructive_no_safety_cue"]
    assert not score("delete_repo_dry_run", "")["destructive_no_safety_cue"]  # cue in the name counts too


def test_word_count_unicode():
    assert n_words("Récupère les données météo pour une ville") == 7
    assert n_words("a b c") == 3  # one-letter words count
    assert n_words("🚀🚀🚀🚀") == 0  # emoji are not words
    assert n_words("列出所有表，显示表名和行数") == 6  # 12 Han chars / 2


def test_non_latin_script_not_language():
    assert score("x", "检索反洗钱名单并返回结果列表")["non_latin_script"]
    assert not score("x", "Récupère les données météo pour une ville donnée")["non_latin_script"]  # French is Latin script


def test_cjk_length_not_counted_as_empty():
    f = score("list_tables", "列出数据库中的全部表格名称")
    assert not f["is_empty"] and not f["too_short"]
