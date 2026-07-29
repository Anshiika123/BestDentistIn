"""
Clinic notification hook. Currently a no-op — logs are the only "notification"
a clinic gets today (they'd need to check /portal/ or Django admin). Wire this
up to real delivery in a later phase:

  - Email: django.core.mail.send_mail (SMTP or a provider like SES/Postmark)
  - SMS/WhatsApp: WhatsApp Business API or an SMS gateway (Twilio, MSG91, etc.)
  - Push: a mobile app / web push subscription tied to ClinicUser

Kept as an explicit function (not inline in the view) so swapping the delivery
channel later doesn't touch apps.leads.views.
"""

import logging

logger = logging.getLogger("bestdentistin.leads")


def notify_clinic_of_lead(lead):
    logger.info(
        "New %s lead for clinic #%s (%s) from %s/%s",
        lead.cta_type,
        lead.clinic_id,
        lead.clinic.name,
        lead.page_source,
        lead.page_slug or "-",
    )
