# Ansible dynamic inventory plugin for Hetzner dedicated servers

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This is an Ansible dynamic inventory plugin for [Hetzner's bare metal
dedicated server](https://www.hetzner.de/dedicated-rootserver) offering.
It utilizes the [Robot webservice API][robot-api] at

> https://robot-ws.your-server.de

This plugin complements the [hcloud inventory plugin](
https://docs.ansible.com/ansible/latest/plugins/inventory/hcloud.html )
and the related [hcloud modules](
https://docs.ansible.com/ansible/latest/modules/list_of_cloud_modules.html#hcloud
) for [Hetzner cloud servers](https://www.hetzner.de/cloud).

## Installation

Simply put the Python script into [one of the default locations][dev-local]
or into a subdir with the name `inventory_plugins` next to your playbooks.

`ansible-playbook` will usually be able to pick up the plugin automatically,
however, commands like `ansible-inventory` and `ansible-doc` might require
an additional entry in `ansible.cfg` to find it:

```ini
[defaults]
inventory_plugins = ./inventory_plugins
```

To check if the plugin is picked up (and to show it's documentation):

```shell
$ ansible-doc -t inventory hrobot
```

## Configuration

Using the plugin requires a YAML configuration file with a name that ends
with `hrobot.yaml` or `hrobot.yml`, e.g.:

*demo.hrobot.yaml:*

```yaml
plugin: hrobot

# Credentials can alternatively be provided in `HETZNER_ROBOT_USER` and
# `HETZNER_ROBOT_PASSWORD` via the environment.
api_user: "<your API user"
api_password: "<your API PW>"

groups:
  proxy_hosts: inventory_hostname.startswith("proxy")
  staging_hosts: inventory_hostname is regex(".*\.staging\.example\.com")

keyed_groups:
  - key: product | lower
    prefix: type
  - key: dc
    separator: ""
```

The following will then print out the whole inventory in JSON format:

```shell
$ ansible-inventory -i demo.hrobot.yaml --list
```

### Constructing groups

From the raw inventory data of the API you can construct additional host
groups as in the example config above:

* `groups` based on Jinja2 conditionals, e.g. regexes.
* `keyed_groups` based on host variables provided by the API.

Specifying any additional groups is optional; all host attributes
returned by the [Robot API][robot-api] also end up as hostvars.  Here is
an example what variables we get for each host:

```json
"server.example.com": {
    "ansible_ssh_user": "root",
    "cancelled": false,
    "dc": "FSN1-DC8",
    "flatrate": true,
    "jobdir": "/tmp",
    "paid_until": "2099-12-31",
    "product": "EX41S-SSD",
    "server_ip": "192.0.2.10",
    "server_number": 987654,
    "status": "ready",
    "throttled": false,
    "traffic": "unlimited"
}
```

For more details see the ["constructed" inventory plugin][grouping].

### Security

For added security credentials in the config file can be encrypted via
`ansible-vault`, e.g.:

```yaml
plugin: hrobot
api_user: "<your API user>"
api_password: !vault |
          $ANSIBLE_VAULT;1.2;AES256;dummy
          62353431303730613536656135663237633934616539396136623566386566316165343764363733
          6664356532383035323665636437353936326361373461320a643165623632373363336162653936
          66613431353538666636326538646630356436643633656266663234663232653261626338306666
          3363353934616362630a386433346563626533626462396463396139393434653935373037356336
          36363035323864343032383438326533636437333531633162386236353535386537
```

To print the inventory or to run playbooks you then have to prompt for the
vault key:

```shell
$ ansible-inventory -i demo.hrobot.yaml --list --vault-id demo@prompt
```

## Caching

To reduce the number of API requests the plugin is able to locally cache
inventory data.  This first requires some general configuration in
`ansible.cfg`:

```ini
[inventory]
# Which cache plugin to use.
cache_plugin=jsonfile
# Where to store cached data.
cache_connection=./.cache
# Lifetime of cached data (default 3600).
cache_timeout=1800
```

After that actual caching can be enabled on a per-inventory basis in the
respective YAML file, e.g.:

```yaml
plugin: hrobot
cache: True
api_user: ...
# [...]
```

For more details and a list of available cache plugins see the
related [Ansible documentation][cache].

## References

* [Inventory plugins][inventory], Ansible documentation.
* [Developing dynamic inventory][inventory-dev], Ansible documentation.
* [Adding modules and plugins locally][dev-local], Ansible documentation.
* [Using Jinja2 to construct vars and groups][grouping], Ansible documentation.
* [Cache plugins][cache], Ansible documentation.
* [Managing Meaningful Inventories][inv-slides], AnsibleFest2019, slides (PDF)
* [Ansible Custom Inventory Plugin - a hands-on, quick start guide][inv-blog], blog post.

[robot-api]: https://robot.your-server.de/doc/webservice/en.html
[inventory]: https://docs.ansible.com/ansible/latest/plugins/inventory.html
[inventory-dev]: https://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html
[grouping]: https://docs.ansible.com/ansible/latest/plugins/inventory/constructed.html
[cache]: https://docs.ansible.com/ansible/latest/plugins/cache.html
[dev-local]: https://docs.ansible.com/ansible/latest/dev_guide/developing_locally.html
[inv-slides]: https://www.ansible.com/hubfs//AnsibleFest%20ATL%20Slide%20Decks/AnsibleFest%202019%20-%20Managing%20Meaningful%20Inventories.pdf
[inv-blog]: https://termlen0.github.io/2019/11/16/observations/

## License

GNU General Public License v3.0 or later.  This follows the general
licensing of the Ansible project.
