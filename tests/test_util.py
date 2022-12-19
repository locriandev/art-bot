from random import randint

from artbotlib import util


def test_cached():
    """
    A cached function returning a random integer will return the same value when called twice
    """

    @util.cached
    def a_function():
        return randint(0, 10)

    result_1 = a_function()
    result_2 = a_function()
    assert result_1 == result_2
