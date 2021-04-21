"""
Copyright (c) 2020 Keitaro AB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

# encoding: utf-8
import logging
import string
import re
import random
import secrets
from six import text_type

from ckanext.saml2auth.client import Saml2Client

from saml2.config import Config as Saml2Config

import ckan.model as model
import ckan.authz as authz
from ckan.common import config, asbool, aslist


log = logging.getLogger(__name__)


def saml_client(config):
    sp_config = Saml2Config()
    sp_config.load(config)
    client = Saml2Client(config=sp_config)
    return client


def generate_password():
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for i in range(8))
    return password


def is_default_login_enabled():
    return asbool(
        config.get('ckanext.saml2auth.enable_ckan_internal_login',
                   False))


def update_user_sysadmin_status(username, email):
    sysadmins_list = aslist(
        config.get('ckanext.saml2auth.sysadmins_list'))
    user = model.User.by_name(text_type(username))
    sysadmin = authz.is_sysadmin(username)

    if sysadmins_list:
        if sysadmin and email not in sysadmins_list:
            user.sysadmin = False
            model.Session.add(user)
            model.Session.commit()
        elif not sysadmin and email in sysadmins_list:
            user.sysadmin = True
            model.Session.add(user)
            model.Session.commit()


def activate_user_if_deleted(userobj):
    u'''Reactivates deleted user.'''
    if not userobj:
        return
    if userobj.is_deleted():
        userobj.activate()
        userobj.commit()
        log.info(u'User {} reactivated'.format(userobj.name))


def ensure_unique_username_from_email(email):
    localpart = email.split('@')[0]
    cleaned_localpart = re.sub(r'[^\w]', '-', localpart).lower()

    if not model.User.get(cleaned_localpart):
        return cleaned_localpart

    max_name_creation_attempts = 10

    for i in range(max_name_creation_attempts):
        random_number = random.SystemRandom().random() * 10000
        name = '%s-%d' % (cleaned_localpart, random_number)
        if not model.User.get(name):
            return name

    return cleaned_localpart
