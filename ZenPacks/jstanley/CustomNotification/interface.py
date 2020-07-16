from Products.Zuul.form import schema
from Products.Zuul.interfaces import IInfo
from Products.Zuul.utils import ZuulMessageFactory as _t


class IHttpBinActionContentInfo(IInfo):
    hbSource = schema.TextLine(
        title=_t(u"Source"),
        description=_t(u"Source Field"),
        default=u"Zenoss"
    )

    hbEventClass = schema.TextLine(
        title=_t(u"Event Class"),
        description=_t(u"event_class Field"),
        default=u"${evt/eventClass}"
    )

    hbDescription = schema.TextLine(
        title=_t(u"Short Description"),
        description=_t(u"Short description Field"),
        default=u"${evt/summary}"
    )

    hbFullDescription = schema.Text(
        title=_t(u"Full description"),
        description=_t(u"Full multiline description"),
        default=u'\n'.join([
            "device=${evt/tag}",
            "deviceTitle=${dev/titleOrId}",
            "componentTitle=${component/titleOrId}",
            "collector=${evt/monitor}",
            "message=${evt/message}",
        ])
    )

    skipfails = schema.Bool(
        title=_t(u"Skip fails in TALES evaluation?"),
        description=_t(u"Skip bad TALES expression"),
        default=True,
    )