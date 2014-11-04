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

from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from timesketch.apps.acl.models import AccessControlEntry
from timesketch.apps.sketch.models import Sketch
from timesketch.apps.sketch.models import SketchTimeline
from timesketch.apps.sketch.models import Timeline
from timesketch.apps.sketch.models import SavedView

from django.views.generic import TemplateView
from django.views.generic import DetailView
from django.views.generic import CreateView
from django.contrib.contenttypes.models import ContentType
from django.utils.decorators import method_decorator


class LoginRequiredMixin(object):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
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
            _sketch = ace.content_object
            # Don't include the users own sketches
            if not _sketch.user == self.request.user:
                result.add(_sketch)
        return result

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['my_sketches'] = Sketch.objects.filter(
            user=self.request.user).order_by('-created')
        context['shared_sketches'] = self._get_shared_sketches()
        return context


class SketchView(LoginRequiredMixin, DetailView):
    """
    Renders the sketch overview page.
    """
    model = Sketch


class SketchDetailView(SketchView):
    def get_context_data(self, **kwargs):
        context = super(SketchDetailView, self).get_context_data(**kwargs)
        context['views'] = SavedView.objects.filter(
            sketch=self.object).exclude(name="").order_by("created")
        return context


class SketchCreateView(LoginRequiredMixin, CreateView):
    model = Sketch
    fields = ['title', 'description']

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super(SketchCreateView, self).form_valid(form)


@login_required
def add_timeline(request, sketch_id):
    """Add timeline to sketch."""
    sketch = Sketch.objects.get(id=sketch_id)
    if request.method == 'POST':
        form_timelines = request.POST.getlist('timelines')
        if form_timelines:
            for timeline_id in form_timelines:
                t = Timeline.objects.get(id=timeline_id)
                sketch_timeline = SketchTimeline.objects.create(timeline=t)
                sketch_timeline.color = sketch_timeline.generate_color()
                sketch_timeline.save()
                sketch.timelines.add(sketch_timeline)
                sketch.save()
        return redirect("/sketch/%s/timelines/" % sketch.id)
    timelines = set()
    for timeline in Timeline.objects.all():
        if not timeline in [x.timeline for x in sketch.timelines.all()]:
            if timeline.can_read(request.user):
                timelines.add(timeline)
    return render(request, 'add_timeline.html', {'sketch': sketch,
                                                 'timelines': timelines})


@login_required
def explore(request, sketch_id):
    """Renders the search interface."""
    sketch = Sketch.objects.get(id=sketch_id)
    view = request.GET.get('view', 0)
    timelines = [t.timeline.datastore_index for t in sketch.timelines.all()]
    timelines = ",".join(timelines)
    context = {"timelines": timelines, "sketch": sketch, "view": view}
    return render(request, 'explore.html', context)


@login_required
def edit_timeline(request, sketch_id, timeline_id):
    """Edit timeline."""
    sketch = Sketch.objects.get(id=sketch_id)
    timeline = SketchTimeline.objects.get(id=timeline_id)
    if request.method == 'POST':
        color_in_hex = request.POST.get('color').replace('#', '')[:6]
        if re.match("[0-9a-fA-F]{3,6}", color_in_hex):
            timeline.color = color_in_hex
            timeline.save()
        return redirect('/sketch/%s/timelines/' % sketch.id)
    return render(
        request, 'edit_timeline.html', {'sketch': sketch, 'timeline': timeline})


@login_required
def search_sketches(request):
    """Search sketches."""
    result = set()
    if request.method == 'POST':
        q = request.POST['search']
        if q:
            for sketch in Sketch.objects.filter(Q(title__icontains=q) |
                                                Q(description__icontains=q)):
                if sketch.can_read(request.user):
                    result.add(sketch)
    return render(request, 'search.html', {'result': result})


@login_required
def settings_sharing(request, sketch_id):
    """Set sharing options."""
    sketch = Sketch.objects.get(id=sketch_id)
    if request.method == 'POST':
        permission = request.POST.getlist('optionsPermission')[0]
        if permission == "public":
            sketch.make_public(request.user)
        else:
            sketch.make_private(request.user)
    return redirect("/sketch/%i/" % sketch.id)
