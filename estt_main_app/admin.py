from django.contrib import admin
from .models import Team, Team_user, Game, Level, Time, Target_times, Team_game

# Register your models here.
admin.site.register(Team)
admin.site.register(Team_user)
admin.site.register(Game)
admin.site.register(Level)
admin.site.register(Time)
admin.site.register(Target_times)
admin.site.register(Team_game)