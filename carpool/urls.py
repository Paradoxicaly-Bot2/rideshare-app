# -*- coding: utf-8 -*-

"""URL routes for the CarPool web application."""

from django.urls import path
from django.contrib import admin

from ui.views import (
    logout_view, my_commutes, new_commute, save_commute, search_commute, signin, signup, user_home,
    welcome, delete_commutes
)

admin.autodiscover()

urlpatterns = [
    path('', welcome, name='home'),  # Updated name to 'home'
    path('new_commute/', new_commute, name='new_commute'),
    path('user_home/', user_home, name='user_home'),
    path('signup/', signup, name='signup'),
    path('login/', signin, name='login'),
    path('save_commute/', save_commute, name='save_commute'),
    path('logout/', logout_view, name='logout'),
    path('search_commute/', search_commute, name='search_commute'),
    path('my_commutes/', my_commutes, name='my_commutes'),
    path('delete_commutes/', delete_commutes, name='delete_commutes'),
    path('admin/', admin.site.urls),
]