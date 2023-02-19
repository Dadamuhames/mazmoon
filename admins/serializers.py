from .models import Translations, Languages
from rest_framework import serializers


class TranslationSerializer(serializers.ModelSerializer):
    group = serializers.ReadOnlyField(source='group.sub_text')

    class Meta:
        model = Translations
        fields = '__all__'

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

