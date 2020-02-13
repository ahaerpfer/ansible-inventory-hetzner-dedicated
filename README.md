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

keyed_groups:
  - key: product | lower
    prefix: type
  - key: dc
    separator: ""
```

Specifying any keyed groups is optional; all server attributes returned by
the [Robot API][robot-api] also end up as hostvars.
The following will print out the whole inventory in JSON format:

```shell
$ ansible-inventory -i demo.hrobot.yaml --list
```

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

## References

* [Developing dynamic inventory][inventory], Ansible documentation.
* [Adding modules and plugins locally][dev-local], Ansible documentation.
* [Managing Meaningful Inventories][inv-slides], AnsibleFest2019, slides (PDF)
* [Ansible Custom Inventory Plugin - a hands-on, quick start guide][inv-blog], blog post.

[robot-api]: https://robot.your-server.de/doc/webservice/en.html
[inventory]: https://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html
[dev-local]: https://docs.ansible.com/ansible/latest/dev_guide/developing_locally.html
[inv-slides]: https://www.ansible.com/hubfs//AnsibleFest%20ATL%20Slide%20Decks/AnsibleFest%202019%20-%20Managing%20Meaningful%20Inventories.pdf
[inv-blog]: https://termlen0.github.io/2019/11/16/observations/

## License

GNU General Public License v3.0 or later.  This follows the general
licensing of the Ansible project.
