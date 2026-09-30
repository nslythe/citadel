
# Config
[examples](doc/config-examples.md)

Every watcher and trigger is configured with environment variables (or a `.env` file, see [env file](#env-file)) named:

```
citadel_<type-name>__<name>__<option>
```

* `citadel_` is the reserved prefix.
* `__` is the separator, a `<name>` cannot contain it.
* `<option>` is the name of an option of the `<type-name>`, options are python identifiers, so `-` is not a separator.

Each `<type-name>` is loaded by its own [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) class, options are typed and validated when the application starts. An unknown `<type-name>`, an unknown option, an invalid value or a missing required option stops the application with an explicit error.

## Global config
### variables
| Name               | Type   | Default |
| ------------------ | ------ | ------- |
| TZ                 | str    | UTC     |
| citadel_log_level  | str    | info    |

`TZ` can also be set with `citadel_tz`. It is the default timezone used by every watcher and trigger, each of them can override it with its own `tz` option.

## Watchers
Watchers are used to monitor containers and services. Each triggers is run following the cron passe in variable or each 15 minutes. When a watched item is out of date, it's image digest does not match the one on the registry this item is sent to all trigger to be executed.

### base watchers variables
| Name               | Type | Default      |
| ------------------ | ---- | ------------ |
| enable             | bool | True         |
| include_by_default | bool | False        |
| tz                 | str  | Use the default timezone set in [global config](#global-config) |
| cron               | str  | */15 * * * * |

### container-watcher
#### variables
Include the [base watchers variables](#base-watchers-variables)
| Name               | Type | Required | Default |
| ------------------ | ---- | -------- | ------- |
| url                | str  | yes      | -       |


### swarm-watcher
#### variables
Include the [base watchers variables](#base-watchers-variables)
| Name               | Type | Required | Default |
| ------------------ | ---- | -------- | ------- |
| url                | str  | yes      | -       |

## Triggers
### base triggers variables
| Name               | Type | Default |
| ------------------ | ---- | ------- |
| enable             | bool | True    |
| dry_run            | bool | False   |
| tz                 | str  | Use the default timezone set in [global config](#global-config) |

### container-update
No option, include the [base triggers variables](#base-triggers-variables)

### swarm-service-update
Include the [base triggers variables](#base-triggers-variables)
| Name               | Type | Default |
| ------------------ | ---- | ------- |
| pull_on_all_node   | bool | False   |

### discord
Include the [base triggers variables](#base-triggers-variables)
| Name               | Type | Required | Default |
| ------------------ | ---- | -------- | ------- |
| webhook            | str  | yes      | -       |

## Env file
The `.env` file located next to `main.py` is loaded on start up, environment variables have priority over it. In the container, variables are provided by the orchestrator, for example with `docker run --env-file .env` or the `env_file` key of a compose service.
