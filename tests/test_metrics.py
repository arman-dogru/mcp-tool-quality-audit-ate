import sys; sys.path.insert(0, "src")
from metrics import score

def test_empty_and_short():
    assert score("get_x", "")["empty"] and score("get_x", "")["underspecified"]
    assert score("ping", "Pings it.")["too_short"]

def test_overclaim():
    assert score("search", "The best and most comprehensive search for anything.")["overclaim"]
    assert not score("search", "Search issues by label. Returns a list of issue ids.")["overclaim"]

def test_io_spec():
    assert not score("get_weather", "Get the weather forecast for a city. Takes a city name and returns JSON.")["no_io_spec"]
    assert score("get_weather", "Weather information tool for travellers around the world today.")["no_io_spec"]

def test_name_echo():
    assert score("get_user_profile", "Get user profile")["name_echo"]
    assert not score("get_user_profile", "Fetch a user's profile by id, returning name and email.")["name_echo"]

def test_vague_underspecified():
    f = score("files", "Handles files and various other things for your project needs here.")
    assert f["vague"] and f["no_io_spec"] and f["underspecified"]

def test_side_effect_safety():
    assert score("delete_repo", "Delete a repository by name.")["side_effect_no_safety_cue"]
    assert not score("delete_repo", "Delete a repository by name. Irreversible; requires confirmation.")["side_effect_no_safety_cue"]

def test_non_english_and_deterministic():
    assert score("x", "检索反洗钱名单并返回结果列表")["non_english"]
    assert score("a", "Returns a list.") == score("a", "Returns a list.")

def test_cjk_length_not_counted_as_empty():
    f = score("calibrate_tables", "列出所有表，显示表名和行数")
    assert not f["empty"] and not f["too_short"]
