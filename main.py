
from citadel.watcher import base_watcher, swarm_watcher, container_watcher
from citadel.trigger import base_trigger, swarm_service_update, discord, container_update
from citadel.config import config
import logging
import time

supported_type = [
    swarm_watcher.SwarmWatcher,
    container_watcher.ContainerWatcher,
    swarm_service_update.SwarmServiceUpdate,
    container_update.ContainerUpdate,
    discord.Discord
]

def set_logger():
    logging.root.setLevel(level=config.global_settings().log_level.upper())
    logging.getLogger("docker").setLevel(level="ERROR")
    logging.getLogger("urllib3").setLevel(level="ERROR")

if __name__ == "__main__":
    set_logger()

    conf = config.Config(plugins=supported_type)
    conf.load()

    watchers = []
    single_message_triggers = []
    multi_message_triggers = []

    for v in conf.instances:
        if isinstance(v, base_watcher.BaseWatcher):
            watchers.append(v)
        if isinstance(v, base_trigger.BaseTriggerSingleMessage):
            single_message_triggers.append(v)
        if isinstance(v, base_trigger.BaseTriggerMultiMessage):
            multi_message_triggers.append(v)

    # check swarm list
    known_swarm_id = {}
    for w in watchers:
        if isinstance(w, swarm_watcher.SwarmWatcher):
            if w.swarm_id in known_swarm_id:
                logging.warning("watcher \"%s\" disable because swarm already known from \"%s\"", w.name, known_swarm_id[w.swarm_id].name)
                w.enable = False
                continue
            known_swarm_id[w.swarm_id] = w

    ######## MAIN LOOP ########
    while True:
        for w in watchers:
            check_list = w.check()
            if len(check_list) > 0:
                for t in multi_message_triggers:
                    t.trigger(check_list)
                for c in check_list:
                    for t in single_message_triggers:
                        t.trigger(c)

        time.sleep(3)
