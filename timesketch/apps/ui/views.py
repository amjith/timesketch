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
# ToDo: Refactor this to class based views (see github issue #22)

import re

from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from timesketch.apps.sketch.models import Sketch
from timesketch.apps.sketch.models import SketchTimeline
from timesketch.apps.sketch.models import Timeline
from timesketch.apps.sketch.models import SavedView


@login_required
def home(request):
    """Renders the available sketches for the user."""
    my_sketches = Sketch.objects.filter(user=request.user).order_by("-created")
    public_sketches = set()
    for sketch in Sketch.objects.all().exclude(user=request.user):
        if sketch.is_public():
            public_sketches.add(sketch)
    context = {"my_sketches": my_sketches, "public_sketches": public_sketches}
    return render(request, 'home.html', context)


@login_required
def sketch(request, sketch_id):
    """Renders specific sketch."""  
    sketch = Sketch.objects.get(id=sketch_id)
    if not sketch.can_read(request.user):
        return HttpResponseForbidden()
    saved_views = SavedView.objects.filter(sketch=sketch).exclude(
        name="").order_by("created")
    context = {"sketch": sketch, "views": saved_views}
    return render(request, 'sketch.html', context)


@login_required
def new_sketch(request):
    """Create new sketch."""
    if request.method == 'POST':
        title = request.POST.get('inputTitle')
        description = request.POST.get('inputDescription')
        obj, created = Sketch.objects.get_or_create(title=title,
                                                    description=description,
                                                    user=request.user)
        return redirect("/sketch/%s/" % obj.id)
    return render(request, 'new_sketch.html', {})


@login_required
def add_timeline(request, sketch_id):
    """Add timeline to sketch."""
    sketch = Sketch.objects.get(id=sketch_id)
    if request.method == 'POST':
        form_timelines = request.POST.getlist('timelines')
        if form_timelines:
            for timeline_id in form_timelines:
                timeline = Timeline.objects.get(id=timeline_id)
                sketch_timeline = SketchTimeline.objects.create(
                    timeline=timeline, sketch=sketch, user=request.user)
                sketch_timeline.color = sketch_timeline.generate_color()
                sketch_timeline.save()
        return redirect("/sketch/%s/timelines/" % sketch.id)
    timelines = set()
    for timeline in Timeline.objects.all():
        if not timeline in [x.timeline for x in sketch.timelines.all()]:
            if timeline.can_read(request.user):
                timelines.add(timeline)
    return render(request, 'add_timeline.html', {'sketch': sketch,
                                                 'timelines': timelines})


@login_required
def views(request, sketch_id):
    """List of all saved views in a specific sketch."""
    sketch = Sketch.objects.get(id=sketch_id)
    views = SavedView.objects.filter(sketch=sketch).exclude(
        name="").order_by("created")
    context = {"sketch": sketch, "views": views}
    return render(request, 'views.html', context)


@login_required
def timelines(request, sketch_id):
    """List of all timelines in a specific sketch."""
    sketch = Sketch.objects.get(id=sketch_id)
    timelines = Timeline.objects.all()
    context = {"sketch": sketch, "timelines": timelines}
    return render(request, 'timelines.html', context)


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
def event(request, index_id, event_id):
    """Renders the event page. This is used for ng-include in the tamplates."""
    context = {"index_id": index_id, "event_id": event_id}
    return render(request, 'event.html', context)


@login_required
def user_profile(request):
    """Profile for the user."""
    return render(request, 'profile.html', {})

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
def settings(request, sketch_id):
    """Settings for a sketch."""
    sketch = Sketch.objects.get(id=sketch_id)
    context = {"sketch": sketch}
    return render(request, 'settings.html', context)


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
