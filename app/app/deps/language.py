from sanic.request import Request

from lingua import LanguageDetector


def language_detector(request: Request) -> "LanguageDetector":
    return request.app.ctx.language_detector
