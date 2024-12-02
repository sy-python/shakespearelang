from shakespearelang import Shakespeare
from io import StringIO


def test_character_input(monkeypatch, capsys):
    reader = StringIO("Test")
    s = Shakespeare(
        "Foo. Juliet, a test. Romeo, a test.", input_style="reader", reader=reader
    )
    s.run_event("[Enter Romeo and Juliet]")

    s.run_sentence("Open your mind!", "Juliet")
    assert s.state.character_by_name("Romeo").value == 84

    s.run_sentence("Open your mind!", "Juliet")
    assert s.state.character_by_name("Romeo").value == 101

    s.run_sentence("Open your mind!", "Juliet")
    assert s.state.character_by_name("Romeo").value == 115

    s.run_sentence("Open your mind!", "Juliet")
    assert s.state.character_by_name("Romeo").value == 116

    s.run_sentence("Open your mind!", "Juliet")
    assert s.state.character_by_name("Romeo").value == -1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_numeric_input(monkeypatch, capsys):
    reader = StringIO("123\n-2aaa")
    s = Shakespeare(
        "Foo. Juliet, a test. Romeo, a test.", input_style="reader", reader=reader
    )
    s.run_event("[Enter Romeo and Juliet]")

    s.run_sentence("Listen to your heart!", "Juliet")
    assert s.state.character_by_name("Romeo").value == 123

    s.run_sentence("Open your mind!", "Juliet")
    assert s.state.character_by_name("Romeo").value == 10

    s.run_sentence("Listen to your heart!", "Juliet")
    assert s.state.character_by_name("Romeo").value == -2

    s.run_sentence("Listen to your heart!", "Juliet")
    assert s.state.character_by_name("Romeo").value == 0

    assert "".join(s.settings.input_manager._buffer) + reader.read() == "aaa"

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
