from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Knowledge, KnowledgeImage
from PIL import Image
import io


def create_test_image():
    image_file = io.BytesIO()
    image = Image.new('RGB', (100, 100), color='red')
    image.save(image_file, 'PNG')
    image_file.seek(0)
    return SimpleUploadedFile("test_image.png", image_file.read(), content_type="image/png")


class KnowledgeAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.list_url = reverse('knowledge-list')
        self.base_data = {
            'user_id': 'test_user_1',
            'text': 'Test knowledge text',
            'quiz': []
        }

    def test_create_knowledge(self):
        response = self.client.post(self.list_url, self.base_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Knowledge.objects.count(), 1)
        knowledge = Knowledge.objects.first()
        self.assertEqual(knowledge.user_id, 'test_user_1')
        self.assertEqual(knowledge.text, 'Test knowledge text')
        self.assertEqual(knowledge.quiz, [])

    def test_create_knowledge_with_quiz(self):
        data = self.base_data.copy()
        data['quiz'] = ['question1', 'question2']
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        knowledge = Knowledge.objects.first()
        self.assertEqual(knowledge.quiz, ['question1', 'question2'])

    def test_list_knowledge(self):
        Knowledge.objects.create(
            user_id='user1',
            text='Text 1',
            quiz=[]
        )
        Knowledge.objects.create(
            user_id='user2',
            text='Text 2',
            quiz=[]
        )
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_list_knowledge_pagination(self):
        for i in range(25):
            Knowledge.objects.create(
                user_id=f'user{i}',
                text=f'Text {i}',
                quiz=[]
            )
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 20)
        self.assertIsNotNone(response.data['next'])

    def test_filter_by_user_id(self):
        Knowledge.objects.create(user_id='user1', text='Text 1', quiz=[])
        Knowledge.objects.create(user_id='user2', text='Text 2', quiz=[])
        response = self.client.get(self.list_url, {'user_id': 'user1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['user_id'], 'user1')

    def test_search_by_text(self):
        Knowledge.objects.create(user_id='user1', text='Python programming', quiz=[])
        Knowledge.objects.create(user_id='user2', text='Django framework', quiz=[])
        response = self.client.get(self.list_url, {'search': 'Python'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIn('Python', response.data['results'][0]['text'])

    def test_search_by_user_id(self):
        Knowledge.objects.create(user_id='test_user', text='Text', quiz=[])
        Knowledge.objects.create(user_id='other_user', text='Text', quiz=[])
        response = self.client.get(self.list_url, {'search': 'test_user'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_ordering(self):
        knowledge1 = Knowledge.objects.create(user_id='user1', text='Text', quiz=[])
        knowledge2 = Knowledge.objects.create(user_id='user2', text='Text', quiz=[])
        response = self.client.get(self.list_url, {'ordering': 'created_at'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['id'], knowledge1.id)

        response = self.client.get(self.list_url, {'ordering': '-created_at'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['id'], knowledge2.id)

    def test_retrieve_knowledge(self):
        knowledge = Knowledge.objects.create(
            user_id='user1',
            text='Test text',
            quiz=['q1', 'q2']
        )
        url = reverse('knowledge-detail', args=[knowledge.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_id'], 'user1')
        self.assertEqual(response.data['text'], 'Test text')
        self.assertEqual(response.data['quiz'], ['q1', 'q2'])

    def test_update_knowledge(self):
        knowledge = Knowledge.objects.create(
            user_id='user1',
            text='Original text',
            quiz=[]
        )
        url = reverse('knowledge-detail', args=[knowledge.id])
        data = {'text': 'Updated text', 'quiz': ['new_question']}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        knowledge.refresh_from_db()
        self.assertEqual(knowledge.text, 'Updated text')
        self.assertEqual(knowledge.quiz, ['new_question'])

    def test_soft_delete_knowledge(self):
        knowledge = Knowledge.objects.create(
            user_id='user1',
            text='Text',
            quiz=[]
        )
        url = reverse('knowledge-detail', args=[knowledge.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        knowledge.refresh_from_db()
        self.assertIsNotNone(knowledge.deleted_at)
        
        response = self.client.get(self.list_url)
        self.assertEqual(len(response.data['results']), 0)

    def test_restore_knowledge(self):
        knowledge = Knowledge.objects.create(
            user_id='user1',
            text='Text',
            quiz=[]
        )
        knowledge.soft_delete()
        
        url = reverse('knowledge-restore', args=[knowledge.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        knowledge.refresh_from_db()
        self.assertIsNone(knowledge.deleted_at)

    def test_restore_already_active_knowledge(self):
        knowledge = Knowledge.objects.create(
            user_id='user1',
            text='Text',
            quiz=[]
        )
        url = reverse('knowledge-restore', args=[knowledge.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_by_date_range(self):
        from datetime import timedelta
        now = timezone.now()
        
        knowledge1 = Knowledge.objects.create(
            user_id='user1',
            text='Text',
            quiz=[]
        )
        Knowledge.objects.filter(pk=knowledge1.pk).update(created_at=now - timedelta(days=5))
        
        knowledge2 = Knowledge.objects.create(
            user_id='user2',
            text='Text',
            quiz=[]
        )
        Knowledge.objects.filter(pk=knowledge2.pk).update(created_at=now - timedelta(days=2))
        
        knowledge3 = Knowledge.objects.create(
            user_id='user3',
            text='Text',
            quiz=[]
        )
        Knowledge.objects.filter(pk=knowledge3.pk).update(created_at=now)
        
        start_date = now - timedelta(days=3)
        end_date = now + timedelta(seconds=1)
        
        response = self.client.get(self.list_url, {
            'created_at__gte': start_date.isoformat(),
            'created_at__lte': end_date.isoformat()
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        user_ids = [item['user_id'] for item in response.data['results']]
        self.assertIn('user2', user_ids)
        self.assertIn('user3', user_ids)

    def test_upload_image(self):
        knowledge = Knowledge.objects.create(
            user_id='user1',
            text='Text',
            quiz=[]
        )
        url = reverse('knowledge-upload-image', args=[knowledge.id])
        
        image_file = create_test_image()
        response = self.client.post(url, {'image': image_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(knowledge.images.count(), 1)

    def test_upload_image_without_file(self):
        knowledge = Knowledge.objects.create(
            user_id='user1',
            text='Text',
            quiz=[]
        )
        url = reverse('knowledge-upload-image', args=[knowledge.id])
        response = self.client.post(url, {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_image(self):
        knowledge = Knowledge.objects.create(
            user_id='user1',
            text='Text',
            quiz=[]
        )
        image_file = create_test_image()
        image = KnowledgeImage.objects.create(
            knowledge=knowledge,
            image=image_file
        )
        url = reverse('knowledge-delete-image', args=[knowledge.id, image.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(knowledge.images.count(), 0)

    def test_delete_nonexistent_image(self):
        knowledge = Knowledge.objects.create(
            user_id='user1',
            text='Text',
            quiz=[]
        )
        url = reverse('knowledge-delete-image', args=[knowledge.id, 99999])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_knowledge_with_images_in_response(self):
        knowledge = Knowledge.objects.create(
            user_id='user1',
            text='Text',
            quiz=[]
        )
        image_file = create_test_image()
        KnowledgeImage.objects.create(
            knowledge=knowledge,
            image=image_file
        )
        url = reverse('knowledge-detail', args=[knowledge.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['images']), 1)
        self.assertIn('image', response.data['images'][0])

    def test_validate_quiz_must_be_list(self):
        data = self.base_data.copy()
        data['quiz'] = 'not a list'
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_deleted_knowledge_not_in_list(self):
        knowledge1 = Knowledge.objects.create(
            user_id='user1',
            text='Text 1',
            quiz=[]
        )
        knowledge2 = Knowledge.objects.create(
            user_id='user2',
            text='Text 2',
            quiz=[]
        )
        knowledge1.soft_delete()
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], knowledge2.id)
