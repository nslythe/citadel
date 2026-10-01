
from citadel.watcher import  swarm_watcher, container_watcher
from citadel.trigger import swarm_service_update, discord, container_update
from citadel import api, app
import threading

supported_type = [
    swarm_watcher.SwarmWatcher,
    container_watcher.ContainerWatcher,
    swarm_service_update.SwarmServiceUpdate,
    container_update.ContainerUpdate,
    discord.Discord
]

if __name__ == "__main__":
    citadel_app = app.App(supported_type)

    server_thread = threading.Thread(target=api.run_server, args=(citadel_app,))
    server_thread.daemon = True
    server_thread.start()

    citadel_app.run()
