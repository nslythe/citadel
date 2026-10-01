
from litestar import Litestar
from litestar.di import Provide
from litestar.logging import LoggingConfig
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import SwaggerRenderPlugin
from .. import app
from . import routers
import uvicorn

citadel_app = None
def get_citadel_app() -> app.App:
    return citadel_app

openapi_config = OpenAPIConfig(
        title = "fix-ratio api",
        description = "",
        version = "0.0.1",
        path = "/doc",
        render_plugins = [SwaggerRenderPlugin()]
    )

logging_config = LoggingConfig(
    root={"level": "INFO", "handlers": ["queue_listener"]},
    formatters={
        "standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}
    },
    log_exceptions="always",
    disable_existing_loggers = False
)

litestar_app = Litestar(
    route_handlers=routers.get_routers(),
    openapi_config = openapi_config,
    logging_config = logging_config,
    dependencies={
        "citadel_app" : Provide(get_citadel_app, sync_to_thread=True)
    })

def run_server(c_app: app.App, *, host="0.0.0.0", port=8000, log_level="debug"):
    global citadel_app
    citadel_app = c_app

    uvicorn.run(
        litestar_app,
        host=host, 
        port=port,
        log_level=log_level
    )