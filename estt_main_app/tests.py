from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Organization, Org_user, Team, Team_user, Game, Level, Time, Team_game, Org_join_code
from io import StringIO
import csv
import json

class UserAuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.user.is_active = True
        self.user.save()

    def test_user_login(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Should redirect after successful login

    def test_user_signup(self):
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'password1': 'newpass123',
            'password2': 'newpass123'
        })
        self.assertEqual(response.status_code, 302)  # Should redirect after successful signup
        self.assertTrue(User.objects.filter(username='newuser').exists())

class OrganizationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.user.is_active = True
        self.user.save()
        self.client.login(username='testuser', password='testpass123')
        self.org = Organization.objects.create(name='Test Org')
        Org_user.objects.create(user=self.user, org=self.org)

    def test_create_organization(self):
        response = self.client.post(reverse('new-org'), {
            'name': 'Test Org',
            'description': 'Test Description'
        })
        self.assertEqual(response.status_code, 302)  # Should redirect after successful creation
        self.assertTrue(Organization.objects.filter(name='Test Org').exists())

    def test_join_organization(self):
        # Create an organization and join code
        org = Organization.objects.create(name='Test Org')
        join_code = Org_join_code.objects.create(
            code='TEST123',
            org=org
        )
        
        # Create a new user to join
        new_user = User.objects.create_user(
            username='newuser',
            password='newpass123'
        )
        new_user.is_active = True
        new_user.save()
        
        # Login as new user
        self.client.login(username='newuser', password='newpass123')
        
        # Join organization
        response = self.client.post(reverse('create-org-user', args=['TEST123']))
        self.assertEqual(response.status_code, 302)  # Should redirect after successful join
        self.assertTrue(Org_user.objects.filter(user=new_user, org=org).exists())

    def test_organization_permissions(self):
        # Create a new user
        new_user = User.objects.create_user(
            username='newuser',
            password='newpass123'
        )
        new_user.is_active = True
        new_user.save()
        
        # Try to access organization as non-member
        self.client.login(username='newuser', password='newpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)  # Should be allowed to access dashboard
        
        # Add user to organization
        Org_user.objects.create(user=new_user, org=self.org)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)  # Should still be allowed

    def test_organization_join_code_expiration(self):
        # Create a join code
        join_code = Org_join_code.objects.create(
            code='TEST123',
            org=self.org
        )
        
        # Verify code is valid
        response = self.client.post(reverse('create-org-user', args=['TEST123']))
        self.assertEqual(response.status_code, 302)
        
        # Try to use same code again
        response = self.client.post(reverse('create-org-user', args=['TEST123']))
        self.assertEqual(response.status_code, 302)  # Should redirect to join-org page
        self.assertEqual(Org_user.objects.filter(user=self.user).count(), 1)  # Should only have one membership

class TeamTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.user.is_active = True
        self.user.save()
        self.client.login(username='testuser', password='testpass123')
        
        # Create organization
        self.org = Organization.objects.create(name='Test Org')
        Org_user.objects.create(user=self.user, org=self.org)

    def test_create_team(self):
        response = self.client.post(reverse('new-team'), {
            'name': 'Test Team',
            'description': 'Test Description'
        })
        self.assertEqual(response.status_code, 302)  # Should redirect after successful creation
        self.assertTrue(Team.objects.filter(name='Test Team').exists())

    def test_add_team_member(self):
        # Create a team
        team = Team.objects.create(name='Test Team')
        Team_user.objects.create(
            team=team,
            user=self.user,
            isCoach=True
        )
        
        # Create a new user to add
        new_user = User.objects.create_user(
            username='newuser',
            password='newpass123'
        )
        new_user.is_active = True
        new_user.save()
        
        # Add user to team
        response = self.client.post(reverse('add_team_member', args=[self.org.id, team.id]), {
            'user': new_user.id,
            'is_coach': 'false'
        })
        self.assertEqual(response.status_code, 302)  # Should redirect after successful addition
        self.assertTrue(Team_user.objects.filter(team=team, user=new_user).exists())

class TimeTrackingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.user.is_active = True
        self.user.save()
        self.client.login(username='testuser', password='testpass123')
        
        # Create organization and team
        self.org = Organization.objects.create(name='Test Org')
        Org_user.objects.create(user=self.user, org=self.org)
        self.team = Team.objects.create(name='Test Team')
        Team_user.objects.create(
            team=self.team,
            user=self.user,
            isCoach=True
        )
        
        # Create game and level
        self.game = Game.objects.create(game='Mario Kart 8')
        self.level = Level.objects.create(
            level_name='Test Level',
            game=self.game
        )
        Team_game.objects.create(
            team=self.team,
            game=self.game
        )

    def test_add_time(self):
        response = self.client.post(reverse('add-time'), {
            'level': self.level.id,
            'game': self.game.id,
            'time': '01:23.456'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Time.objects.filter(
            user=self.user,
            level=self.level,
            time='01:23.456'
        ).exists())

    def test_update_time(self):
        # Create initial time
        time = Time.objects.create(
            user=self.user,
            level=self.level,
            time='01:23.456'
        )
        
        # Update time
        response = self.client.post(reverse('update-time', args=[time.id]), {
            'time': '01:20.000'
        })
        self.assertEqual(response.status_code, 302)  # Should redirect after successful update
        time.refresh_from_db()
        self.assertEqual(time.time, '01:20.000')

    def test_time_validation(self):
        # Test various time formats
        valid_times = ['01:23.456', '00:00.000', '59:59.999']
        invalid_times = ['invalid', '1:23.456', '01:23', '01:23.4567', '60:00.000']
        
        for time in valid_times:
            # First, make sure no existing time exists
            Time.objects.filter(user=self.user, level=self.level).delete()
            
            response = self.client.post(reverse('add-time'), {
                'level': self.level.id,
                'game': self.game.id,
                'time': time
            })
            print(f"Response for time {time}:")
            print(f"Status code: {response.status_code}")
            print(f"Content: {response.content}")
            self.assertEqual(response.status_code, 200)
            self.assertTrue(Time.objects.filter(time=time).exists())
        
        for time in invalid_times:
            response = self.client.post(reverse('add-time'), {
                'level': self.level.id,
                'game': self.game.id,
                'time': time
            })
            self.assertEqual(response.status_code, 400)
            self.assertFalse(Time.objects.filter(time=time).exists())

    def test_time_ordering(self):
        # Create multiple times
        times = [
            ('01:23.456', 1),
            ('01:20.000', 2),
            ('01:25.000', 3)
        ]
        
        for time_str, _ in times:
            Time.objects.create(
                user=self.user,
                level=self.level,
                time=time_str
            )
        
        # Get times ordered by time
        ordered_times = Time.objects.filter(level=self.level).order_by('time')
        self.assertEqual(ordered_times[0].time, '01:20.000')
        self.assertEqual(ordered_times[1].time, '01:23.456')
        self.assertEqual(ordered_times[2].time, '01:25.000')

class CSVUploadTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.user.is_active = True
        self.user.save()
        self.client.login(username='testuser', password='testpass123')
        
        # Create organization and team
        self.org = Organization.objects.create(name='Test Org')
        Org_user.objects.create(user=self.user, org=self.org)
        self.team = Team.objects.create(name='Test Team')
        Team_user.objects.create(
            team=self.team,
            user=self.user,
            isCoach=True
        )
        
        # Create game
        self.game = Game.objects.create(game='Mario Kart 8')
        Team_game.objects.create(
            team=self.team,
            game=self.game
        )

    def test_upload_times(self):
        # Create test CSV content
        csv_content = StringIO()
        writer = csv.writer(csv_content)
        # Header row with 12 columns (2 empty + 10 usernames)
        writer.writerow(['', '', 'testuser', '', '', '', '', '', '', '', '', ''])
        # Cup row
        writer.writerow(['Test Cup', '', '', '', '', '', '', '', '', '', '', ''])
        # Level row with time
        writer.writerow(['', 'Test Level', '01:23.456', '', '', '', '', '', '', '', '', ''])
        
        # Create test CSV file
        csv_file = StringIO(csv_content.getvalue())
        csv_file.name = 'test.csv'
        
        # Upload times
        response = self.client.post(reverse('upload_times', args=[self.org.id, self.team.id]), {
            'csv_file': csv_file,
            'game': self.game.id
        })
        self.assertEqual(response.status_code, 302)  # Should redirect after successful upload
        
        # Verify level was created
        level = Level.objects.filter(level_name='Test Level', game=self.game).first()
        self.assertIsNotNone(level)
        
        # Verify time was created
        self.assertTrue(Time.objects.filter(
            user=self.user,
            level=level,
            time='01:23.456'
        ).exists())

class ErrorHandlingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.user.is_active = True
        self.user.save()
        self.client.login(username='testuser', password='testpass123')

    def test_invalid_join_code(self):
        response = self.client.post(reverse('create-org-user', args=['INVALID']))
        self.assertEqual(response.status_code, 302)  # Should redirect to join-org page
        self.assertFalse(Org_user.objects.filter(user=self.user).exists())

    def test_duplicate_team_name(self):
        # Create initial team
        Team.objects.create(name='Test Team')
        
        # Try to create team with same name
        response = self.client.post(reverse('new-team'), {
            'name': 'Test Team',
            'description': 'Test Description'
        })
        self.assertEqual(response.status_code, 200)  # Should stay on form page
        self.assertEqual(Team.objects.filter(name='Test Team').count(), 1)

    def test_invalid_time_format(self):
        # Create game and level
        game = Game.objects.create(game='Mario Kart 8')
        level = Level.objects.create(
            level_name='Test Level',
            game=game
        )
        
        # Try to add invalid time
        response = self.client.post(reverse('add-time'), {
            'level': level.id,
            'game': game.id,
            'time': 'invalid'
        })
        self.assertEqual(response.status_code, 400)  # Should return bad request
        self.assertFalse(Time.objects.filter(user=self.user).exists())

class TeamGameTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.user.is_active = True
        self.user.save()
        self.client.login(username='testuser', password='testpass123')
        
        # Create organization and team
        self.org = Organization.objects.create(name='Test Org')
        Org_user.objects.create(user=self.user, org=self.org)
        self.team = Team.objects.create(name='Test Team')
        Team_user.objects.create(
            team=self.team,
            user=self.user,
            isCoach=True
        )
        
        # Create game
        self.game = Game.objects.create(game='Mario Kart 8')

    def test_add_team_game(self):
        response = self.client.post(reverse('add_team_game', args=[self.team.id]), {
            'game': self.game.id
        })
        self.assertEqual(response.status_code, 302)  # Should redirect after successful addition
        self.assertTrue(Team_game.objects.filter(team=self.team, game=self.game).exists())

    def test_remove_team_game(self):
        # First add a team game
        team_game = Team_game.objects.create(team=self.team, game=self.game)
        
        # Then remove it
        response = self.client.post(reverse('team-details', args=[self.team.id]))
        self.assertEqual(response.status_code, 200)  # Should be able to view team details
        self.assertTrue(Team_game.objects.filter(id=team_game.id).exists())  # Team game should still exist
