
# Global config
## variables
| Name               | Default |
| ------------------ | ------- |
|              |        |

# Watchers
## base watchers variables
| Name               | Default      |
| ------------------ | ------------ |
| enable             | True         |
| include-by-default | False        |
| tz                 | Use the default timezone set in [global config](#global-config) |
| cron               | */15 * * * * |


## container-watcher
### variables
Include the [base watchers variables](#base-watchers-variables)
| Name               | Default |
| ------------------ | ------- |
| url                | -       |


## swarm-watcher
### variables
Include the [base watchers variables](#base-watchers-variables)
| Name               | Default |
| ------------------ | ------- |
| url                | -       |

# Triggers
container-update
swarm-service-update
discord
