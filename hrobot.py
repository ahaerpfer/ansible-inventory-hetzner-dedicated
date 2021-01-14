# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Andreas Härpfer
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
    name: hrobot
    plugin_type: inventory
    author:
        - Andreas Haerpfer
    short_description: Ansible dynamic inventory plugin for Hetzner dedicated servers.
    requirements:
        - python >= 2.7
    description:
        - Reads inventory data from the Hetzner Robot API.
        - Uses a YAML configuration file that ends with hrobot.(yml|yaml).
    extends_documentation_fragment:
        - constructed
        - inventory_cache
    options:
        plugin:
            description: Marks this as an instance of the "hrobot" plugin
            required: true
            choices: ["hrobot"]
        api_user:
            description: The Hetzner Robot API user.
            required: true
            env:
                - name: HETZNER_ROBOT_USER
        api_password:
            description: The Hetzner Robot API password.
            required: true
            env:
                - name: HETZNER_ROBOT_PASSWORD
"""

EXAMPLES = r"""
# Minimal example. `HETZNER_ROBOT_USER` and `HETZNER_ROBOT_PASSWORD` have to
# be provided via the environment.

plugin: hrobot


# Example including credentials.  The API password has been encrypted with
# ansible-vault for added security.

plugin: hrobot
api_user: "#ws+XXXXXXXX"
api_password: !vault |
          $ANSIBLE_VAULT;1.2;AES256;dummy
          62353431303730613536656135663237633934616539396136623566386566316165343764363733
          6664356532383035323665636437353936326361373461320a643165623632373363336162653936
          66613431353538666636326538646630356436643633656266663234663232653261626338306666
          3363353934616362630a386433346563626533626462396463396139393434653935373037356336
          36363035323864343032383438326533636437333531633162386236353535386537


# Additionally group by Jinja2 expression or by host variable with prefix,
# e.g. "type_ex41" and by data center location without a prefix, e.g.
# "FSN1_DC4".  Jinja filters can be used for additional transformations.
# `prefix` defaults to "", `separator` defaults to "_".

plugin: hrobot

groups:
  proxy_hosts: inventory_hostname.startswith("proxy")
  staging_hosts: inventory_hostname is regex(".*\.staging\.example\.com")

keyed_groups:
  - key: product | lower
    prefix: type
  - key: dc
    separator: ""
"""

import json
import os
from ansible.errors import AnsibleError
from ansible.module_utils.urls import open_url
from ansible.module_utils._text import to_native
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable
from ansible.release import __version__


class RobotAPI:

    BASE = "https://robot-ws.your-server.de"

    def __init__(self, user, password):
        self.user = user
        self.password = password

    def get_servers(self):
        api_url = "%s/server" % self.BASE
        try:
            response = open_url(
                api_url,
                url_username=self.user,
                url_password=self.password,
                headers={"Content-type": "application/json"},
            )
            servers = json.loads(response.read())
            return servers
        except ValueError:
            raise AnsibleError("Incorrect JSON payload")
        except Exception as e:
            raise AnsibleError("Error while fetching %s: %s" % (api_url, to_native(e)))


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):

    NAME = "hrobot"

    def verify_file(self, path):
        return super(InventoryModule, self).verify_file(path) and path.endswith(
            (self.NAME + ".yaml", self.NAME + ".yml")
        )

    def _read_servers_from_API(self):
        servers = RobotAPI(
            self.get_option("api_user"), self.get_option("api_password")
        ).get_servers()
        return servers

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path, cache)
        config = self._read_config_data(path)
        cache_key = self.get_cache_key(path)

        # `cache` may be True or False at this point to indicate if the
        # inventory is being refreshed.  Get the user's cache option too
        # to see if we should save the cache when it is changing.
        user_cache_setting = self.get_option("cache")

        # Read if the user has caching enabled and the cache isn't being
        # refreshed.
        attempt_to_read_cache = user_cache_setting and cache

        # Update if the user has caching enabled and the cache is being
        # refreshed; update this value to True if the cache has expired below.
        cache_needs_update = user_cache_setting and not cache

        # Attempt to read the cache if inventory isn't being refreshed and
        # the user has caching enabled.
        if attempt_to_read_cache:
            try:
                servers = self._cache[cache_key]
            except KeyError:
                # This occurs if the cache_key is not in the cache or if
                # the cache_key expired, so the cache needs to be updated.
                servers = self._read_servers_from_API()
                cache_needs_update = True
        else:
            servers = self._read_servers_from_API()

        if cache_needs_update:
            self._cache[cache_key] = servers

        self.populate(servers)

    def populate(self, servers):
        # Add a default top group 'hetzner'
        self.inventory.add_group(group="hetzner")

        for server in servers:
            s = server["server"]
            sname = s["server_name"]
            self.inventory.add_host(sname, group="hetzner")

            self.inventory.set_variable(sname, "server_ip", to_native(s["server_ip"]))
            self.inventory.set_variable(sname, "server_number", s["server_number"])
            self.inventory.set_variable(sname, "product", to_native(s["product"]))
            self.inventory.set_variable(sname, "dc", to_native(s["dc"]))
            self.inventory.set_variable(sname, "traffic", to_native(s["traffic"]))
            self.inventory.set_variable(sname, "status", to_native(s["status"]))
            self.inventory.set_variable(sname, "cancelled", s["cancelled"])
            self.inventory.set_variable(sname, "paid_until", to_native(s["paid_until"]))
            # FIXME: self.inventory.set_variable(sname, "ip", ALIST s["ip"])
            # FIXME: self.inventory.set_variable(sname, "subnet", IP-MASK-PAIR s["subnet"])

            strict = self.get_option("strict")

            # Composed variables.
            self._set_composite_vars(
                self.get_option("compose"),
                self.inventory.get_host(sname).get_vars(),
                sname,
                strict=strict,
            )

            # Complex groups based on jinja2 conditionals, hosts that meet
            # the conditional are added to group.
            self._add_host_to_composed_groups(
                self.get_option("groups"), {}, sname, strict=strict
            )

            # Create groups based on variable values and add the corresponding
            # hosts to it.
            self._add_host_to_keyed_groups(
                self.get_option("keyed_groups"), {}, sname, strict=strict
            )
