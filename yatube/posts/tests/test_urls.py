from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class URLTemplateNameTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.randomuser = User.objects.create_user(username='Vasya')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='TestAuthor'),
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post.author)

    def test_urls_exists_at_desired_location(self):
        """URL-адрес доступен для анонимов,тест неизвестного URL"""
        url_names = [
            (reverse('posts:index'), HTTPStatus.OK, False),
            (reverse('posts:group_list', kwargs={'slug': self.group.slug}),
             HTTPStatus.OK, False),
            (reverse('posts:profile', kwargs={'username': self.post.author}),
             HTTPStatus.OK, False),
            (reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
             HTTPStatus.OK, False),
            ('/post/', HTTPStatus.NOT_FOUND, False),
            (reverse('posts:post_create'), HTTPStatus.OK, True),
            (reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
             HTTPStatus.OK, True),
            (reverse('posts:follow_index'), HTTPStatus.OK, True)
        ]
        for address, status_code, authuser in url_names:
            with self.subTest(address=address):
                if not authuser:
                    response = self.guest_client.get(address)
                else:
                    response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, status_code)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон,
        тест соответствия фактических адресов."""
        url_template_names = [
            ('posts/index.html', reverse('posts:index'), '/'),
            ('posts/group_list.html', reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}),
                f'/group/{self.group.slug}/'),
            ('posts/profile.html', reverse(
                'posts:profile', kwargs={'username': self.post.author}),
                f'/profile/{self.post.author}/'),
            ('posts/post_detail.html', reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}),
                f'/posts/{self.post.id}/'),
            ('posts/create_post.html', reverse('posts:post_create'),
                '/create/'),
            ('posts/create_post.html', reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}),
                f'/posts/{self.post.id}/edit/'),
            ('posts/follow.html', reverse('posts:follow_index'), '/follow/'),
            ('core/404.html', 'post/', 'post/'),
        ]
        for template, address, url in url_template_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(address, url)

    def test_redirect_on_create_edit(self):
        """Перенаправляет анонимного пользователя на страницу логина,
        при попытке создать или изменить пост.
        """
        url_names = [
            (reverse('posts:post_create'),
             f"{reverse('users:login')}?next={reverse('posts:post_create')}"
             ),
            (reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
             f"{reverse('users:login')}?next="
             f"{reverse('posts:post_edit', kwargs={'post_id': self.post.id})}"
             ),
        ]
        for address, redirect in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, redirect)

    def test_redirect_on_edit_edit(self):
        """перенаправляет зарегистрированного пользователя,
        при попытке изменить пост"""
        self.authorized_client.force_login(self.randomuser)
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}), follow=True)
        redirect = reverse('posts:post_detail',
                           kwargs={'post_id': self.post.id})
        self.assertRedirects(response, redirect)
