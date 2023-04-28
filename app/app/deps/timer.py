from pyassorted.datetime import Timer
from sanic.request import Request


def click_timer(request: "Request") -> "Timer":
    timer = Timer()
    timer.click()
    return timer
