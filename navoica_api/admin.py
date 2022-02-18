# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .models import CareerModel
from django.contrib import admin
from django.db import models
from django import forms


@admin.register(CareerModel)
class AuthorAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.CharField: {'widget': forms.Textarea(attrs={'rows': 8, 'cols': 100})},
    }
