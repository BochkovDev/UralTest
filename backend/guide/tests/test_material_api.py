from io import BytesIO

from openpyxl import Workbook
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from guide.models import Material, Category

class MaterialAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.category = Category.objects.create(
            code=1111,
            name="Test Category",
        )

        self.material = Material.objects.create(
            category=self.category,
            code=1001,
            name="Test Material",
            cost=150.50,
        )

        self.material_list_url = reverse('material-list') 
        self.material_detail_url = reverse('material-detail', args=[self.material.id])

    def test_get_materials_list(self):
        response = self.client.get(self.material_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)

    def test_create_material(self):
        data = {
            'category': self.category.id,
            'code': 1002,
            'name': 'New Material',
            'cost': '200.00'
        }
        response = self.client.post(self.material_list_url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Material.objects.filter(code=1002).exists())

    

    def test_get_material(self):
        response = self.client.get(self.material_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], self.material.code)

    def test_put_material(self):
        data = {
            'category': self.category.id,
            'code': 1010,
            'name': 'Updated Material Name',
            'cost': 150.50,
        }
        response = self.client.put(self.material_detail_url, data, format='json')
        self.assertEqual(response.status_code, 200)

        self.material.refresh_from_db()
        self.assertEqual(self.material.name, 'Updated Material Name')

    def test_patch_material(self):
        data = {
            'name': 'Updated Material Name',
        }
        response = self.client.patch(self.material_detail_url, data, format='json')
        self.assertEqual(response.status_code, 200)

        self.material.refresh_from_db()
        self.assertEqual(self.material.name, 'Updated Material Name')

    def test_delete_material(self):
        response = self.client.delete(self.material_detail_url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Material.objects.filter(id=self.material.id).exists())


class MaterialExcelUploadTest(TestCase):
    def setUp(self):
        Category.objects.create(
            id=1,
            code=1000,
            name="Test Category",
        )

        self.category = Category.objects.create(
            id=2,
            code=1001,
            name="Test Category",
        )

        self.client = Client()
        self.url = '/materials/' 

    def create_excel_file(self, rows):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(['Category', 'Code', 'Name', 'Cost']) 
        for row in rows:
            sheet.append(row)

        excel_file = BytesIO()
        workbook.save(excel_file)
        excel_file.seek(0)

        return excel_file

    def test_upload_single_excel_file(self):
        excel_file = self.create_excel_file([
            [1, 101, 'Material 1', 10.5],
            [2, 102, 'Material 2', 15.75]
        ])
        uploaded_file = SimpleUploadedFile('test_materials.xlsx', excel_file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        response = self.client.post(self.url, {'files': [uploaded_file]}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Material.objects.count(), 2)

    def test_upload_multiple_excel_files(self):
        excel_file1 = self.create_excel_file([
            [1, 201, 'Material A', 20.0],
            [1, 202, 'Material B', 25.5]
        ])
        excel_file2 = self.create_excel_file([
            [2, 301, 'Material C', 30.0],
            [2, 302, 'Material D', 35.5]
        ])

        uploaded_file1 = SimpleUploadedFile('test_materials_1.xlsx', excel_file1.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        uploaded_file2 = SimpleUploadedFile('test_materials_2.xlsx', excel_file2.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        response = self.client.post(self.url, {'files': [uploaded_file1, uploaded_file2]}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Material.objects.count(), 4)

        material1 = Material.objects.get(code=201)
        self.assertEqual(material1.name, 'Material A')
        self.assertEqual(material1.cost, 20.0)

        material2 = Material.objects.get(code=202)
        self.assertEqual(material2.name, 'Material B')
        self.assertEqual(material2.cost, 25.5)

        material3 = Material.objects.get(code=301)
        self.assertEqual(material3.name, 'Material C')
        self.assertEqual(material3.cost, 30.0)

        material4 = Material.objects.get(code=302)
        self.assertEqual(material4.name, 'Material D')
        self.assertEqual(material4.cost, 35.5)