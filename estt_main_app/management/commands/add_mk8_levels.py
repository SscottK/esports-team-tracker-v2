from django.core.management.base import BaseCommand
from estt_main_app.models import Game, Level

class Command(BaseCommand):
    help = 'Adds Mario Kart 8 levels to the database'

    def handle(self, *args, **options):
        # Get or create the game
        game, _ = Game.objects.get_or_create(game='Mario Kart 8 Deluxe')
        
        # Define all levels
        mk8_levels = [
            # Mushroom Cup
            "Mario Kart Stadium",
            "Water Park",
            "Sweet Sweet Canyon",
            "Thwomp Ruins",
            
            # Flower Cup
            "Mario Circuit",
            "Toad Harbor",
            "Twisted Mansion",
            "Shy Guy Falls",
            
            # Star Cup
            "Sunshine Airport",
            "Dolphin Shoals",
            "Electrodrome",
            "Mount Wario",
            
            # Special Cup
            "Cloudtop Cruise",
            "Bone-Dry Dunes",
            "Wii U Bowser's Castle",
            "Wii U Rainbow Road",
            
            # Egg Cup
            "Yoshi Circuit",
            "Excitebike Arena",
            "Dragon Driftway",
            "Mute City",
            
            # Crossing Cup
            "Baby Park",
            "Cheese Land",
            "Wild Woods",
            "Animal Crossing",
            
            # Shell Cup
            "Moo Moo Meadows",
            "GBA Mario Circuit",
            "Cheep Cheep Beach",
            "Toad's Turnpike",
            
            # Banana Cup
            "Dry Dry Desert",
            "Donut Plains 3",
            "Royal Raceway",
            "DK Jungle",
            
            # Leaf Cup
            "DS Wario Stadium",
            "GCN Sherbert Land",
            "Music Park",
            "Yoshi Valley",
            
            # Lightning Cup
            "Tick-Tock Clock",
            "Piranha Plant Slide",
            "Grumble Volcano",
            "N64 Rainbow Road",
            
            # Triforce Cup
            "Wario's Gold Mine",
            "SNES Rainbow Road",
            "Ice Ice Outpost",
            "Hyrule Circuit",
            
            # Bell Cup
            "Neo Bowser City",
            "Ribbon Road",
            "Super Bell Subway",
            "Big Blue"
        ]
        
        # Add levels
        levels_added = 0
        for level_name in mk8_levels:
            level, created = Level.objects.get_or_create(
                game=game,
                level_name=level_name
            )
            if created:
                levels_added += 1
                self.stdout.write(f'Added level: {level_name}')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully added {levels_added} new levels')) 