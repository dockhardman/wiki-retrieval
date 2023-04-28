import openai
import sanic
from pyassorted.datetime import Timer
from sanic.request import Request
from sanic.response import text as PlainTextResponse

from app.config import logger, settings
from app.deps import click_timer


def create_app():
    app = sanic.Sanic(
        name=settings.APP_NAME,
    )

    @app.before_server_start
    async def before_server_start(*_):
        openai.api_key = settings.OPENAI_API_KEY
        logger.debug("Have set OpenAI credential.")

    @app.get("/")
    async def root(request: "Request"):
        return PlainTextResponse("OK")

    # Dependencies injection
    app.ext.add_dependency(Timer, click_timer)

    # Blueprint

    return app


app = create_app()
