from Products.ZenModel.NotificationSubscription import NotificationSubscription

from Products.Zuul.infos import InfoBase
from Products.Zuul.infos.actions import ActionFieldProperty

from zope.component import adapts
from zope.interface import implements

from .interface import IHttpBinActionContentInfo


class HttpBinActionContentInfo(InfoBase):
    implements(IHttpBinActionContentInfo)
    adapts(NotificationSubscription)

    hbSource  = ActionFieldProperty(IHttpBinActionContentInfo, "hbSource")
    hbEventClass  = ActionFieldProperty(IHttpBinActionContentInfo, "hbEventClass")
    hbDescription  = ActionFieldProperty(IHttpBinActionContentInfo, "hbDescription")
    hbFullDescription  = ActionFieldProperty(IHttpBinActionContentInfo, "hbFullDescription")
    skipfails  = ActionFieldProperty(IHttpBinActionContentInfo, "skipfails")