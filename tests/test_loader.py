"""Tests for engine/loader.py — bot discovery, validation, error handling."""


from engine.loader import load_bots


def _write_bot(tmp_path, filename, content):
    """Write a bot file to tmp_path."""
    path = tmp_path / filename
    path.write_text(content)
    return path


VALID_BOT = '''
BOT_NAME = "TestBot"
BOT_EMOJI = "🤖"
BOT_BIO = "A test bot"
BOT_AUTHOR = "tester"

def decide(state):
    return ("rest",)
'''

MINIMAL_BOT = '''
BOT_NAME = "Minimal"
BOT_EMOJI = "⚡"

def decide(state):
    return ("rest",)
'''


class TestLoadBots:
    def test_loads_valid_bot(self, tmp_path):
        _write_bot(tmp_path, "good_bot.py", VALID_BOT)
        bots = load_bots(str(tmp_path))
        assert len(bots) == 1
        assert bots[0]["name"] == "TestBot"
        assert bots[0]["emoji"] == "🤖"
        assert bots[0]["bio"] == "A test bot"
        assert bots[0]["author"] == "tester"
        assert callable(bots[0]["decide_func"])

    def test_minimal_bot_defaults(self, tmp_path):
        _write_bot(tmp_path, "min_bot.py", MINIMAL_BOT)
        bots = load_bots(str(tmp_path))
        assert len(bots) == 1
        assert bots[0]["bio"] == ""
        assert bots[0]["author"] == "unknown"

    def test_skips_template(self, tmp_path):
        _write_bot(tmp_path, "template.py", VALID_BOT)
        bots = load_bots(str(tmp_path))
        assert len(bots) == 0

    def test_skips_underscore_prefix(self, tmp_path):
        _write_bot(tmp_path, "_helper.py", VALID_BOT)
        bots = load_bots(str(tmp_path))
        assert len(bots) == 0

    def test_skips_non_py_files(self, tmp_path):
        (tmp_path / "readme.txt").write_text("not a bot")
        (tmp_path / "data.json").write_text("{}")
        bots = load_bots(str(tmp_path))
        assert len(bots) == 0

    def test_skips_missing_name(self, tmp_path):
        _write_bot(tmp_path, "bad.py", '''
BOT_EMOJI = "🤖"
def decide(state): return ("rest",)
''')
        bots = load_bots(str(tmp_path))
        assert len(bots) == 0

    def test_skips_missing_emoji(self, tmp_path):
        _write_bot(tmp_path, "bad.py", '''
BOT_NAME = "Bad"
def decide(state): return ("rest",)
''')
        bots = load_bots(str(tmp_path))
        assert len(bots) == 0

    def test_skips_missing_decide(self, tmp_path):
        _write_bot(tmp_path, "bad.py", '''
BOT_NAME = "Bad"
BOT_EMOJI = "🤖"
''')
        bots = load_bots(str(tmp_path))
        assert len(bots) == 0

    def test_skips_syntax_error(self, tmp_path):
        _write_bot(tmp_path, "broken.py", "def bad syntax(:")
        bots = load_bots(str(tmp_path))
        assert len(bots) == 0

    def test_alphabetical_order(self, tmp_path):
        _write_bot(tmp_path, "charlie.py", VALID_BOT.replace("TestBot", "C").replace("🤖", "C"))
        _write_bot(tmp_path, "alpha.py", VALID_BOT.replace("TestBot", "A").replace("🤖", "A"))
        _write_bot(tmp_path, "bravo.py", VALID_BOT.replace("TestBot", "B").replace("🤖", "B"))
        bots = load_bots(str(tmp_path))
        assert [b["name"] for b in bots] == ["A", "B", "C"]

    def test_empty_directory(self, tmp_path):
        bots = load_bots(str(tmp_path))
        assert bots == []

    def test_multiple_valid_bots(self, tmp_path):
        _write_bot(tmp_path, "bot_a.py", VALID_BOT.replace("TestBot", "A").replace("🤖", "🅰️"))
        _write_bot(tmp_path, "bot_b.py", VALID_BOT.replace("TestBot", "B").replace("🤖", "🅱️"))
        bots = load_bots(str(tmp_path))
        assert len(bots) == 2

    def test_decide_func_callable(self, tmp_path):
        _write_bot(tmp_path, "bot.py", VALID_BOT)
        bots = load_bots(str(tmp_path))
        result = bots[0]["decide_func"]({"round": 1})
        assert result == ("rest",)
