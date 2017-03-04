from django.contrib import admin
from models import *

class EntryAdmin(admin.ModelAdmin):
  pass

class LogEntryAdmin(admin.ModelAdmin):
  def save_model(self, request, obj, form, change):
    # ignore changes to log entries
    pass

admin.site.site_header = 'Lobby Administration'
admin.site.register(Entry, EntryAdmin)
admin.site.register(LogEntry, LogEntryAdmin)
