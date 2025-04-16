from django.core.management.base import BaseCommand
from estt_main_app.models import Diamond_times, Game, Level, Team

class Command(BaseCommand):
    help = 'Adds test diamond times for testing purposes'

    def handle(self, *args, **options):
        # Get or create test game and levels
        game, _ = Game.objects.get_or_create(game="Test Game")
        level1, _ = Level.objects.get_or_create(level_name="Level 1", game=game)
        level2, _ = Level.objects.get_or_create(level_name="Level 2", game=game)
        
        # Get the first team
        team = Team.objects.first()
        if not team:
            self.stdout.write(self.style.ERROR('No teams found. Please create a team first.'))
            return

        # Create test diamond times
        Diamond_times.objects.get_or_create(
            team=team,
            level=level1,
            defaults={'diamond_target': '01:40.000'}  # 1:40.000
        )
        
        Diamond_times.objects.get_or_create(
            team=team,
            level=level2,
            defaults={'diamond_target': '02:30.000'}  # 2:30.000
        )

        self.stdout.write(self.style.SUCCESS('Successfully added test diamond times')) 