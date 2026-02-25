"""
Custom admin site configuration for Exam Stellar.

Provides a professional, styled admin interface with custom branding.
"""

from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _


class ExamStellarAdminSite(AdminSite):
    """
    Custom admin site for Exam Stellar with professional branding.
    """
    site_header = _("Exam Stellar Administration")
    site_title = _("Exam Stellar Admin")
    index_title = _("Welcome to Exam Stellar Administration")


# Create custom admin site instance
exam_stellar_admin = ExamStellarAdminSite(name='exam_stellar_admin')

