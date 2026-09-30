
```
citadel_swarm-watcher__docker-manager01__url = tcp://192.168.1.10:2375
citadel_swarm-watcher__docker-manager01__cron = */30 * * * *
citadel_swarm-watcher__docker-manager01__enable = True
```
```
citadel_container-watcher__docker-manager01__url = tcp://192.168.1.10:2375
citadel_container-watcher__docker-manager01__cron = */30 * * * *
citadel_container-watcher__docker-manager01__enable = True
```

```
citadel_container-update__auto-update__enable = true
```

```
citadel_swarm-service-update__updater__enable = true
citadel_swarm-service-update__updater__dry_run = true
citadel_swarm-service-update__updater__pull_on_all_node = true
```

```
citadel_discord__test__webhook = https://discord.com/api/webhooks/<id>/<token>
```

```
TZ=America/Montreal
citadel_log_level=info
```
