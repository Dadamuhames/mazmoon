from .models import ShortApplication
from rest_framework import serializers
from admins.models import Services, Languages, Translations, StaticInformation, MetaTags
from rest_framework import serializers
from django.conf import settings
from django.core.files.storage import default_storage
import os
from easy_thumbnails.templatetags.thumbnail import thumbnail_url, get_thumbnailer


class ThumbnailSerializer(serializers.BaseSerializer):
    def __init__(self, alias, instance=None, **kwargs):
        super().__init__(instance, **kwargs)
        self.alias = alias

    def to_representation(self, instance):
        alias = settings.THUMBNAIL_ALIASES.get('').get(self.alias)
        if alias is None:
            return None

        size = alias.get('size')[0]
        url = None

        if instance:
            orig_url = instance.path.split('.')
            thb_url = '.'.join(orig_url) + f'.{size}x{size}_q85.{orig_url[-1]}'
            if default_storage.exists(thb_url):
                print("if")
                last_url = instance.url.split('.')
                url = '.'.join(last_url) + f'.{size}x{size}_q85.{last_url[-1]}'
            else:
                print('else')
                url = get_thumbnailer(instance)[self.alias].url

        if url == '' or url is None:
            return None

        request = self.context.get('request', None)
        if request is not None:
            return request.build_absolute_uri(url)

        return url


# field lang serializer
class JsonFieldSerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        language = self.context['request'].headers.get('Language')
        default_lang = Languages.objects.filter(default=True).first().code

        if not language:
            language = default_lang

        data = instance.get(language)

        if data is None or data == '':
            data = instance.get(default_lang)

        return data


# meta serializer
class MetaFieldSerializer(serializers.ModelSerializer):
    meta_keys = JsonFieldSerializer()
    meta_deck = JsonFieldSerializer()

    class Meta:
        model = MetaTags
        exclude = ['id']


# aplicaiotn serializer
class AplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShortApplication
        fields = '__all__'


# services serilaizer
class ServisesSerializer(serializers.ModelSerializer):
    pass


# static information
class StaticInformationSerializer(serializers.ModelSerializer):
    title = JsonFieldSerializer()
    subtitle = JsonFieldSerializer()
    deskription = JsonFieldSerializer()
    about_us = JsonFieldSerializer()
    adres = JsonFieldSerializer()
    work_time = JsonFieldSerializer()
    logo_first = ThumbnailSerializer(alias='prod_photo')
    logo_second = ThumbnailSerializer(alias='prod_photo')

    class Meta:
        model = StaticInformation
        exclude = ['id']


# translation serializer
class TranslationSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = {}

        for item in instance:
            val = JsonFieldSerializer(item.value, context={'request': self.context.get('request')}).data
            key = str(item.group.sub_text) + '.' + str(item.key)
            data[key] = val

        return data


# class TransaltionForDostonaka
class TranslationsSerializerBadVersion(serializers.Serializer):
    def to_representation(self, instance):
        data = {}
        languages = Languages.objects.filter(active=True)
        def_lang = languages.filter(default=True).first()


        for lang in languages:
            data[lang.code] = {}
            new_data = {}
            for item in instance:
                val = item.value.get(lang.code, '')

                if val == '':
                    val = item.value.get(def_lang.code, None)
                    
                key = str(item.key)
                new_data[key] = val

            data[lang.code] = new_data

        return data


# langs serializer
class LangsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Languages
        fields = '__all__'
