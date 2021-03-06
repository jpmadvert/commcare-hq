from __future__ import absolute_import
from __future__ import unicode_literals
from datetime import datetime


def utcnow():
    """
    Defined here to do patching in tests.
    """
    return datetime.utcnow()


def domain_has_reminders(domain):
    from corehq.apps.data_interfaces.models import AutomaticUpdateRule
    from corehq.apps.reminders.models import CaseReminderHandler
    from corehq.messaging.scheduling.models import ScheduledBroadcast, ImmediateBroadcast

    return (
        AutomaticUpdateRule.domain_has_conditional_alerts(domain) or
        ScheduledBroadcast.domain_has_broadcasts(domain) or
        ImmediateBroadcast.domain_has_broadcasts(domain) or
        CaseReminderHandler.domain_has_reminders(domain)
    )
