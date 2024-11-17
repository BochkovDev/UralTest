from django.db import models
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    ''' Модель Категории материалов '''
    parent = models.ForeignKey(
        'self',
        verbose_name=_('Родительская категория'),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children',
    )

    code = models.PositiveSmallIntegerField(verbose_name=_('Код'), unique=True)
    name = models.CharField(verbose_name=_('Название'), max_length=55)

    def __str__(self) -> str:
        return f'{self.code}-{self.name}'
    
    class Meta:
        verbose_name = _('Категория')
        verbose_name_plural = _('Категории')
        ordering = ['parent__id', 'code']


class Material(models.Model):
    ''' Модель Материала '''
    category = models.ForeignKey(
        Category,
        verbose_name=_('Категория'),
        on_delete=models.CASCADE,
        related_name='materials',
    )

    code = models.PositiveIntegerField(verbose_name=_('Код'), unique=True)
    name = models.CharField(verbose_name=_('Название'), max_length=100)
    cost = models.DecimalField(verbose_name=_('Стоимость'), max_digits=12, decimal_places=2)

    def __str__(self) -> str:
        return f'{self.code}-{self.name}'
    
    class Meta:
        verbose_name = _('Материал')
        verbose_name_plural = _('Материалы')
        ordering = ['category__id', 'code']