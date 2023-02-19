from .models import Category,  ShortApplication
from rest_framework import generics, views, pagination, filters
from .serializers import TranslationsSerializerBadVersion, StaticInformationSerializer, TranslationSerializer, LangsSerializer, AplicationSerializer
from admins.models import Articles, StaticInformation, Partners, Reviews, Translations, Languages
from rest_framework.response import Response
# Create your views here.


# pagination
class BasePagination(pagination.PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 1000


# static information
class StaticInfView(views.APIView):
    def get(self, request, format=None):
        try:
            obj = StaticInformation.objects.get(id=1)
        except:
            obj = StaticInformation.objects.create()

        ob = StaticInformation.objects.get_or_create(id=1)
        print(ob)

        serializer = StaticInformationSerializer(
            obj, context={'request': request})

        return Response(serializer.data)


# translations
class TranslationsView(views.APIView):
    def get(self, request, fromat=None):
        translations = Translations.objects.all()
        serializer = TranslationsSerializerBadVersion(
            translations, context={'request': request})
        return Response(serializer.data)


# langs list
class LangsList(generics.ListAPIView):
    queryset = Languages.objects.filter(active=True)
    serializer_class = LangsSerializer
    pagination_class = BasePagination


# add aplication
class AddAplication(generics.CreateAPIView):
    queryset = ShortApplication.objects.all()
    serializer_class = AplicationSerializer