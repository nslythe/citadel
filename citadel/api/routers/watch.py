
from litestar import get, Router, Controller
from litestar.exceptions import HTTPException
from citadel import app

class WatchController(Controller):
    @get("/watch/{name:str}")
    async def get_watch(self, name: str, citadel_app: app.App) -> str:
        if not citadel_app.has_watcher(name):
            raise HTTPException(f"Watcher {name} does not exists", status_code=404)
        citadel_app.watch(name)

    @get("/watch_all")
    async def get_watch_all(self, name: str, citadel_app: app.App) -> str:
        citadel_app.watch_all()

routers = [
    Router(path="/", route_handlers=[WatchController])
]
