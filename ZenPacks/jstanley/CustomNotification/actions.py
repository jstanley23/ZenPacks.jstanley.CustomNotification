import logging
import json
import re
import requests

from Products.ZenEvents.EventManagerBase import EventManagerBase
from Products.ZenEvents.events2.proxy import EventSummaryProxy
from Products.ZenModel.actions import IActionBase
from Products.ZenModel.interfaces import IAction
from Products.ZenUtils.guid.guid import GUIDManager
from Products.Zuul import getFacade

from zenoss.protocols.protobufs.zep_pb2 import EventDetailSet
from zenoss.protocols.services.zep import ZepConnectionError
try:
    from zenoss.protocols.services import ServiceConnectionError, ZepConnectionTimeout
except ImportError:
    class ZepConnectionTimeout(ZepConnectionError):
        pass

    class ServiceConnectionError(ZepConnectionError):
        pass

from zope.interface import implements

from .utils import processTALES
from .interface import IHttpBinActionContentInfo


LOG = logging.getLogger("zen.HttpBin.Notificaiton")


class HttpBinAction(IActionBase):
    implements(IAction)

    id = "HttpBin"
    name = "HttpBin"
    skipfails = True

    actionContentInfo = IHttpBinActionContentInfo

    shouldExecuteInBatch = False

    def logEventAction(self, notificationId, eventId, status, payload=None):
        logPayload = "Notification {} sent event {} as {} to HttpBin with payload: {}".format(
            notificationId,
            eventId,
            status,
            payload,
        )
        LOG.info(logPayload)

    def setupAction(self, dmd):
        self.guidManager = GUIDManager(dmd)
        self.dmd = dmd
        self.zep = getFacade("zep", self.dmd)
        self.statuses = {
            "0": "New",
            "1": "Acknowledged",
            "2": "Suppressed",
            "3": "Closed",
            "4": "Cleared",
            "5": "Dropped",
            "6": "Aged",
        }

    def updateEvent(self, evid, comment=None):
        if not evid:
            LOG.warn("Received an empty evid -- ignoring")
            return

        if comment:
            tryNum = 0
            while tryNum < 3:
                try:
                    self.zep.addNote(evid, comment, 'admin')
                    return
                except (ServiceConnectionError, ZepConnectionError, ZepConnectionTimeout):
                    tryNum += 1

        LOG.error("Unable to update event: %s" % evid)
        return

    def buildPayload(self, signal, notification, data):
        skipfails = notification.content.get('skipfails', False)
        event = EventSummaryProxy(signal.event)

        hbSource = processTALES(
            notification.content.get('hbSource'),
            skipfails,
            data
        )
        hbEventClass = processTALES(
            notification.content.get('hbEventClass'),
            skipfails,
            data
        )
        hbDescription = processTALES(
            notification.content.get('hbDescription'),
            skipfails,
            data
        )
        hbFullDescription = processTALES(
            notification.content.get('hbFullDescription'),
            skipfails,
            data
        )

        severity = EventManagerBase.severities.get(
            event.severity,
            'Unknown (%s)' % event.severity
        )
        clear = signal.clear

        payload = {
            "source": hbSource,
            "event_class": hbEventClass,
            "severity": 'Clear' if clear else severity,
            "summary": hbDescription,
            "details": hbFullDescription,
        }

        return payload

    def execute(self, notification, signal):
        url = "https://httpbin.org/post"

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        # Building out context data for TALES expressions
        data = self._signalToContextDict(signal, notification)
        actor = signal.event.occurrence[0].actor
        
        if not data.get('dev', False):
            device = None
            if actor.element_uuid:
                device = self.guidManager.getObject(actor.element_uuid)
            data['dev'] = device
            data['device'] = device

        if not data.get('component', False):
            component = None
            if actor.element_sub_uuid:
                component = self.guidManager.getObject(actor.element_sub_uuid)
            data['component'] = component

        payload = self.buildPayload(signal, notification, data)

        s = requests.Session()
        requestData = dict(
            url=url,
            headers=headers,
            data=json.dumps(payload),
        )

        try:
            request = s.post(**requestData)
        except Exception as e:
            LOG.error("Unable to send event (%s): %s" % (
                signal.event.uuid,
                e.message,
            ))

            comment = "Unable to send event (%s)" % e.message
            self.updateEvent(signal.event.uuid, comment)
            return

        if request.ok:
            LOG.info("Request to HttpBin returned: %s" % request.content)
        elif not request.ok:
            LOG.error("Unable to send event (%s): %s" % (
                signal.event.uuid,
                request.content,
            ))

            comment = "Unable to send event (%s)" % request.content
            self.updateEvent(signal.event.uuid, comment)
            return

        responseContent = request.json()
        if responseContent.get('status', False) == 'failure':
            LOG.error("Unable to send event (%s): %s" % (
                signal.event.uuid,
                request.content,
            ))

            comment = "Unable to send event (%s)" % request.content
            self.updateEvent(signal.event.uuid, comment)
            return

        status = self.statuses.get(
            str(signal.event.status),
            'Unknown (%s)' % signal.event.status
        )
        comment = "Sent to HttpBin by Notification: %s using Trigger: %s" % (
            notification.titleOrId(),
            data.get('trigger', {}).get('name', 'Unknown')
        )

        self.logEventAction(notification.titleOrId(), signal.event.uuid, status, payload)
        self.updateEvent(signal.event.uuid, comment)

        return