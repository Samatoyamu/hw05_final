import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cache.clear()
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
        cls.secondgroup = Group.objects.create(
            title='Другая тестовая группа',
            slug='another-test-slug',
            description='Другое тестовое описание',
        )
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='TestAuthor'),
            group=cls.group,
            text='Тестовый пост',
            image=cls.pic
        )
        cls.follow = Follow.objects.create(
            author=cls.post.author,
            user=User.objects.create_user(username='Fan')
        )
        cls.notfan = User.objects.create_user(username='NotFan')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.follow.user)

    def test_pages_show_correct_context_main_details_profile_pages(self):
        """Шаблоны сформированы с правильным контекстом,
        на главной,на странице деталей,на странице группы и в профиле"""
        url_names = [
            reverse('posts:index'),
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
            reverse('posts:profile', kwargs={'username': self.post.author}),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:follow_index'),
        ]
        for address in url_names:
            with self.subTest(address=address):
                cache.clear()
                response = self.authorized_client.get(address)
                self.assertEqual(response.context['post'].text, self.post.text)
                self.assertEqual(response.context['post'].author,
                                 self.post.author)
                self.assertEqual(response.context['post'].group,
                                 self.post.group)
                self.assertTrue(response.context['post'].image,)

    def test_pages_show_correct_context_create_page(self):
        """Шаблон сформирован с правильным контекстом,
        на странице создания поста"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_pages_show_correct_context_edit_page(self):
        """Шаблон сформирован с правильным контекстом,
        на странице редактирования поста"""
        self.authorized_client.force_login(self.post.author)
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        self.assertIsInstance(response.context.get('form'), PostForm)
        self.assertEqual(response.context.get('form').instance, self.post)

    def test_pages_show_correct_context_group_author_pages(self):
        """Шаблоны сформированы с правильным контекстом,
        на странице автора и группы"""
        url_names = [
            (reverse('posts:profile', kwargs={'username': self.post.author}),
             'author', self.post.author),
            (reverse('posts:group_list', kwargs={'slug': self.group.slug}),
             'group', self.group),
        ]
        for address, object, expected in url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.context[object], expected)

    def test_post_not_in_another_group(self):
        """Пост не выводится в другой группе"""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.secondgroup.slug}))
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_follow(self):
        """Можно подписыватся"""
        Follow.objects.all().delete()
        follow_count = Follow.objects.count()
        self.authorized_client.get(reverse('posts:profile_follow',
                                   kwargs={'username': self.post.author}))
        object = Follow.objects.get(user=self.follow.user,
                                    author=self.post.author)
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertEqual(object.author, self.post.author)
        self.assertEqual(object.user, self.follow.user)

    def test_unfollow(self):
        """можно отписываться"""
        self.authorized_client.get(reverse('posts:profile_unfollow',
                                   kwargs={'username': self.post.author}))
        self.assertFalse(Follow.objects.count())
        self.assertFalse(Follow.objects
                               .filter(
                                   user=self.follow.user,
                                   author=self.post.author).exists())

    def test_feed(self):
        """нету записей того,на кого не подписан"""
        self.authorized_client.force_login(self.notfan)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_cache(self):
        """тест кэширования"""
        first_response = self.authorized_client.get(reverse('posts:index'))
        Post.objects.all().delete()
        second_response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(first_response.content, second_response.content)
        cache.clear()
        third_response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(second_response.content, third_response.content)
