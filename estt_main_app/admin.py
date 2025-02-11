from django.contrib import admin
from .models import Team, Team_user, Game, Level, Time, Target_times, Team_game, Organization, Org_user, Org_team, Org_join_code

# Register your models here.
admin.site.register(Team)
admin.site.register(Team_user)
admin.site.register(Game)
admin.site.register(Level)
admin.site.register(Time)
admin.site.register(Target_times)
admin.site.register(Team_game)
admin.site.register(Organization)
admin.site.register(Org_team)
admin.site.register(Org_user)
admin.site.register(Org_join_code)