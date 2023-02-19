from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, FormView
from .models import Articles, Languages, Translations, TranlsationGroups, StaticInformation, ArticleCategories, Services
from .models import AboutUs, MetaTags, telephone_validator, Reviews, Partners
from main.models import ShortApplication
from .forms import LngForm, UserForm  # , ApplicationForm
from django.core.exceptions import ValidationError
import datetime
from django.db.models import Q
import json
from django.apps import apps
from django.http import JsonResponse, QueryDict, HttpResponseRedirect
from django.core.files.storage import default_storage
from .utils import *
from .serializers import TranslationSerializer
from django.contrib.auth.models import User
from django.contrib.auth import logout
# Create your views here.

# based list view


class BasedListView(ListView):
    search_fields = list()

    def search(self, queryset, fields: list, model, *args, **kwargs):
        query = self.request.GET.get("q", '')

        langs = Languages.objects.filter(active=True)
        endlist = list()

        if query == '':
            return queryset

        queryset = queryset.values()

        for field in fields:
            for item in queryset:
                for lang in langs:
                    if query.lower() in str(item.get(field, {}).get(lang.code, '')).lower():
                        if item['id'] not in [it['id'] for it in endlist]:
                            endlist.append(item)
                    continue

        queryset = list_of_dicts_to_queryset(endlist, model)

        return queryset

    def get_queryset(self):
        queryset = self.model.objects.order_by('-id')
        queryset = self.search(queryset, self.search_fields, self.model)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(BasedListView, self).get_context_data(**kwargs)

        context['objects'] = get_lst_data(
            self.get_queryset(), self.request, 20)
        context['lang'] = Languages.objects.filter(
            active=True).filter(default=True).first()
        context['page_obj'] = paginate(self.get_queryset(), self.request, 20)
        context['url'] = search_pagination(self.request)

        return context


# based create view
class BasedCreateView(CreateView):
    related_model = None
    related_model_varb_name = None
    fields = '__all__'

    def get_context_data(self, **kwargs):
        context = super(BasedCreateView, self).get_context_data(**kwargs)
        context['langs'] = Languages.objects.filter(
            active=True).order_by('-default')
        context['lang'] = Languages.objects.filter(default=True).first()

        if self.related_model is not None:
            context['relateds'] = self.related_model.objects.order_by('-id')

        context['dropzone_key'] = self.model._meta.verbose_name
        context['images'] = []

        if self.request.session.get(context['dropzone_key']):
            context['images'] = list({'name': it['name'], 'id': clean_text(
                it['name'])} for it in self.request.session[context['dropzone_key']] if it['id'] == '')

        return context

    def form_valid(self, form):
        return None


# home admin
def home(request):
    return render(request, 'admin/base_template.html')


# delete model item
def delete_item(request):
    model_name = request.POST.get("model_name_del")
    app_name = request.POST.get('app_name_del')
    id = request.POST.get('item_id')
    url = request.POST.get("url")

    try:
        model = apps.get_model(model_name=model_name, app_label=app_name)
        model.objects.get(id=int(id)).delete()
    except:
        pass

    return redirect(url)


def delete_alot(request):
    model_name = request.POST.get("model_name")
    app_name = request.POST.get('app_name')
    id_list = request.POST.getlist('id')

    url = request.POST.get('url')

    try:
        model = apps.get_model(model_name=model_name, app_label=app_name)
        for item in id_list:
            if f'id[{item}]' in request.POST:
                model.objects.get(id=int(item)).delete()
    except:
        pass

    return redirect(url)


# save images
def save_images(request):
    if request.method == 'POST':
        key = request.POST.get("key")
        file = request.FILES.get('file')
        id = request.POST.get("id")

        request.session[key] = request.session.get(key, [])
        file_name = default_storage.save('dropzone/' + file.name, file)

        data = {
            'id': id,
            'name': file_name
        }

        request.session[key].append(data)
        request.session.modified = True

    return JsonResponse(file_name, safe=False)


# del lang icond
def del_lang_icon(request):
    id = request.POST.get("item_id")
    url = request.POST.get('url')
    try:
        Languages.objects.get(id=int(id)).icon.delete()
    except:
        pass

    return redirect(url)


# delete article group image
def delete_article_group_img(request):
    id = request.POST.get('item_id')

    try:
        ArticleCategories.objects.get(id=int(id)).image.delete()
    except:
        return JsonResponse("error", safe=False)

    return JsonResponse('success', safe=False)


# add static image
def add_static_image(request):
    url = request.POST.get('url')
    key = request.POST.get("key")
    file = request.FILES.get('file')

    try:
        model = StaticInformation.objects.get(id=1)

        if key == 'logo1':
            model.logo_first = file
        elif key == 'logo2':
            model.logo_second = file

        model.save()
    except:
        pass

    return redirect(url)


# delete article images
def del_statics_image(request):
    url = request.POST.get('url')
    key = request.POST.get("key")

    try:
        model = StaticInformation.objects.get(id=1)

        if key == 'logo1':
            model.logo_first.delete()
        elif key == 'logo2':
            model.logo_second.delete()
        elif key == 'cotalog':
            model.cotalog.delete()

        model.save()
    except:
        pass

    return redirect(url)


# delete image
def delete_image(request):
    if request.method == 'POST':
        key = request.POST.get('key')
        file = request.POST.get("file")

        if request.session.get(key):
            for it in request.session[key]:
                if it['name'] == file:
                    request.session[key].remove(it)
                    request.session.modified = True

    return redirect(request.META.get("HTTP_REFERER"))


# articles create
class ArticleCreateView(BasedCreateView):
    model = Articles
    template_name = 'admin/new_article.html'
    success_url = 'articles_list'
    related_model = ArticleCategories

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        data_dict = serialize_request(self.model, request)
        data_dict['created_date'] = data_dict.get(
            'created_date', str(datetime.date.today()))
        data_dict['author'] = request.user
        key = request.POST.get('dropzone-key')
        categories = request.POST.getlist('categories[]')

        data = self.get_context_data()

        if is_valid_field(data_dict, 'title') == False:
            data['request_post'] = data_dict
            data['error'] = 'This field is required.'
            return render(request, self.template_name, data)

        try:
            article = Articles(**data_dict)
            article.full_clean()
            article.save()
            if categories:
                ctg_queryset = [ArticleCategories.objects.get(
                    id=int(it)) for it in categories]
                article.category.set(ctg_queryset)

            key = self.model._meta.verbose_name
            sess_images = request.session.get(key)

            if sess_images and len([it for it in request.session.get(key) if it['id'] == '']) > 0:
                image = [it for it in request.session.get(
                    key) if it['id'] == ''][0]

                article.image = image['name']
                article.save()
                request.session.get(key).remove(image)
                request.session.modified = True

            meta_dict = serialize_request(MetaTags, request)
            try:
                meta = MetaTags(**meta_dict)
                meta.full_clean()
                meta.save()
                article.meta = meta
                article.save()
            except:
                pass

            article.save()

        except ValidationError:
            print(ValidationError)

        return redirect('articles_list')  # redirect("")


# articles list
class ArticlesList(BasedListView):
    model = Articles
    template_name = 'admin/articles_list.html'
    search_fields = ['title', 'body']


# article update
class ArticleUpdate(UpdateView):
    model = Articles
    template_name = 'admin/new_article.html'
    success_url = 'articles_list'
    fields = '__all__'

    def get_context_data(self, **kwargs):
        context = super(ArticleUpdate, self).get_context_data(**kwargs)
        context['langs'] = Languages.objects.filter(
            active=True).order_by('-default')
        context['lang'] = Languages.objects.filter(default=True).first()
        context['relateds'] = ArticleCategories.objects.order_by('-id')
        context['dropzone_key'] = self.model._meta.verbose_name

        return context

    def post(self, request, *args, **kwargs):
        context = super().post(request, *args, **kwargs)
        data_dict = serialize_request(self.model, request)
        url = request.POST.get("url")
        key = self.model._meta.verbose_name

        data = self.get_context_data()
        if is_valid_field(data_dict, 'title') == False:
            data['request_post'] = data_dict
            data['error'] = 'This field is required.'
            return render(request, self.template_name, data)

        try:
            file = [it for it in request.session.get(
                key, []) if it['id'] == str(self.get_object().pk)][0]
        except:
            file = None
        categories = request.POST.getlist('categories[]')

        try:
            instance = self.get_object()

            for attr, value in data_dict.items():
                setattr(instance, attr, value)

            instance.save()

            if categories:
                ctg_queryset = [ArticleCategories.objects.get(
                    id=int(it)) for it in categories]
                instance.category.set(ctg_queryset)

            if file:
                instance.image = file['name']
                for it in request.session.get(key):
                    if it['id'] == str(self.get_object().pk):
                        try:
                            request.session.get(key).remove(it)
                            request.session.modified = True
                        except:
                            pass
                instance.save()

            meta_dict = serialize_request(MetaTags, request)
            meta = instance.meta
            if meta is None:
                meta = MetaTags.objects.create()
                instance.meta = meta
                instance.save()

            try:
                for attr, value in meta_dict.items():
                    if str(attr) != 'id':
                        setattr(instance.meta, attr, value)
                instance.meta.save()
            except:
                pass

        except ValidationError:
            print(ValidationError)

        return redirect('articles_list')


# langs list
class LangsList(ListView):
    model = Languages
    context_object_name = 'langs'
    template_name = 'admin/lang_list.html'

    def get_queryset(self):
        queryset = Languages.objects.all().order_by('-default')
        query = self.request.GET.get("q")
        if query == '':
            query = None

        if query:
            queryset = queryset.filter(
                Q(name__iregex=query) | Q(code__iregex=query))
        return queryset

    def get_context_data(self, **kwargs):
        context = super(LangsList, self).get_context_data(**kwargs)
        context['q'] = self.request.GET.get("q")
        context['langs'] = get_lst_data(self.get_queryset(), self.request, 20)
        context['page_obj'] = paginate(self.get_queryset(), self.request, 20)
        context['url'] = search_pagination(self.request)

        return context


# langs create
class LngCreateView(CreateView):
    model = Languages
    form_class = LngForm
    success_url = '/admin/langs'
    template_name = "admin/lng_create.html"

    def form_valid(self, form):
        lang_save(form, self.request)

        return redirect('langs_list')

    def get_context_data(self, **kwargs):
        context = super(LngCreateView, self).get_context_data(**kwargs)
        context['dropzone_key'] = self.model._meta.verbose_name
        context['images'] = []

        if self.request.session.get(context['dropzone_key']):
            context['images'] = list({'name': it['name'], 'id': clean_text(str(
                it['name']))} for it in self.request.session[context['dropzone_key']] if it['id'] == '')

        return context


# langs update
class LangsUpdate(UpdateView):
    model = Languages
    form_class = LngForm
    success_url = '/admin/langs'
    template_name = "admin/lng_create.html"

    def get_context_data(self, **kwargs):
        context = super(LangsUpdate, self).get_context_data(**kwargs)
        context['dropzone_key'] = self.model._meta.verbose_name

        return context

    def form_valid(self, form):
        lang_save(form, self.request)

        return redirect('langs_list')


# langs delete
def delete_langs(request):
    if request.method == 'POST':
        lng_id = request.POST.get("id")
        try:
            Languages.objects.get(id=int(lng_id)).delete()
        except:
            pass

        url = request.POST.get("url", request.META.get('HTTP_REFERER'))

        return redirect(url)


# static update
class StaticUpdate(UpdateView):
    model = StaticInformation
    fields = "__all__"
    template_name = 'admin/static_add.html'
    success_url = '/admin/'

    def get_object(self):
        try:
            object = StaticInformation.objects.get(id=1)
        except:
            object = StaticInformation.objects.create()

        return object

    def get_context_data(self, **kwargs):
        context = super(StaticUpdate, self).get_context_data(**kwargs)
        context['langs'] = Languages.objects.filter(
            active=True).order_by('-default')
        context['dropzone_key'] = self.model._meta.verbose_name

        return context

    def form_valid(self, form):
        return None

    def post(self, request, *args, **kwargs):
        context = super().post(request, *args, **kwargs)
        data_dict = serialize_request(StaticInformation, request)
        instance = self.get_object()
        cotalog = request.FILES.get("cotalog")

        data = self.get_context_data()
        if is_valid_field(data_dict, 'title') == False:
            data['request_post'] = data_dict
            data['error'] = 'This field is required'
            return render(request, self.template_name, data)
        else:
            try:
                for attr, value in data_dict.items():
                    setattr(instance, attr, value)

                if cotalog:
                    instance.cotalog = cotalog

                instance.save()
            except:
                data['request_post'] = data_dict
                data['error_all'] = 'There is some errors'
                return render(request, self.template_name, data)

        return redirect('static_info')


# translations list
class TranslationList(ListView):
    model = Translations
    template_name = 'admin/translation_list.html'

    def get_queryset(self):
        queryset = Translations.objects.order_by("-id")
        query = self.request.GET.get("q")
        queryset = search_translation(query, queryset)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(TranslationList, self).get_context_data(**kwargs)
        context['groups'] = TranlsationGroups.objects.all()
        context['langs'] = Languages.objects.filter(
            active=True).order_by('-default')
        context['url'] = search_pagination(self.request)

        # pagination
        context['translations'] = get_lst_data(
            self.get_queryset(), self.request, 20)
        context['page_obj'] = paginate(self.get_queryset(), self.request, 20)

        return context


# translation group
class TranslationGroupDetail(DetailView):
    model = TranlsationGroups
    template_name = 'admin/translation_list.html'

    def get_context_data(self, **kwargs):
        context = super(TranslationGroupDetail,
                        self).get_context_data(**kwargs)
        context['groups'] = TranlsationGroups.objects.all()
        context['langs'] = Languages.objects.filter(
            active=True).order_by('-default')
        lst_one = self.get_object().translations.order_by('-id')

        # search
        query = self.request.GET.get("q")
        lst_one = search_translation(query, lst_one)

        # range
        lst_two = range(1, len(lst_one) + 1)

        # zip 2 lst
        context['translations'] = dict(pairs=zip(lst_one, lst_two))

        return context


# transtion update
def translation_update(request):
    if request.method == 'GET':
        id = request.GET.get('id')

        try:
            translation = Translations.objects.get(id=int(id))
            serializer = TranslationSerializer(translation)

            return JsonResponse(serializer.data)
        except:
            return JsonResponse({'error': 'error'}, safe=False)

    elif request.method == 'POST':
        data = serialize_request(Translations, request)
        id = request.POST.get("id")
        lang = Languages.objects.filter(
            active=True).filter(default=True).first()

        if data.get('value').get(lang.code, '') == '':
            return JsonResponse({'lng_error': 'This language is required'})

        try:
            translation = Translations.objects.get(id=int(id))
            key = data.get('key', '')

            if key == '':
                return JsonResponse({'key_error': 'Key is required'})

            if str(key) in [str(it.key) for it in Translations.objects.exclude(id=translation.pk)]:
                return JsonResponse({'key_error': 'Key is already in use'})

            translation.key = key
            translation.value = data['value']
            translation.full_clean()
            translation.save()
        except:
            return JsonResponse('some error', safe=False)

        serializer = TranslationSerializer(translation)

        return JsonResponse(serializer.data)


# add translation group
def add_trans_group(request):
    if request.method == 'POST':
        data_dict = serialize_request(TranlsationGroups, request)

        if data_dict.get('sub_text', '') == '':
            return JsonResponse({'key_error': 'Sub text is required'})
        elif (data_dict.get('sub_text'), ) in TranlsationGroups.objects.values_list('sub_text'):
            return JsonResponse({'key_error': 'This key is already in use'})

        try:
            transl_group = TranlsationGroups(**data_dict)
            transl_group.full_clean()
            transl_group.save()
        except ValidationError:
            return JsonResponse({'title_error': 'This title is empty or already in use'})

        data = {
            'id': transl_group.id,
            'name': transl_group.title,
            'key': transl_group.sub_text
        }
        return JsonResponse(data)


# translation group udate
class TranslationGroupUdpate(UpdateView):
    model = TranlsationGroups
    template_name = 'admin/translation_edit.html'
    fields = '__all__'
    success_url = '/admin/translations'

    def get_context_data(self, **kwargs):
        context = super(TranslationGroupUdpate,
                        self).get_context_data(**kwargs)
        context['groups'] = TranlsationGroups.objects.all()
        context['langs'] = Languages.objects.filter(
            active=True).order_by('-default')
        context['lng'] = Languages.objects.filter(
            active=True).filter(default=True).first()
        lst_one = self.get_object().translations.all()

        # range
        lst_two = range(1, len(lst_one) + 1)

        # zip 2 lst
        context['translations'] = dict(pairs=zip(lst_one, lst_two))

        return context

    def post(self, request, *args, **kwargs):
        transls = list(self.get_object().translations.all())
        langs = Languages.objects.filter(active=True).order_by('-default')
        lang = Languages.objects.filter(
            active=True).filter(default=True).first()
        items_count = request.POST.get("item_count")

        data = []
        for l in range(1, int(items_count) + 1):
            new_data = {}
            new_data['id'] = l
            new_data['key'] = request.POST[f'key[{l}]']
            new_data['values'] = []
            for lng in langs:
                new_data['values'].append(
                    {'key': f'value[{l}][{lng.code}]', 'value': request.POST[f'value[{l}][{lng.code}]'], 'def_lang': lang.code, 'lng': lng.code})

            data.append(new_data)

        objects = dict(pairs=zip(data, list(range(1, int(items_count) + 1))))

        for i in range(len(transls)):
            transls[i].key = request.POST.get(f'key[{i + 1}]', '')

            if transls[i].key == '':
                return render(request, template_name=self.template_name, context={'key_errors': {str(i+1): 'Key is required'},  'new_objects': objects, 'langs': langs, 'len': int(items_count) + 1})

            in_default_lng = request.POST.get(f'value[{i+1}][{lang.code}]', '')

            if in_default_lng == '':
                return render(request, template_name=self.template_name, context={'lng_errors': {str(i+1): 'This language is required'}, 'new_objects': objects, 'langs': langs, 'len': int(items_count) + 1})

            value_dict = {}
            for lang in langs:
                value_dict[str(lang.code)
                           ] = request.POST[f'value[{i + 1}][{lang.code}]']

            transls[i].value = value_dict
            try:
                transls[i].full_clean()
                transls[i].save()
            except:
                return render(request, template_name=self.template_name, context={'key_errors': {str(i): 'Key is alredy in use'},  'new_objects': objects, 'langs': langs, 'len': items_count})

        for i in range(len(transls) + 1, int(items_count) + 1):
            new_trans = Translations()
            data = {}
            new_trans.key = request.POST.get(f'key[{i}]', '')

            if new_trans.key == '':
                return render(request, template_name=self.template_name, context={'key_errors': {str(i): 'Key is required'},  'new_objects': objects, 'langs': langs, 'len': items_count})

            value_dict = {}
            in_default_lng = request.POST.get(f'value[{i}][{lang.code}]', '')

            if in_default_lng == '':
                return render(request, template_name=self.template_name, context={'lng_errors': {str(i): 'This language is required'}, 'new_objects': objects, 'langs': langs, 'len': items_count})

            for lang in langs:
                value_dict[str(lang.code)
                           ] = request.POST[f'value[{i}][{lang.code}]']

            new_trans.value = value_dict
            new_trans.group = self.get_object()

            try:
                new_trans.full_clean()
                new_trans.save()
            except:
                return render(request, template_name=self.template_name, context={'key_errors': {str(i): 'Key is alredy in use'}, 'new_objects': objects, 'langs': langs, 'len': items_count})

        return redirect('transl_group_detail', pk=self.get_object().id)


# article ctg list
class ArticleCtgList(BasedListView):
    model = ArticleCategories
    template_name = 'admin/article_ctg.lst.html'
    search_fields = ['name']


# add article ctg
class AddArticleCtg(BasedCreateView):
    model = ArticleCategories
    template_name = 'admin/article_ctg_form.html'
    fields = '__all__'
    success_url = 'article_ctg_list'
    related_model = ArticleCategories

    def form_valid(self, form):
        return None

    def post(self, request, *args, **kwargs):
        context = super().post(request, *args, **kwargs)
        data_dict = serialize_request(self.model, request)

        data = self.get_context_data()
        try:
            data_dict['parent'] = ArticleCategories.objects.get(
                id=int(data_dict.get('parent')))
        except:
            if data_dict.get("parent"):
                del data_dict['parent']

        if is_valid_field(data_dict, 'name') == False:
            data['request_post'] = data_dict
            data['error'] = 'This field is required.'
            return render(request, self.template_name, data)
        else:
            try:
                art_ctg = ArticleCategories(**data_dict)
                art_ctg.full_clean()
                art_ctg.save()

                key = self.model._meta.verbose_name
                sess_images = request.session.get(key)

                if sess_images and len([it for it in request.session.get(key) if it['id'] == '']) > 0:
                    image = [it for it in request.session.get(
                        key) if it['id'] == ''][0]

                    art_ctg.image = image['name']
                    art_ctg.save()
                    request.session.get(key).remove(image)
                    request.session.modified = True
            except:
                pass

        return redirect('article_ctg_list')


# article ctg edit
class ArticleCtgEdit(UpdateView):
    model = ArticleCategories
    fields = "__all__"
    template_name = 'admin/article_ctg_form.html'
    success_url = '/admin/article_categories'

    def get_context_data(self, **kwargs):
        context = super(ArticleCtgEdit, self).get_context_data(**kwargs)
        context['langs'] = Languages.objects.filter(
            active=True).order_by('-default')
        context['relateds'] = ArticleCategories.objects.exclude(
            id=self.get_object().id).order_by('-id')
        context['lang'] = Languages.objects.filter(
            active=True).filter(default=True).first()
        context['dropzone_key'] = self.model._meta.verbose_name

        return context

    def form_valid(self, form):
        return None

    def post(self, request, *args, **kwargs):
        context = super().post(request, *args, **kwargs)
        data_dict = serialize_request(self.model, self.request)
        key = self.model._meta.verbose_name
        try:
            file = [it for it in request.session.get(
                key, []) if it['id'] == str(self.get_object().id)][0]
        except:
            file = None

        try:
            data_dict['parent'] = ArticleCategories.objects.get(
                id=int(data_dict.get('parent')))
        except:
            if data_dict.get("parent"):
                del data_dict['parent']

        data = self.get_context_data()
        if is_valid_field(data_dict, 'name') == False:
            data['request_post'] = data_dict
            data['error'] = 'This field is required.'
            return render(request, self.template_name, data)

        instance = self.get_object()

        for attr, value in data_dict.items():
            setattr(instance, attr, value)

        instance.save()

        if file:
            instance.image = file['name']
            for it in request.session.get(key):
                if it['id'] == str(self.get_object().id):
                    try:
                        request.session.get(key).remove(it)
                        request.session.modified = True
                    except:
                        pass
            instance.save()

        return redirect('article_ctg_list')

# delete about us video


def delete_about_video(request):
    try:
        model = AboutUs.objects.get(id=1)
        model.video.delete()
    except:
        return JsonResponse("error", safe=False)

    return JsonResponse("success", safe=False)


# set about video
def set_about_video(request):
    video = request.FILES.get("file")
    try:
        model = AboutUs.objects.get(id=1)
    except:
        model = AboutUs().save()
        return JsonResponse({'error': 'error'})

    model.video = video
    model.save()

    return JsonResponse('success', safe=False)

# super users list


class AdminsList(BasedListView):
    model = User
    template_name = 'admin/moterators_list.html'

    def get_queryset(self):
        queryset = User.objects.filter(is_superuser=True)
        query = self.request.GET.get("q", '')

        if query != '':
            queryset = queryset.filter(Q(username__iregex=query) | Q(
                first_name__iregex=query) | Q(last_name__iregex=query))

        return queryset


# super user create
class AdminCreate(CreateView):
    model = User
    form_class = UserForm
    success_url = '/'
    template_name = 'admin/moder_form.html'

    def form_valid(self, form):
        new_user = form.save()
        new_user.is_superuser = True
        full_name = self.request.POST.get("name")

        if full_name:
            if len(full_name.split(' ')) == 1:
                new_user.first_name = full_name.split(' ')[0]

            if len(full_name.split(' ')) == 2:
                new_user.last_name = full_name.split(' ')[1]

        new_user.save()

        return redirect('admin_list')


# admin udate
class AdminUpdate(UpdateView):
    model = User
    form_class = UserForm
    success_url = '/'
    template_name = 'admin/moder_form.html'

    def get_context_data(self, **kwargs):
        context = super(AdminUpdate, self).get_context_data(**kwargs)
        context['full_name'] = None

        if self.get_object().first_name:
            context['full_name'] = self.get_object().first_name

        if self.get_object().last_name:
            context['full_name'] += self.get_object().last_name

        return context

    def form_valid(self, form):
        user = form.save()
        user.is_superuser = True
        full_name = self.request.POST.get("name")

        if full_name:
            if len(full_name.split(' ')) == 1:
                user.first_name = full_name.split(' ')[0]

            if len(full_name.split(' ')) == 2:
                user.last_name = full_name.split(' ')[1]

        user.save()

        return redirect('admin_list')


# del article image
def delete_article_image(request):
    id = request.POST.get("item_id")

    try:
        Articles.objects.get(id=int(id)).image.delete()
    except:
        return JsonResponse({'detail': 'error'})

    return JsonResponse('success', safe=False)


# quic applications
class ShortApplicationList(BasedListView):
    model = ShortApplication
    template_name = 'admin/short_apls.html'


# short application update
class ShortApplicationUpdate(UpdateView):
    model = ShortApplication
    fields = ['nbm', 'status']
    template_name = 'admin/short_apl_edit.html'
    success_url = '/admin/quick_applications'

    def get_context_data(self, **kwargs):
        context = super(ShortApplicationUpdate,
                        self).get_context_data(**kwargs)
        context['statuses'] = ["На рассмотрении", "Рассмотрено", "Отклонено"]
        context['lang'] = Languages.objects.filter(default=True).first()

        return context


# services list
class ServicesList(ListView):
    model = Services
    template_name = 'admin/services.html'

    def get_queryset(self):
        queryset = Services.objects.order_by("-id")
        queryset = search(self.request, queryset, [
                          'title', 'deckription', 'sub_title'], self.model)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(ServicesList, self).get_context_data(**kwargs)

        context['q'] = self.request.GET.get('q')
        context['lang'] = Languages.objects.filter(default=True).first()
        context['objects'] = get_lst_data(
            self.get_queryset(), self.request, 20)
        context['page_obj'] = paginate(self.get_queryset(), self.request, 20)
        context['url'] = search_pagination(self.request)

        return context


# services update
class ServicesUpdate(UpdateView):
    model = Services
    fields = '__all__'
    success_url = '/admin/services'
    template_name = 'admin/services_form.html'

    def get_context_data(self, **kwargs):
        context = super(ServicesUpdate, self).get_context_data(**kwargs)
        context['langs'] = Languages.objects.filter(
            active=True).order_by('-default')
        context['sevices'] = Services.objects.exclude(id=self.get_object().id).exclude(
            id__in=[it.id for it in self.get_object().children.all()])
        context['lang'] = Languages.objects.filter(
            active=True).filter(default=True).first()
        context['dropzone_key'] = self.model._meta.verbose_name

        return context

    def form_valid(self, form):
        return None

    def post(self, request, *args, **kwargs):
        context = super().post(request, *args, **kwargs)
        data_dict = serialize_request(self.model, request)
        url = request.POST.get("url")
        key = self.model._meta.verbose_name
        parent_id = request.POST.get('parent')

        data = self.get_context_data()
        if is_valid_field(data_dict, 'title') == False:
            data['request_post'] = data_dict
            data['error'] = 'This field is required.'
            return render(request, self.template_name, data)

        try:
            data_dict['parent'] = Services.objects.get(id=int(parent_id))
        except:
            pass

        try:
            file = [it for it in request.session.get(
                key, []) if it['id'] == str(self.get_object().id)][0]
        except:
            file = None

        instance = self.get_object()

        for attr, value in data_dict.items():
            setattr(instance, attr, value)

        instance.save()

        if file:
            instance.image = file['name']
            for it in request.session.get(key):
                if it['id'] == str(self.get_object().id):
                    try:
                        request.session.get(key).remove(it)
                        request.session.modified = True
                    except:
                        pass
            instance.save()

        meta_dict = serialize_request(MetaTags, request)
        try:
            for attr, value in meta_dict.items():
                if str(attr) != 'id':
                    setattr(instance.meta_field, attr, value)
            instance.meta_field.save()
        except:
            pass

        return redirect('services')


# services create
class ServiceCreate(CreateView):
    model = Services
    fields = "__all__"
    success_url = '/admin/sevices'
    template_name = 'admin/services_form.html'

    def get_context_data(self, **kwargs):
        context = super(ServiceCreate, self).get_context_data(**kwargs)
        context['langs'] = Languages.objects.filter(
            active=True).order_by('-default')
        context['sevices'] = Services.objects.all()
        context['lang'] = Languages.objects.filter(
            active=True).filter(default=True).first()
        context['dropzone_key'] = self.model._meta.verbose_name
        context['images'] = []

        if self.request.session.get(context['dropzone_key']):
            context['images'] = list({'name': it['name'], 'id': clean_text(str(
                it['name']))} for it in self.request.session[context['dropzone_key']] if it['id'] == '')

        return context

    def form_valid(self, form):
        return None

    def post(self, request, *args, **kwargs):
        context = super().post(request, *args, **kwargs)
        data_dict = serialize_request(self.model, request)
        key = self.model._meta.verbose_name

        data = self.get_context_data()

        if is_valid_field(data_dict, 'title') == False:
            print("if1")
            data['error'] = 'This field is required.'
            data['request_post'] = data_dict
            return render(request, self.template_name, data)

        parent_id = request.POST.get('parent')
        try:
            data_dict['parent'] = Services.objects.get(id=int(parent_id))
        except:
            pass
        print('else1')
        instance = Services(**data_dict)
        instance.full_clean()
        instance.save()

        sess_images = request.session.get(key)

        if sess_images and len([it for it in sess_images if it['id'] == '']) > 0:
            image = [it for it in sess_images if it['id'] == ''][0]
            instance.image = image['name']
            instance.save()
            request.session.get(key).remove(image)
            request.session.modified = True

        meta_dict = serialize_request(MetaTags, request)
        try:
            meta = MetaTags(**meta_dict)
            meta.full_clean()
            meta.save()
            instance.meta_field = meta
            instance.save()
        except:
            pass

        return redirect('services')  # redirect("")


def del_sev_image(request):
    id = request.POST.get('item_id')

    try:
        Services.objects.get(id=int(id)).image.delete()
    except:
        JsonResponse({'detail': 'error'})

    return JsonResponse('success', safe=False)

# class reviews list
class ReviewsList(BasedListView):
    model = Reviews
    template_name = 'admin/reviews_list.html'
    search_fields = ['title']


# reviews crete
class ReviewsCreate(BasedCreateView):
    model = Reviews
    fields = '__all__'
    template_name = 'admin/reviews_form.html'

    def post(self, request, *args, **kwargs):
        context = super().post(request, *args, **kwargs)
        data_dict = serialize_request(self.model, request)
        data = self.get_context_data()
        req_fields = ['title', 'text']

        for field in req_fields:
            if is_valid_field(data_dict, field) == False:
                data['request_post'] = data_dict
                data[f'{field}_error'] = 'This field is required.'
                return render(request, self.template_name, data)

        rating = data_dict.get('rating', 0)
        if type(rating) == float or int(rating) < 0 or int(rating) > 5:
            data['request_post'] = data_dict
            data['rating_error'] = 'Рейтинг должен быть натуральным числом в интервале от 0 до 5'
            return render(request, self.template_name, data)

        try:
            review = Reviews(**data_dict)
            review.full_clean()
            review.save()

            key = self.model._meta.verbose_name
            sess_images = request.session.get(key)

            if sess_images and len([it for it in request.session.get(key) if it['id'] == '']) > 0:
                image = [it for it in request.session.get(
                    key) if it['id'] == ''][0]

                review.image = image['name']
                review.save()
                request.session.get(key).remove(image)
                request.session.modified = True
        except:
            pass

        return redirect('review_list')


# reviews update
class ReviewsUpdate(UpdateView):
    model = Reviews
    fields = '__all__'
    template_name = 'admin/reviews_form.html'

    def get_context_data(self, **kwargs):
        context = super(ReviewsUpdate, self).get_context_data(**kwargs)
        context['langs'] = Languages.objects.filter(
            active=True).order_by('-default')
        context['dropzone_key'] = self.model._meta.verbose_name
        return context

    def form_valid(self, form):
        return None

    def post(self, request, *args, **kwargs):
        context = super().post(request, *args, **kwargs)
        data_dict = serialize_request(self.model, request)
        data = self.get_context_data()

        if is_valid_field(data_dict, 'title') == False:
            data['request_post'] = data_dict
            data['title_error'] = 'This field is required.'
            return render(request, self.template_name, data)

        if is_valid_field(data_dict, 'text') == False:
            data['request_post'] = data_dict
            data['text_error'] = 'This field is required.'
            return render(request, self.template_name, data)

        rating = data_dict.get('rating', 0)
        if type(rating) == float or int(rating) < 0 or int(rating) > 5:
            data['request_post'] = data_dict
            data['rating_error'] = 'Рейтинг должен быть натуральным числом в интервале от 0 до 5'
            return render(request, self.template_name, data)

        instance = self.get_object()
        key = self.model._meta.verbose_name

        for attr, value in data_dict.items():
            setattr(instance, attr, value)

        try:
            file = [it for it in request.session.get(
                key, []) if it['id'] == str(self.get_object().id)][0]
        except:
            file = None

        if file:
            instance.image = file['name']
            for it in request.session.get(key):
                if it['id'] == str(self.get_object().id):
                    try:
                        request.session.get(key).remove(it)
                        request.session.modified = True
                    except:
                        pass

        instance.save()

        return redirect("review_list")


# del review image
def delete_review_image(request):
    id = request.POST.get('obj_id')
    try:
        model = Reviews.objects.get(id=id)
        model.image.delete()
    except:
        return JsonResponse("error", safe=False)

    return JsonResponse("success", safe=False)


# logout
def logout_view(request):
    logout(request)

    return redirect('login_admin')


# partners
class PartnersList(BasedListView):
    model = Partners
    template_name = 'admin/partners.html'
    search_fields = ['name']


# partners create
class PartnersCreate(BasedCreateView):
    model = Partners
    fields = "__all__"
    template_name = 'admin/partners_form.html'

    def post(self, request, *args, **kwargs):
        context = super().post(request, *args, **kwargs)
        data_dict = serialize_request(self.model, request)
        data = self.get_context_data()

        if is_valid_field(data_dict, 'name') == False:
            data['request_post'] = data_dict
            data['name_error'] = 'This field is required.'
            return render(request, self.template_name, data)

        try:
            partner = Partners(**data_dict)
            partner.full_clean()
            partner.save()

            key = self.model._meta.verbose_name
            sess_images = request.session.get(key)
            images = [it for it in request.session.get(key) if it['id'] == '']

            if sess_images and len(images) > 0:
                image = images[0]

                partner.image = image['name']
                partner.save()
                request.session.get(key).remove(image)
                request.session.modified = True
        except:
            pass

        return redirect('partners_list')


# pertners eidt
class PartnersEdit(UpdateView):
    model = Partners
    fields = "__all__"
    template_name = 'admin/partners_form.html'

    def get_context_data(self, **kwargs):
        context = super(PartnersEdit, self).get_context_data(**kwargs)
        context['langs'] = Languages.objects.filter(
            active=True).order_by('-default')
        context['lang'] = Languages.objects.filter(default=True).first()
        context['dropzone_key'] = self.model._meta.verbose_name

        return context

    def form_valid(self, form):
        return None

    def post(self, request, *args, **kwargs):
        context = super().post(request, *args, **kwargs)
        data_dict = serialize_request(self.model, request)
        data = self.get_context_data()

        if is_valid_field(data_dict, 'name') == False:
            data['request_post'] = data_dict
            data['name_error'] = 'This field is required.'
            return render(request, self.template_name, data)

        instance = self.get_object()
        key = self.model._meta.verbose_name

        for attr, value in data_dict.items():
            setattr(instance, attr, value)

        try:
            file = [it for it in request.session.get(
                key, []) if it['id'] == str(self.get_object().id)][0]
        except:
            file = None

        if file:
            instance.image = file['name']
            for it in request.session.get(key):
                if it['id'] == str(self.get_object().id):
                    try:
                        request.session.get(key).remove(it)
                        request.session.modified = True
                    except:
                        pass

        instance.save()

        return redirect("partners_list")

