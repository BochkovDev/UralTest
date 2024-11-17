from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView 
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample

from .models import Material, Category
from .serializers import MaterialSerializer, CategorySerializer, CategoryTreeSerializer
from .utils import ExcelParser


@extend_schema_view(
    get=extend_schema(
        summary="Получение списка материалов",
        description="Возвращает полный список всех материалов в базе данных.",
        responses={200: MaterialSerializer(many=True)}
    ),
    post=extend_schema(
        summary="Создание нового материала или загрузка данных из Excel файла",
        description=(
            "Создает новый материал на основе данных из запроса или обрабатывает Excel файл. "
            "Если загружены файлы с расширением .xlsx, они будут обработаны и материалы будут добавлены в базу данных."
        ),
        request={
            'multipart/form-data': {
                'file': {
                    'type': 'array',
                    'items': {
                        'type': 'string',
                        'format': 'binary'
                    }
                }
            }
        },
        responses={201: MaterialSerializer, 400: 'Ошибка валидации данных'}
    )
)
class MaterialListView(APIView):
    def get(self, request: Request) -> Response:
        ''' Получение списка материалов '''
        materials = Material.objects.all()
        serializer = MaterialSerializer(materials, many=True)
        return Response(serializer.data)
    
    def post(self, request: Request) -> Response:
        ''' Создание нового материала или обработка загрузки Excel файлов '''
        if 'file' in request.FILES or 'files' in request.FILES:
            files = request.FILES.getlist('file') or request.FILES.getlist('files')
            errors = []

            for file in files:
                if file.name.endswith('.xlsx'):
                    try:
                        parser = ExcelParser(file)
                        parsed_data = parser.parse(2)

                        serializer = MaterialSerializer(data=parsed_data, many=True)
                        if serializer.is_valid():
                            serializer.save()
                        else:
                            errors.append(serializer.errors)
                    except Exception as e:
                        errors.append(str(e))
                else:
                    errors.append(f"Неподдерживаемый формат файла: {file.name}")

            if errors:
                return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'detail': 'Materials created successfully'}, status=status.HTTP_201_CREATED)
        
        serializer = MaterialSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(
        summary="Получение материала",
        description="Возвращает детальную информацию о материале по его идентификатору.",
        responses={200: MaterialSerializer, 404: 'Material not found'}
    ),
    put=extend_schema(
        summary="Обновление материала",
        description="Полное обновление материала по его идентификатору.",
        responses={200: MaterialSerializer, 400: 'Ошибка валидации данных'}
    ),
    patch=extend_schema(
        summary="Частичное обновление материала",
        description="Частично обновляет материал по его идентификатору.",
        responses={200: MaterialSerializer, 400: 'Ошибка валидации данных'}
    ),
    delete=extend_schema(
        summary="Удаление материала",
        description="Удаляет материал по его идентификатору.",
        responses={204: 'Material deleted successfully', 404: 'Material not found'}
    )
)
class MaterialDetailView(APIView):
    def get_object(self, id: int):
        ''' Получение материала или 404 '''
        return get_object_or_404(Material, id=id)

    def get(self, request: Request, id: int) -> Response:
        ''' Получение материала '''
        material = self.get_object(id)
        serializer = MaterialSerializer(material)
        return Response(serializer.data)
    
    def put(self, request: Request, id: int) -> Response:
        ''' Обновление материала '''
        material = self.get_object(id)
        serializer = MaterialSerializer(material, data=request.data)
        if serializer.is_valid(): 
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request: Request, id: int) -> Response:
        ''' Частичное обновление материала '''
        material = self.get_object(id)
        serializer = MaterialSerializer(material, data=request.data, partial=True)
        if serializer.is_valid(): 
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request: Request, id: int) -> Response:
        ''' Удаление материала '''
        material = self.get_object(id)
        material.delete()
        return Response({'detail': 'Material deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(
        summary="Получение списка категорий",
        description="Возвращает список всех категорий с их материалами.",
        responses={200: CategorySerializer(many=True)}
    ),
    retrieve=extend_schema(
        summary="Получение категории по ID",
        description="Возвращает детальную информацию о категории и её материалах.",
        responses={200: CategorySerializer}
    ),
    create=extend_schema(
        summary="Создание новой категории",
        description="Создает новую категорию в базе данных.",
        responses={201: CategorySerializer, 400: 'Ошибка валидации данных'}
    ),
    update=extend_schema(
        summary="Полное обновление категории",
        description="Полностью обновляет данные категории.",
        responses={200: CategorySerializer, 400: 'Ошибка валидации данных'}
    ),
    partial_update=extend_schema(
        summary="Частичное обновление категории",
        description="Частично обновляет данные категории.",
        responses={200: CategorySerializer, 400: 'Ошибка валидации данных'}
    ),
    destroy=extend_schema(
        summary="Удаление категории",
        description="Удаляет категорию из базы данных.",
        responses={204: 'Category deleted successfully'}
    )
)
class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления категориями.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_queryset(self):
        """
        Переопределение метода для оптимизации запросов (только для категорий и их материалов).
        """
        return Category.objects.prefetch_related(
            Prefetch('materials')
        ).all()

    @extend_schema(
        summary="Получение категорий в виде дерева",
        description="Возвращает категории и их материалы в иерархической структуре.",
        responses={
            200: OpenApiResponse(
                response=CategoryTreeSerializer(many=True),
                description="Возвращает дерево категорий."
            )
        },
        examples=[
            OpenApiExample(
                'Category Tree Example',
                value=[
                    {
                        "id": 1,
                        "name": "Root Category",
                        "code": 1001,
                        "materials": [
                            {
                                "id": 10,
                                "category": 1,
                                "code": 5001,
                                "name": "Material 1",
                                "cost": "150.00"
                            }
                        ],
                        "children": [
                            {
                                "id": 2,
                                "name": "Child Category",
                                "code": 1002,
                                "materials": [],
                                "children": []
                            }
                        ]
                    }
                ],
                description='Example of a category tree structure'
            )
        ]
    )
    @action(detail=False, methods=['get'], url_path='tree')
    def tree(self, request):
        """
        Эндпоинт для вывода категорий в формате дерева.
        """
        categories = Category.objects.prefetch_related(
            Prefetch('materials'),
            Prefetch('children', queryset=Category.objects.prefetch_related('materials'))
        ).all()

        category_map = {category.id: category for category in categories}
        root_categories = []

        for category in categories:
            if category.parent_id:
                parent = category_map.get(category.parent_id)
                if not hasattr(parent, 'child_list'):
                    parent.child_list = []
                parent.child_list.append(category)
            else:
                root_categories.append(category)

        result = CategoryTreeSerializer(root_categories, many=True).data
        return Response(result)