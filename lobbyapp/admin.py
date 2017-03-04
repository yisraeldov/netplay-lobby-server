from django.contrib import admin
from models import *

class EntryAdmin(admin.ModelAdmin):
  pass

admin.site.site_header = 'Lobby Administration'
admin.site.register(Entry, EntryAdmin)
