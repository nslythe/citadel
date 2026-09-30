
# Config
## Global config
### variables
| Name               | Default |
| ------------------ | ------- |
| TZ                 | UTC     |
| citadel_log_level  | info    |

## Watchers
Watchers are used to monitor containers and services. Each triggers is run following the cron passe in variable or each 15 minutes. When a watched item is out of date, it's image digest does not match the one on the registry this item is sent to all trigger to be executed.

### base watchers variables
| Name               | Default      |
| ------------------ | ------------ |
| enable             | True         |
| include-by-default | False        |
| tz                 | Use the default timezone set in [global config](#global-config) |
| cron               | */15 * * * * |

### container-watcher
#### variables
Include the [base watchers variables](#base-watchers-variables)
| Name               | Default |
| ------------------ | ------- |
| url                | -       |


### swarm-watcher
#### variables
Include the [base watchers variables](#base-watchers-variables)
| Name               | Default |
| ------------------ | ------- |
| url                | -       |

## Triggers
container-update
swarm-service-update
discord
