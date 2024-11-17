import json

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from core.utils import log_db_queries
from guide.models import Category, Material


class CategoryViewSetTestCase(TestCase):
    """Тесты для CategoryViewSet с улучшенной валидацией и покрытием."""

    def setUp(cls):
        """Создание данных для всех тестов."""
        cls.client = APIClient()

        cls.root_category = Category.objects.create(name="Металлы", code="001")
        cls.child_category = Category.objects.create(
            name="Цветные металлы", code="0002", parent=cls.root_category
        )
        cls.grandchild_category = Category.objects.create(
            name="Алюминий", code="0003", parent=cls.child_category
        )

        cls.material_1 = Material.objects.create(
            category=cls.root_category, code=1001, name="Железо", cost=150.00
        )
        cls.material_2 = Material.objects.create(
            category=cls.child_category, code=1002, name="Медь", cost=200.00
        )
        cls.material_3 = Material.objects.create(
            category=cls.grandchild_category, code=1003, name="Алюминий", cost=300.00
        )

    @log_db_queries
    def test_flat_list(self):
        """Тест эндпоинта /categories/"""
        url = reverse('category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        # print(json.dumps(data, indent=4, ensure_ascii=False))
        self.assertEqual(len(data), 3)
        self.assertIn('materials', data[0])
        self.assertEqual(len(data[0]['materials']), 1) 

    @log_db_queries
    def test_tree_view(self):
        """Тест эндпоинта /categories/tree/ для получения иерархического дерева."""
        url = reverse('category-tree')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        print(json.dumps(data, indent=4, ensure_ascii=False))
        self.assertEqual(len(data), 1)  
        root = data[0]
        self.assertEqual(root['name'], "Металлы")
        self.assertEqual(len(root['materials']), 1)
        self.assertEqual(root['materials'][0]['name'], "Железо")
        
        self.assertEqual(len(root['children']), 1)
        child = root['children'][0]
        self.assertEqual(child['name'], "Цветные металлы")
        self.assertEqual(len(child['materials']), 1)
        self.assertEqual(child['materials'][0]['name'], "Медь")
        
        self.assertEqual(len(child['children']), 1)
        grandchild = child['children'][0]
        self.assertEqual(grandchild['name'], "Алюминий")
        self.assertEqual(len(grandchild['materials']), 1)
        self.assertEqual(grandchild['materials'][0]['name'], "Алюминий")

    def test_create_category(self):
        """Тест создания новой категории с проверкой на правильность данных."""
        url = reverse('category-list')
        payload = {
            'name': 'Пластмассы',
            'code': '004',
            'parent': self.root_category.id
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_category = Category.objects.get(name="Пластмассы")
        self.assertEqual(new_category.parent, self.root_category)
        self.assertEqual(new_category.code, 4)

    def test_update_category(self):
        """Тест обновления категории и проверки данных после обновления."""
        url = reverse('category-detail', args=[self.child_category.id])
        payload = {'name': 'Обновленные цветные металлы'}
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.child_category.refresh_from_db()
        self.assertEqual(self.child_category.name, 'Обновленные цветные металлы')

    def test_delete_category(self):
        """Тест удаления категории с проверкой на отсутствие в БД."""
        url = reverse('category-detail', args=[self.grandchild_category.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with self.assertRaises(Category.DoesNotExist):
            Category.objects.get(id=self.grandchild_category.id)

    def test_create_category_with_duplicate_code(self):
        """Тест на создание категории с дублирующимся кодом."""
        url = reverse('category-list')
        payload = {
            'name': 'Дублирующий код',
            'code': '002', 
            'parent': self.root_category.id
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('code', response.json())

    def test_create_category_without_required_fields(self):
        """Тест на создание категории без обязательных полей."""
        url = reverse('category-list')
        payload = {
            'name': '',  # Пустое имя
            'code': '',
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.json())
        self.assertIn('code', response.json())
