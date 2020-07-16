import re

from Products.ZenModel.actions import processTalSource


TAL_RE = re.compile('\$\{([-A-Za-z_.0-9]+/[-A-Za-z_.0-9]+)[\s+]?\}')


def processTALES(expression, skipfails, data):
    if not expression:
        return ''

    if skipfails:
        m = re.search(TAL_RE, expression)
        if m:
            expression = "${%s | string:}" % m.groups()[0]

    return processTalSource(expression, skipfails, **data)