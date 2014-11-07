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
"""This module implements timesketch Django views."""

import re

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.views.generic import TemplateView
from django.views.generic import DetailView
from django.views.generic import CreateView
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.shortcuts import redirect

from django.http import HttpResponseForbidden

from timesketch.apps.acl.models import AccessControlEntry
from timesketch.apps.sketch.models import Sketch
from timesketch.apps.sketch.models import SketchTimeline
from timesketch.apps.sketch.models import Timeline
from timesketch.apps.sketch.models import SavedView


class LoginRequiredMixin(object):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        try:
            if not self.get_object().can_read(self.request.user):
                return HttpResponseForbidden()
        except AttributeError:
            pass
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)


class HomeView(LoginRequiredMixin, TemplateView):
    """
    Renders the landing page for the user.
    """
    template_name = 'home.html'

    def _get_shared_sketches(self):
        """
        Get sketches that has been shared to the user.

        Returns:
            A set() of timesketch.apps.sketch.models.Sketch instances
        """
        content_type = ContentType.objects.get_for_model(Sketch)
        ace_entries = AccessControlEntry.objects.filter(
            content_type=content_type, user=self.request.user,
            permission_read=True).order_by('-created')
        result = set()
        for ace in ace_entries:
            sketch = ace.content_object
            # Don't include the users own sketches
            if not sketch.user == self.request.user:
                result.add(sketch)
        return result

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['my_sketches'] = Sketch.objects.filter(
            user=self.request.user).order_by('-created')
        context['shared_sketches'] = self._get_shared_sketches()
        return context


class SketchDetailView(LoginRequiredMixin, DetailView):
    model = Sketch


class SketchCreateView(LoginRequiredMixin, CreateView):
    model = Sketch
    fields = ['title', 'description']

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super(SketchCreateView, self).form_valid(form)


class SketchTimelineCreateView(LoginRequiredMixin, TemplateView):
    template_name = 'add_timeline.html'

    def _get_timelines(self, sketch):
        timelines = set()
        for timeline in Timeline.objects.all():
            if not timeline in [x.timeline for x in sketch.timelines.all()]:
                if timeline.can_read(self.request.user):
                    timelines.add(timeline)
        return timelines

    def get_context_data(self, **kwargs):
        context = super(SketchTimelineCreateView, self).get_context_data(**kwargs)
        sketch = Sketch.objects.get(pk=kwargs['sketch'])
        context['sketch'] = sketch
        context['timelines'] = self._get_timelines(sketch)
        return context

    def post(self, request, *args, **kwargs):
        sketch = Sketch.objects.get(pk=kwargs['sketch'])
        timelines = request.POST.getlist('timelines')
        if timelines:
            for timeline_id in timelines:
                timeline = Timeline.objects.get(id=timeline_id)
                sketch_timeline = SketchTimeline.objects.create(
                    timeline=timeline)
                sketch_timeline.color = sketch_timeline.generate_color()
                sketch_timeline.save()
                sketch.timelines.add(sketch_timeline)
                sketch.save()
        return redirect('/sketch/%s/timelines/' % sketch.id)


class SketchTimelineUpdateView(LoginRequiredMixin, DetailView):
    model = Sketch
    template_name = 'edit_timeline.html'

    #def get_object(self):
    #    pk = self.kwargs.get('sketch', None)
    #    return Sketch.objects.get(pk=pk)

    def get_context_data(self, **kwargs):
        context = super(SketchTimelineUpdateView, self).get_context_data(**kwargs)
        sketch = self.get_object()
        context['sketch'] = sketch
        context['timeline'] = SketchTimeline.objects.get(pk=self.kwargs['timeline'])
        return context

    def post(self, request, *args, **kwargs):
        sketch = self.get_object()
        timeline = SketchTimeline.objects.get(pk=kwargs['timeline'])
        color_in_hex = request.POST.get('color').replace('#', '')[:6]
        if re.match("[0-9a-fA-F]{3,6}", color_in_hex):
            timeline.color = color_in_hex
            timeline.save()
        return redirect('/sketch/%s/timelines/' % sketch.id)


class SketchExploreView(LoginRequiredMixin, DetailView):
    model = Sketch

    def get_context_data(self, **kwargs):
        context = super(SketchExploreView, self).get_context_data(**kwargs)
        sketch = self.object
        timelines = [t.timeline.datastore_index for t in sketch.timelines.all()]
        timelines = ",".join(timelines)
        context['sketch'] = sketch
        context['timelines'] = timelines
        context['view'] = self.request.GET.get('view', 0)
        return context


class SearchSketchView(LoginRequiredMixin, TemplateView):
    template_name = 'search.html'

    def get_context_data(self, **kwargs):
        context = super(SearchSketchView, self).get_context_data(**kwargs)
        query = self.request.GET['query']
        result = set()
        if query:
            for sketch in Sketch.objects.filter(
                    Q(title__icontains=query) |
                    Q(description__icontains=query)):
                if sketch.can_read(self.request.user):
                    result.add(sketch)
        context['result'] = result
        return context


class SketchSettingsAclView(LoginRequiredMixin, DetailView):
    model = Sketch

    def post(self, request, *args, **kwargs):
        sketch = self.get_object()
        permission = request.POST.getlist('optionsPermission')[0]
        if permission == "public":
            sketch.make_public(request.user)
        else:
            sketch.make_private(request.user)
        return redirect('/sketch/%i/' % sketch.id)
