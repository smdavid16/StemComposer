from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from .models import Melodie, Stem


# ============================================================
# MODEL TESTS
# ============================================================

class MelodieModelTest(TestCase):
    """Teste pentru modelul Melodie."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )

    def test_creare_melodie(self):
        """Melodia se creează corect cu toate câmpurile."""
        melodie = Melodie.objects.create(
            user=self.user,
            titlu='Test Song.mp3',
            fisier_original='originale/test.mp3'
        )
        self.assertEqual(melodie.titlu, 'Test Song.mp3')
        self.assertEqual(melodie.user, self.user)
        self.assertIsNotNone(melodie.data_incarcare)

    def test_str_representation(self):
        """__str__ returnează titlul și username-ul."""
        melodie = Melodie.objects.create(
            user=self.user,
            titlu='My Track.wav',
            fisier_original='originale/my_track.wav'
        )
        self.assertEqual(str(melodie), 'My Track.wav - testuser')

    def test_relatie_user(self):
        """Melodiile sunt legate corect de user."""
        Melodie.objects.create(
            user=self.user, titlu='Song 1', fisier_original='originale/s1.mp3'
        )
        Melodie.objects.create(
            user=self.user, titlu='Song 2', fisier_original='originale/s2.mp3'
        )
        self.assertEqual(self.user.melodii.count(), 2)

    def test_cascade_delete_user(self):
        """Stergerea userului sterge si melodiile."""
        Melodie.objects.create(
            user=self.user, titlu='Song', fisier_original='originale/s.mp3'
        )
        self.user.delete()
        self.assertEqual(Melodie.objects.count(), 0)


class StemModelTest(TestCase):
    """Teste pentru modelul Stem."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.melodie = Melodie.objects.create(
            user=self.user,
            titlu='Test.mp3',
            fisier_original='originale/test.mp3'
        )

    def test_creare_stem(self):
        """Stemul se creează corect."""
        stem = Stem.objects.create(
            melodie=self.melodie,
            tip='vocals',
            fisier_stem='separated/vocals.wav'
        )
        self.assertEqual(stem.tip, 'vocals')
        self.assertEqual(stem.melodie, self.melodie)

    def test_str_representation(self):
        """__str__ include tipul și titlul melodiei."""
        stem = Stem.objects.create(
            melodie=self.melodie,
            tip='drums',
            fisier_stem='separated/drums.wav'
        )
        self.assertEqual(str(stem), 'drums pentru Test.mp3')

    def test_relatie_melodie_stemuri(self):
        """O melodie poate avea mai multe stemuri."""
        for tip in ['vocals', 'drums', 'bass', 'other']:
            Stem.objects.create(
                melodie=self.melodie,
                tip=tip,
                fisier_stem=f'separated/{tip}.wav'
            )
        self.assertEqual(self.melodie.stemuri.count(), 4)

    def test_cascade_delete_melodie(self):
        """Stergerea melodiei sterge si stemurile."""
        Stem.objects.create(
            melodie=self.melodie, tip='vocals',
            fisier_stem='separated/vocals.wav'
        )
        self.melodie.delete()
        self.assertEqual(Stem.objects.count(), 0)

    def test_tipuri_stem_valide(self):
        """Verifică că toate tipurile de stem sunt valide."""
        tipuri_valide = ['vocals', 'drums', 'bass', 'other']
        tipuri_model = [choice[0] for choice in Stem.TIPURI_STEM]
        self.assertEqual(tipuri_valide, tipuri_model)


# ============================================================
# AUTH API TESTS
# ============================================================

class SignupViewTest(TestCase):
    """Teste pentru API-ul de signup."""

    def setUp(self):
        self.client = Client()

    def test_signup_success(self):
        """Signup cu date valide creează userul și returnează 200."""
        response = self.client.post(
            '/api/signup/',
            {'username': 'newuser', 'password': 'securepass123'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('mesaj', response.json())
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_signup_duplicate_user(self):
        """Signup cu username existent returnează 400."""
        User.objects.create_user(username='existing', password='pass123')
        response = self.client.post(
            '/api/signup/',
            {'username': 'existing', 'password': 'pass123'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('eroare', response.json())

    def test_signup_missing_fields(self):
        """Signup fără username sau parolă returnează 400."""
        response = self.client.post(
            '/api/signup/',
            {'username': '', 'password': ''},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_signup_no_password(self):
        """Signup doar cu username returnează 400."""
        response = self.client.post(
            '/api/signup/',
            {'username': 'user1'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)


class LoginViewTest(TestCase):
    """Teste pentru API-ul de login."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )

    def test_login_success(self):
        """Login cu credențiale valide returnează 200."""
        response = self.client.post(
            '/api/login/',
            {'username': 'testuser', 'password': 'testpass123'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('mesaj', response.json())

    def test_login_wrong_password(self):
        """Login cu parolă greșită returnează 401."""
        response = self.client.post(
            '/api/login/',
            {'username': 'testuser', 'password': 'wrongpass'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn('eroare', response.json())

    def test_login_nonexistent_user(self):
        """Login cu user inexistent returnează 401."""
        response = self.client.post(
            '/api/login/',
            {'username': 'nouser', 'password': 'pass'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)

    def test_login_sets_session(self):
        """După login, sesiunea este activă."""
        self.client.post(
            '/api/login/',
            {'username': 'testuser', 'password': 'testpass123'},
            content_type='application/json'
        )
        # Verificăm că userul este autentificat prin accesarea
        # unui endpoint care cere autentificare
        response = self.client.get('/api/istoric/')
        self.assertEqual(response.status_code, 200)


class LogoutViewTest(TestCase):
    """Teste pentru API-ul de logout."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_logout_success(self):
        """Logout returnează 200."""
        response = self.client.post('/api/logout/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('mesaj', response.json())

    def test_logout_clears_session(self):
        """După logout, endpointurile protejate returnează 403."""
        self.client.post('/api/logout/')
        response = self.client.get('/api/istoric/')
        self.assertEqual(response.status_code, 403)


# ============================================================
# UPLOAD API TESTS
# ============================================================

class UploadViewTest(TestCase):
    """Teste pentru API-ul de upload."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    @patch('app.views.proceseaza_melodia_task.delay')
    def test_upload_success(self, mock_delay):
        """Upload cu fișier valid creează o melodie în DB."""
        mock_delay.return_value.id = 'fake-task-id'

        audio_file = SimpleUploadedFile(
            'test_song.mp3',
            b'fake audio content',
            content_type='audio/mpeg'
        )
        response = self.client.post(
            '/api/upload/',
            {'file': audio_file},
            format='multipart'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('task_id', data)
        self.assertIn('melodie_id', data)
        self.assertEqual(Melodie.objects.count(), 1)
        self.assertEqual(Melodie.objects.first().user, self.user)

    def test_upload_no_file(self):
        """Upload fără fișier returnează 400."""
        response = self.client.post('/api/upload/')
        self.assertEqual(response.status_code, 400)
        self.assertIn('eroare', response.json())

    def test_upload_unauthenticated(self):
        """Upload fără autentificare returnează 403."""
        self.client.logout()
        audio_file = SimpleUploadedFile(
            'test.mp3', b'content', content_type='audio/mpeg'
        )
        response = self.client.post('/api/upload/', {'file': audio_file})
        self.assertEqual(response.status_code, 403)


# ============================================================
# ISTORIC (HISTORY) API TESTS
# ============================================================

class IstoricViewTest(TestCase):
    """Teste pentru API-ul de istoric."""

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user1', password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='user2', password='pass123'
        )

        # Creăm melodii pentru user1
        self.melodie1 = Melodie.objects.create(
            user=self.user1, titlu='Song1.mp3',
            fisier_original='originale/song1.mp3'
        )
        Stem.objects.create(
            melodie=self.melodie1, tip='vocals',
            fisier_stem='separated/vocals.wav'
        )

        # Creăm melodii pentru user2
        Melodie.objects.create(
            user=self.user2, titlu='OtherSong.mp3',
            fisier_original='originale/other.mp3'
        )

    def test_istoric_returns_own_melodies(self):
        """Istoricul returnează doar melodiile userului autentificat."""
        self.client.login(username='user1', password='pass123')
        response = self.client.get('/api/istoric/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['titlu'], 'Song1.mp3')

    def test_istoric_includes_stemuri(self):
        """Istoricul include stemurile melodiei."""
        self.client.login(username='user1', password='pass123')
        response = self.client.get('/api/istoric/')
        data = response.json()
        self.assertEqual(len(data[0]['stemuri']), 1)
        self.assertEqual(data[0]['stemuri'][0]['tip'], 'vocals')

    def test_istoric_not_shows_other_users(self):
        """User1 nu vede melodiile lui user2."""
        self.client.login(username='user1', password='pass123')
        response = self.client.get('/api/istoric/')
        data = response.json()
        titluri = [m['titlu'] for m in data]
        self.assertNotIn('OtherSong.mp3', titluri)

    def test_istoric_unauthenticated(self):
        """Istoric fără autentificare returnează 403."""
        response = self.client.get('/api/istoric/')
        self.assertEqual(response.status_code, 403)

    def test_istoric_response_structure(self):
        """Verifică structura răspunsului API de istoric."""
        self.client.login(username='user1', password='pass123')
        response = self.client.get('/api/istoric/')
        data = response.json()
        item = data[0]
        self.assertIn('id', item)
        self.assertIn('titlu', item)
        self.assertIn('data', item)
        self.assertIn('url_original', item)
        self.assertIn('stemuri', item)


# ============================================================
# DETALII MELODIE API TESTS
# ============================================================

class DetaliiMelodieViewTest(TestCase):
    """Teste pentru API-ul de detalii melodie."""

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user1', password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='user2', password='pass123'
        )
        self.melodie = Melodie.objects.create(
            user=self.user1, titlu='MySong.mp3',
            fisier_original='originale/mysong.mp3'
        )
        for tip in ['vocals', 'drums', 'bass', 'other']:
            Stem.objects.create(
                melodie=self.melodie, tip=tip,
                fisier_stem=f'separated/{tip}.wav'
            )

    def test_detalii_own_melodie(self):
        """Userul își poate vedea propria melodie."""
        self.client.login(username='user1', password='pass123')
        response = self.client.get(f'/api/melodie/{self.melodie.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['titlu'], 'MySong.mp3')
        self.assertEqual(len(data['stemuri']), 4)

    def test_detalii_other_user_melodie(self):
        """Userul NU poate vedea melodia altui user."""
        self.client.login(username='user2', password='pass123')
        response = self.client.get(f'/api/melodie/{self.melodie.id}/')
        self.assertEqual(response.status_code, 404)

    def test_detalii_nonexistent_melodie(self):
        """Melodie inexistentă returnează 404."""
        self.client.login(username='user1', password='pass123')
        response = self.client.get('/api/melodie/99999/')
        self.assertEqual(response.status_code, 404)

    def test_detalii_unauthenticated(self):
        """Detalii fără autentificare returnează 403."""
        response = self.client.get(f'/api/melodie/{self.melodie.id}/')
        self.assertEqual(response.status_code, 403)

    def test_detalii_response_structure(self):
        """Verifică structura completă a răspunsului."""
        self.client.login(username='user1', password='pass123')
        response = self.client.get(f'/api/melodie/{self.melodie.id}/')
        data = response.json()
        self.assertIn('id', data)
        self.assertIn('titlu', data)
        self.assertIn('url_original', data)
        self.assertIn('stemuri', data)
        # Verifică structura stemurilor
        stem = data['stemuri'][0]
        self.assertIn('tip', stem)
        self.assertIn('url', stem)


# ============================================================
# HOME PAGE TEST
# ============================================================

class HomePageTest(TestCase):
    """Test pentru pagina principală (interfața inline)."""

    def test_home_page_loads(self):
        """Pagina principală se încarcă cu 200."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_home_page_contains_title(self):
        """Pagina conține titlul StemComposer."""
        response = self.client.get('/')
        self.assertContains(response, 'StemComposer')

    def test_home_page_contains_auth_section(self):
        """Pagina conține secțiunea de autentificare."""
        response = self.client.get('/')
        self.assertContains(response, 'sectiune-auth')
