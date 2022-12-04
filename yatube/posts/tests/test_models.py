from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='TestAuthor'),
            text='Тестовый пост',
        )

    def test_verbose_name_group(self):
        """verbose_name в полях совпадает с ожидаемым в Group"""
        field_verboses_group = [
            ('title', 'название'),
            ('slug', 'адрес'),
            ('description', 'описание'),
        ]
        for field, expected_value in field_verboses_group:
            with self.subTest(field=field):
                self.assertEqual(
                    self.group._meta.get_field(field)
                              .verbose_name, expected_value)

    def test_verbose_name_post(self):
        """verbose_name в полях совпадает с ожидаемым в Post"""
        field_verboses = [
            ('text', 'текст поста'),
            ('pub_date', 'дата публикации'),
            ('group', 'Группы'),
            ('author', 'автор'),
        ]
        for field, expected_value in field_verboses:
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field)
                                   .verbose_name, expected_value)

    def test_help_text_group(self):
        """help_text в полях совпадает с ожидаемым в Group."""
        field_help_texts = [
            ('title', 'введите название группы '
                      '(макс. 200 символов)'),
            ('slug', 'введите уникальный адрес группы'),
            ('description', 'введите описание сообщества'),
        ]
        for field, expected_value in field_help_texts:
            with self.subTest(field=field):
                self.assertEqual(
                    self.group._meta.get_field(field)
                                    .help_text, expected_value)

    def test_help_text_post(self):
        """help_text в полях совпадает с ожидаемым в Post."""
        field_help_texts = [
            ('text', 'введите содержание поста'),
            ('group', 'выберете к какой группе принадлежит пост'),
            ('author', 'выберете автора поста'),
        ]
        for field, expected_value in field_help_texts:
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text, expected_value)

    def test_str(self):
        """__str__  совпадает с ожидаемым."""
        field_str = [
            (self.post.text[:Post.POSTMODELSTRLIMIT], self.post),
            (self.group.title, self.group)
        ]
        for expected_value, object in field_str:
            with self.subTest(expected_value=expected_value):
                self.assertEqual(expected_value, str(object))
