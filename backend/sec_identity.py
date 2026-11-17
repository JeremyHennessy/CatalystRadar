"""Private runtime SEC identification; never persist or print the contact."""
import os
import re


def contact_email():
    value = os.environ.get('SEC_CONTACT_EMAIL', '')
    if not isinstance(value, str) or len(value) > 254 or not re.fullmatch(
            r'[A-Za-z0-9.!#$%&\x27*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,63}', value):
        raise ValueError('SEC_CONTACT_EMAIL must contain an approved contact email; value omitted')
    return value


def user_agent(email):
    return 'CatalystRadar/0.1 research contact ' + email
