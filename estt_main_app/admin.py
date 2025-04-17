from django.contrib import admin
from .models import Team, Team_user, Game, Level, Time, Target_times, Team_game, Organization, Org_user, Org_team, Org_join_code, GameSuggestion, Diamond_times

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
admin.site.register(Diamond_times)

@admin.register(GameSuggestion)
class GameSuggestionAdmin(admin.ModelAdmin):
    list_display = ('game_name', 'suggested_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('game_name', 'suggested_by__username')
    readonly_fields = ('created_at',)

    def log_addition(self, request, object, message):
        # Don't log additions
        pass

    def log_change(self, request, object, message):
        # Don't log changes
        pass

    def log_deletion(self, request, object, object_repr):
        # Don't log deletions
        pass
