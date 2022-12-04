from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        "название",
        help_text="введите название группы "
                  "(макс. 200 символов)",
        max_length=200,
    )
    slug = models.SlugField(
        "адрес",
        help_text="введите уникальный адрес группы",
        unique=True,
    )
    description = models.TextField(
        "описание",
        help_text="введите описание сообщества",
    )

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    POSTMODELSTRLIMIT = 15
    text = models.TextField(
        "текст поста",
        help_text="введите содержание поста",
    )
    pub_date = models.DateTimeField(
        "дата публикации",
        auto_now_add=True,
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="posts",
        verbose_name="Группы",
        help_text="выберете к какой группе принадлежит пост",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="автор",
        help_text="выберете автора поста",
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self) -> str:
        return self.text[:self.POSTMODELSTRLIMIT]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name="Пост",
        help_text="ссылка на пост, к которому оставлен комментарий",
        related_name="comments",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        help_text="автор комментария",
        verbose_name="Автор",
    )
    text = models.TextField(
        help_text="текст комментария",
        verbose_name="Текст",
    )
    created = models.DateTimeField(
        "дата комментария",
        auto_now_add=True,
    )

    def __str__(self) -> str:
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        help_text="пользователь, который подписывается",
        related_name="follower",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        help_text="автор на кого подписываются",
        verbose_name="Автор",
    )
