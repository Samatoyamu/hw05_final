import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pic = SimpleUploadedFile(
            name='small.gif',
            content=(
                b'\x47\x49\x46\x38\x39\x61\x02\x00'
                b'\x01\x00\x80\x00\x00\x00\x00\x00'
                b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                b'\x0A\x00\x3B'
            ),
            content_type='image/gif',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='TestAuthor'),
            text='Тестовый пост',
            group=cls.group,
        )
        cls.form_data = {
            'text': 'Новый тест пост',
            'group': cls.group.id,
            'image': cls.pic
        }
        cls.comment = {
            'text': 'Комментарий',
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post.author)

    def test_create_form(self):
        """Валидная форма создает новый пост."""
        Post.objects.all().delete()
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        object = Post.objects.all().last()
        self.assertEqual(object.text, self.form_data['text'])
        self.assertEqual(object.author, response.context['user'])
        self.assertEqual(object.group.id, self.form_data['group'])
        self.assertEqual(object.image.name,
                         f"posts/{self.form_data['image'].name}")
        self.assertRedirects(response, reverse(
                             'posts:profile',
                             kwargs={'username': object.author}))

    def test_edit_form(self):
        """При отправке валидной формы,пост меняется."""
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data={'text': 'Новый тест пост',
                  'group': self.group.id},
            follow=True,
        )
        object = Post.objects.get(id=self.post.id)
        self.assertEqual(object.text, self.form_data['text'])
        self.assertEqual(self.post.author, object.author)
        self.assertEqual(object.group.id, self.form_data['group'])
        self.assertRedirects(response, reverse(
                             'posts:post_detail',
                             kwargs={'post_id': object.id}))

    def test_can_comment(self):
        """успешно отправляются комментарий"""
        Comment.objects.all().delete()
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=self.comment,
            follow=True,
        )
        object = Comment.objects.last()
        self.assertEqual(object.text, self.comment['text'])
        self.assertEqual(object.author, response.context['user'])
        self.assertEqual(object.post, self.post)
        self.assertRedirects(response, reverse(
                             'posts:post_detail',
                             kwargs={'post_id': object.id}))

    def test_guest_cant_comment(self):
        """неавторизованные не могут комментировать"""
        comments_count = Comment.objects.count()
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=self.comment,
            follow=True,
        )
        object = Comment.objects.last()
        self.assertEqual(object, None)
        self.assertEqual(Comment.objects.count(), comments_count)
