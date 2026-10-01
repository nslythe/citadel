
from litestar import Litestar
from litestar.di import Provide
from .. import app
from . import routers
import uvicorn

citadel_app = None
def get_citadel_app() -> app.App:
    return citadel_app

litestar_app = Litestar(
    route_handlers=routers.get_routers(),
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