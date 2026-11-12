"""Pruebas unitarias para el autocompletador interactivo de comandos en harness/cli.py."""

import pytest
from prompt_toolkit.document import Document
from harness.cli import JarvisCommandCompleter, create_prompt_session


def test_completer_slash_prefix_suggests_all():
    completer = JarvisCommandCompleter()
    doc = Document("/p", cursor_position=2)
    completions = list(completer.get_completions(doc, None))

    matches = [c.text for c in completions]
    assert "/plan" in matches
    assert "/steps" not in matches

    # Meta de /plan
    plan_c = next(c for c in completions if c.text == "/plan")
    assert "Arquitecto" in plan_c.display_meta_text


def test_completer_all_on_slash():
    completer = JarvisCommandCompleter()
    doc = Document("/", cursor_position=1)
    completions = list(completer.get_completions(doc, None))

    matches = [c.text for c in completions]
    assert "/model" in matches
    assert "/plan" in matches
    assert "/doctor" in matches
    assert "/tokens" in matches
    assert "/diff" in matches
    assert "/tree" in matches
    assert "/approval" in matches


def test_completer_no_match_on_regular_text():
    completer = JarvisCommandCompleter()
    doc = Document("crea una funcion en python", cursor_position=26)
    completions = list(completer.get_completions(doc, None))
    assert len(completions) == 0


def test_create_prompt_session_instantiation():
    session = create_prompt_session()
    assert session is not None
    assert session.completer is not None


def test_completer_subcommands_for_model():
    completer = JarvisCommandCompleter()
    doc = Document("/model ", cursor_position=7)
    completions = list(completer.get_completions(doc, None))
    matches = [c.text for c in completions]
    assert "add" in matches
    assert "list" in matches
    assert "rm" in matches


def test_completer_subcommands_filter():
    completer = JarvisCommandCompleter()
    doc = Document("/approval a", cursor_position=11)
    completions = list(completer.get_completions(doc, None))
    matches = [c.text for c in completions]
    assert "auto" in matches
    assert "confirm" not in matches


def test_completer_local_files(tmp_path):
    (tmp_path / "empanada.html").write_text("test", encoding="utf-8")
    (tmp_path / "main.py").write_text("test", encoding="utf-8")

    completer = JarvisCommandCompleter(base_dir=tmp_path)
    text = "revisa el archivo empanada."
    doc = Document(text, cursor_position=len(text))
    completions = list(completer.get_completions(doc, None))
    matches = [c.text for c in completions]
    assert "empanada.html" in matches
