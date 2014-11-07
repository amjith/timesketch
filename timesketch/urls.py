# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Django URL routes"""

from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from tastypie.api import Api
from django.conf.urls.static import static

from timesketch.apps.api import v1_resources
from timesketch.apps.ui.views import HomeView
from timesketch.apps.ui.views import SketchView
from timesketch.apps.ui.views import SketchDetailView
from timesketch.apps.ui.views import SketchCreateView
from timesketch.apps.ui.views import SketchExploreView
from timesketch.apps.ui.views import SketchTimelineUpdateView
from timesketch.apps.ui.views import SketchTimelineCreateView
from timesketch.apps.ui.views import SketchSettingsAclView
from timesketch.apps.ui.views import SearchSketchView

from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required


v1_api = Api(api_name='v1')
v1_api.register(v1_resources.SearchResource())
v1_api.register(v1_resources.EventResource())
v1_api.register(v1_resources.CommentResource())
v1_api.register(v1_resources.LabelResource())
v1_api.register(v1_resources.ViewResource())
v1_api.register(v1_resources.SketchTimelineResource())
v1_api.register(v1_resources.SketchAclResource())
v1_api.register(v1_resources.SketchResource())
v1_api.register(v1_resources.UserResource())
v1_api.register(v1_resources.UserProfileResource())

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),

    # Views
    url(r'^$', HomeView.as_view(), name='home'),

    url(r'^sketch/(?P<pk>\d+)/$', SketchDetailView.as_view(
        template_name='sketch.html'), name='sketch'),

    url(r'^sketch/(?P<pk>\d+)/views/$', SketchDetailView.as_view(
        template_name='views.html'), name='sketch-views'),

    url(r'^sketch/(?P<pk>\d+)/timelines/$', SketchView.as_view(
        template_name='timelines.html'), name='sketch-timelines'),

    url(r'^sketch/(?P<pk>\d+)/settings/$', SketchView.as_view(
        template_name='settings.html'), name='sketch-settings'),

    url(r'^sketch/(?P<sketch>\d+)/settings/sharing/$',
        SketchSettingsAclView.as_view(), name='sketch-settings-acl'),

    url(r'^sketch/add/$', SketchCreateView.as_view(
        template_name='add_sketch.html'), name='add-sketch'),

    url(r'^sketch/(?P<pk>\d+)/explore/event/', login_required(
        TemplateView.as_view(template_name="event.html")), name='event'),

    url(r'^sketch/(?P<pk>\d+)/explore/',
        SketchExploreView.as_view(), name='explore'),

    url(r'^user/profile/$', login_required(TemplateView.as_view(
        template_name='profile.html')), name='user-profile'),

    url(r'^sketch/(?P<sketch>\d+)/timelines/(?P<timeline>\d+)/$',
        SketchTimelineUpdateView.as_view(), name='sketch-edit-timeline'),

    url(r'^sketch/(?P<sketch>\d+)/timelines/add/$',
        SketchTimelineCreateView.as_view(), name='sketch-add-timeline'),

    url(r'^search/$', SearchSketchView.as_view(), name='search-sketch'),

    # API
    (r'^api/', include(v1_api.urls)),

    # Login/Logout
    url('^accounts/', include('django.contrib.auth.urls')),

)

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
