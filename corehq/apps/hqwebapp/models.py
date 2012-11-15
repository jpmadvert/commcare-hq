from django.template.loader import render_to_string
from django.utils.safestring import mark_safe, mark_for_escaping
from dimagi.utils.couch.database import get_db
from dimagi.utils.decorators.memoized import memoized
from django.core.urlresolvers import reverse

class DropdownMenuItem(object):
    title = None
    view = None
    css_id = None

    def __init__(self, request, domain):
        if self.title is None:
            raise NotImplementedError("A title is required")
        if self.view is None:
            raise NotImplementedError("A view is required")
        self.request = request
        self.domain = domain

    @property
    def menu_context(self):
        return {
            'url': self.url,
            'title': mark_for_escaping(self.title),
            'css_id': self.css_id,
            'is_active': self.is_active,
            'submenu': self.submenu_items,
        }

    @property
    def submenu_items(self):
        return []

    def _format_submenu_context(self, title, url=None, html=None,
                                is_header=False, is_divider=False):
        return {
            'title': title,
            'url': url,
            'html': html,
            'is_header': is_header,
            'is_divider': is_divider,
        }

    def _format_second_level_context(self, title, url, menu):
        return {
            'title': title,
            'url': url,
            'is_second_level': True,
            'submenu': menu,
        }

    @property
    @memoized
    def url(self):
        if self.domain:
            try:
                return reverse(self.view, args=[self.domain])
            except Exception:
                pass
        return reverse(self.view)

    @property
    def is_active(self):
        return self.request.get_full_path().startswith(self.url)

    @classmethod
    def is_viewable(cls, request, domain):
        raise NotImplementedError


class ReportsMenuItem(DropdownMenuItem):
    title = "Reports"
    view = "corehq.apps.reports.views.default"
    css_id = "project_reports"

    @classmethod
    def is_viewable(cls, request, domain):
        return domain and not request.project.is_snapshot and request.couch_user.is_web_user()


class ProjectInfoMenuItem(DropdownMenuItem):
    title = "Project Info"
    view = "corehq.apps.appstore.views.project_info"
    css_id = "project_info"

    @classmethod
    def is_viewable(cls, request, domain):
        return domain and request.project.is_snapshot


class ManageDataMenuItem(DropdownMenuItem):
    title = "Manage Data"
    view = "corehq.apps.data_interfaces.views.default"
    css_id = "manage_data"

    @classmethod
    def is_viewable(cls, request, domain):
        return domain and request.couch_user.can_edit_data()


class ApplicationsMenuItem(DropdownMenuItem):
    title = "Applications"
    view = "corehq.apps.app_manager.views.default"
    css_id = "applications"

    @property
    @memoized
    def submenu_items(self):
        # todo async refresh submenu when on the applications page and you change the application name
        key = [self.domain]
        apps = get_db().view('app_manager/applications_brief',
            reduce=False,
            startkey=key,
            endkey=key+[{}],
        ).all()
        submenu_context = []
        if not apps:
            return submenu_context

        submenu_context.append(self._format_submenu_context('My Applications', is_header=True))
        for app in apps:
            app_info = app['value']
            if app_info:
                url = reverse('view_app', args=[self.domain, app_info['_id']])
                app_name = mark_safe("%s" % mark_for_escaping(app_info['name']))
                submenu_context.append(self._format_submenu_context(app_name, url=url))

        if self.request.couch_user.can_edit_apps():
            submenu_context.append(self._format_submenu_context(None, is_divider=True))
            newapp_options = [
                self._format_submenu_context(None, html=self._new_app_link('Blank Application')),
                self._format_submenu_context(None, html=self._new_app_link('RemoteApp (Advanced Users Only)',
                    is_remote=True)),
            ]
            if self.request.couch_user.is_previewer():
                newapp_options.append(self._format_submenu_context('Visit CommCare Exchange to copy existing app...',
                    url=reverse('appstore')))
            submenu_context.append(self._format_second_level_context(
                'New Application...',
                '#',
                newapp_options
            ))
        return submenu_context

    def _new_app_link(self, title, is_remote=False):
        template = "app_manager/partials/new_app_link.html"
        return mark_safe(render_to_string(template, {
            'domain': self.domain,
            'is_remote': is_remote,
            'action_text': title,
        }))

    @classmethod
    def is_viewable(cls, request, domain):
        return (domain is not None and request.couch_user.is_web_user() and
                (request.couch_user.is_member_of(domain) or request.couch_user.is_superuser))


class CloudcareMenuItem(DropdownMenuItem):
    title = "CloudCare"
    view = "corehq.apps.cloudcare.views.default"
    css_id = "cloudcare"

    @classmethod
    def is_viewable(cls, request, domain):
        return domain and request.couch_user.can_edit_data()


class MessagesMenuItem(DropdownMenuItem):
    title = "Messages"
    view = "corehq.apps.sms.views.messaging"
    css_id = "messages"

    @classmethod
    def is_viewable(cls, request, domain):
        return domain and request.project.is_snapshot


class ProjectSettingsMenuItem(DropdownMenuItem):
    title = "Settings & Users"
    view = "corehq.apps.settings.views.default"
    css_id = "project_settings"

    @property
    @memoized
    def submenu_items(self):
        return []

    @classmethod
    def is_viewable(cls, request, domain):
        return (domain is not None
                and (request.couch_user.can_edit_commcare_users() or request.couch_user.can_edit_web_users()))


class AdminReportsMenuItem(DropdownMenuItem):
    title = "Admin"
    view = "corehq.apps.hqadmin.views.default"
    css_id = "admin_tab"

    @property
    @memoized
    def submenu_items(self):
        submenu_context = [
            self._format_submenu_context("Reports", is_header=True),
            self._format_submenu_context("Admin Reports", url=reverse("default_admin_report")),
            self._format_submenu_context("System Info", url=reverse("system_info")),
            self._format_submenu_context("Management", is_header=True),
            self._format_submenu_context(mark_for_escaping("ADM Reports & Columns"),
                url=reverse("default_adm_admin_interface")),
#            self._format_submenu_context(mark_for_escaping("HQ Announcements"),
#                url=reverse("default_announcement_admin")),
        ]
        try:
            submenu_context.append(self._format_submenu_context(mark_for_escaping("Billing"),
                url=reverse("billing_default")))
        except Exception:
            pass
        submenu_context.extend([
            self._format_submenu_context(None, is_divider=True),
            self._format_submenu_context("Django Admin", url="/admin")
        ])
        return submenu_context

    @classmethod
    def is_viewable(cls, request, domain):
        return request.couch_user.is_superuser
