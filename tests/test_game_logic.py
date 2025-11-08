# tests/test_game_logic.py
from server.game_logic import get_result
def test_draw():
    assert get_result('rock','rock') == 'draw'
def test_win():
    assert get_result('rock','scissors') == 'win'
def test_lose():
    assert get_result('paper','scissors') == 'lose'
print('Basic tests passed (run with python -m pytest tests)')