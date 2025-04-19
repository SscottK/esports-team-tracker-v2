from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

#Team modle
class Team(models.Model):
    
    #Team Name
    name = models.CharField(max_length=50)

    #what it will return when being printed
    def __str__(self):
        return self.name
    


#team user moel
class Team_user(models.Model):

    #the user being added to a team
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    #the tema a user is being added to
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    #is this user a coach for this team or no
    isCoach = models.BooleanField(default=False)

    #what it will return when being printed
    def __str__(self):
        
        return self.user.username
    

#game model
class Game(models.Model):

    #Game Title
    game = models.CharField(max_length=50)

    #what it will return when being printed
    def __str__(self):
        return self.game
    

#level model
class Level(models.Model):

    #the game the level belongs to
    game = models.ForeignKey(Game, on_delete=models.CASCADE)

    #the name of the level
    level_name = models.CharField(max_length=50)

    #what it will return when being printed
    def __str__(self):
        return self.level_name
    
#Player times
class Time(models.Model):

    #The user the time belongs to
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    #The level the time is for
    level = models.ForeignKey(Level, on_delete=models.CASCADE)

    #the time for the level formated as 00:00.000
    time = models.CharField(max_length=9)

    #what it will return when being printed
    def __str__(self):
        rtrn_strng = self.user.username + ", " + self.level.level_name + ", " + self.time
        return rtrn_strng
    

#Target Times for each level per team
class Target_times(models.Model):

    #The level the target times are for
    level = models.ForeignKey(Level, on_delete=models.CASCADE)

    #the Team the target times affect
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    #The fastest target time
    high_target = models.CharField(max_length=9)

    #The slowest target time
    low_target = models.CharField(max_length=9)

    #what it will return when being printed
    def __str__(self):
        rtrn_strng = "Target Times for " + self.team.name + ", " + self.level.level_name
        return rtrn_strng
    

#team game for each game a team plays
class Team_game(models.Model):

    #the team the record is being created for    
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    #the game the team plays
    game = models.ForeignKey(Game, on_delete=models.CASCADE)

    #what it will return when being printed
    def __str__(self):
        rtrn_strng = self.game.game + ", " + self.team.name
        return rtrn_strng
    

#org model
class Organization(models.Model):

    #Org Name
    name = models.CharField(max_length=50)
    
    #Creation date
    created_at = models.DateTimeField(default=timezone.now)

    #what it will return when being printed
    def __str__(self):
        return self.name
    

#org team for each org a team plays under
class Org_team(models.Model):

    #the team the record is being created for
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    #the org the team is under
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)

    #what it will return when being printed
    def __str__(self):
        rtrn_strng = self.org.name + ", " + self.team.name
        return rtrn_strng
    

    
#org user for each game a team plays
class Org_user(models.Model):

    #the user that is in the org
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    #the org the user is in
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.org.name}"


#org join code
class Org_join_code(models.Model):
    
    #the code randomly generated to be added to an org
    code = models.CharField(max_length=20)

    #the org that code if for
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)

class GameSuggestion(models.Model):
    game_name = models.CharField(max_length=255, unique=True)
    suggested_by = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.game_name

#Diamond Times for each level per team
class Diamond_times(models.Model):
    #The level the diamond time is for
    level = models.ForeignKey(Level, on_delete=models.CASCADE)

    #the Team the diamond time affects
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    #The diamond target time
    diamond_target = models.CharField(max_length=9)

    #what it will return when being printed
    def __str__(self):
        return f"Diamond Time for {self.team.name}, {self.level.level_name}"

    class Meta:
        unique_together = ('level', 'team')  # Only one diamond time per level per team

class Org_leader(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'org')
        verbose_name = 'Organization Leader'
        verbose_name_plural = 'Organization Leaders'

    def __str__(self):
        return f"{self.user.username} - {self.org.name} Leader"