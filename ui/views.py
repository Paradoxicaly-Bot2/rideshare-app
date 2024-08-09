# -*- coding: utf-8 -*-

import datetime
import re
from datetime import timedelta
from typing import Tuple

import reverse_geocoder as rg
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from ui.models import Commute, User


def phone_format(phone_number: str) -> str:
    """Remove all non-numerical characters from the phone number."""
    return re.sub('[^0-9]', '', phone_number)


def _process_coordinates(coordinates: str) -> Tuple[float, float]:
    """Convert a string of coordinates into a tuple of floats."""
    return tuple(float(x.strip()) for x in coordinates.split(','))


WEEKDAYS_NAMES = {
    0: 'Monday',
    1: 'Tuesday',
    2: 'Wednesday',
    3: 'Thursday',
    4: 'Friday',
    5: 'Saturday',
    6: 'Sunday',
}

WORKING_DAYS = {0, 1, 2, 3, 4}


@require_GET
def welcome(request):
    """Show the welcome page."""
    return render(request, 'home.html')


@login_required
@require_GET
def new_commute(request):
    """Render the new commute creation page. """
    return render(request, 'create_commute.html')


@login_required
@require_GET
def user_home(request):
    """Render the user home page."""
    return render(request, 'user_home.html')


@require_POST
def signup(request):
    """Handle user signup."""
    first_name = request.POST.get('first')
    last_name = request.POST.get('last')
    email = request.POST.get('email')
    password = request.POST.get('password')
    contact = request.POST.get('contact', '0')

    if not all([first_name, last_name, email, password]):
        return render(request, 'home.html', context={"signup_failed": True})

    # Check if email domain is @lbschools.net
    if not email.endswith('@lbschools.net'):
        return render(request, 'home.html', context={"invalid_email_domain": True, "first_name": first_name, "last_name": last_name, "contact": contact})

    # Check if user exists
    if User.objects.filter(email=email).exists():
        return render(request, 'home.html', context={"user_already_exists": True, "first_name": first_name, "last_name": last_name, "contact": contact})

    user = User.objects.create_user(
        email=email,
        first_name=first_name,
        last_name=last_name,
        contact_number=phone_format(contact),
        password=password
    )
    user = authenticate(username=email, password=password)

    if user is not None and user.is_active:
        login(request, user)
        return HttpResponseRedirect('/user_home')

    return render(request, 'home.html')


@require_POST
def signin(request):
    """Handle user sign-in."""
    email = request.POST.get('email')
    password = request.POST.get('password')

    user = authenticate(username=email, password=password)

    if user is None:
        return render(request, 'home.html', context={"not_registered_user": True})

    if user.is_active:
        login(request, user)
        return HttpResponseRedirect('/user_home')

    return render(request, 'home.html')


@login_required
@require_POST
def save_commute(request):
    """Save a new commute or repeated commutes."""
    seats = request.POST.get('seats')
    start = request.POST.get('startPlace')
    end = request.POST.get('endPlace')
    time = request.POST.get('dateStart')
    repeat = request.POST.get('repeat')

    if '' in [start, end, time, seats]:
        return render(request, 'user_home.html', context={'successful': False})

    time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M")

    start_coordinate = _process_coordinates(start)
    end_coordinate = _process_coordinates(end)

    start_res = rg.search(start_coordinate)
    end_res = rg.search(end_coordinate)

    def create_commute_entries(repeat_interval, num_entries):
        for i in range(num_entries):
            extended_time = time + repeat_interval * i
            Commute.objects.get_or_create(
                user=request.user,
                time=extended_time,
                start_latitude=start_coordinate[0],
                start_longitude=start_coordinate[1],
                start_name=start_res[0]['name'] if start_res else None,
                end_latitude=end_coordinate[0],
                end_longitude=end_coordinate[1],
                end_name=end_res[0]['name'] if end_res else None,
                seats=seats,
            )

    if repeat == 'week':
        create_commute_entries(timedelta(days=7), 1)
    elif repeat == '2weeks':
        create_commute_entries(timedelta(days=14), 2)
    elif repeat == 'month':
        create_commute_entries(timedelta(weeks=4), 1)
    elif repeat == 'year':
        create_commute_entries(timedelta(weeks=52), 1)
    else:
        Commute.objects.get_or_create(
            user=request.user,
            time=time,
            start_latitude=start_coordinate[0],
            start_longitude=start_coordinate[1],
            start_name=start_res[0]['name'] if start_res else None,
            end_latitude=end_coordinate[0],
            end_longitude=end_coordinate[1],
            end_name=end_res[0]['name'] if end_res else None,
            seats=seats,
        )

    return render(request, 'user_home.html', context={'successful': True})


@login_required
@require_GET
def logout_view(request):
    """Log out the user."""
    logout(request)
    return HttpResponseRedirect('/')


@login_required
@require_GET
def delete_commutes(request):
    """Delete selected commutes."""
    commutes_to_delete = request.GET.getlist('commutes[]')

    for commute_id in commutes_to_delete:
        Commute.objects.filter(user=request.user, id=commute_id).delete()

    user_commutes = Commute.objects.filter(user=request.user)

    # Filter commutes to only working days
    user_commutes = [
        commute
        for commute in user_commutes
        if commute.time.weekday() in WORKING_DAYS
    ]

    return render(
        request, 'my_commutes.html',
        context={"commutes": user_commutes, "WEEKDAYS": WEEKDAYS_NAMES}
    )


@login_required
@require_GET
def search_commute(request):
    """Display the commute board."""
    now = datetime.datetime.now()
    commutes = Commute.objects.filter(
        time__gte=now,
        time__lte=now + timedelta(days=7)
    ).order_by('time')

    # Filter commutes to only working days
    commutes = [
        commute
        for commute in commutes
        if commute.time.weekday() in WORKING_DAYS
    ]

    commute_details = [
        {
            'commute': commute,
            'user': commute.user
        }
        for commute in commutes
    ]

    return render(
        request, 'search_commute.html',
        context={"commute_details": commute_details, "now": now, "WEEKDAYS": WEEKDAYS_NAMES}
    )


@login_required
@require_GET
def my_commutes(request):
    """Display the user's commutes."""
    user_commutes = Commute.objects.filter(user=request.user)

    return render(request, 'my_commutes.html', context={"commutes": user_commutes, "WEEKDAYS": WEEKDAYS_NAMES})
