from django.core.management.base import BaseCommand
from estt_main_app.models import Diamond_times, Game, Level, Team

class Command(BaseCommand):
    help = 'Adds test diamond times for testing purposes'

    def handle(self, *args, **options):
        # Get or create MK8 game
        game, _ = Game.objects.get_or_create(game='Mario Kart 8 Deluxe')
        
        # Get the first team
        team = Team.objects.first()
        if not team:
            self.stdout.write(self.style.ERROR('No teams found. Please create a team first.'))
            return

        # Define levels and their diamond times
        level_times = {
            "Mario Kart Stadium": "01:42.119",
            "Water Park": "01:45.258", 
            "Sweet Sweet Canyon": "01:50.373",
            "Thwomp Ruins": "01:55.250"
        }

        # Create diamond times for each level
        for level_name, time in level_times.items():
            level = Level.objects.filter(game=game, level_name=level_name).first()
            if level:
                Diamond_times.objects.get_or_create(
                    team=team,
                    level=level,
                    defaults={'diamond_target': time}
                )
                self.stdout.write(f'Added diamond time for {level_name}: {time}')
            else:
                self.stdout.write(self.style.WARNING(f'Level not found: {level_name}'))

        self.stdout.write(self.style.SUCCESS('Successfully added test diamond times')) 