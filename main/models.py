from django.db import models
from easy_thumbnails.fields import ThumbnailerImageField

# Create your models here.
# category
class Category(models.Model):
    name = models.JSONField('Name', blank=True, null=True)
    deckription = models.JSONField("Deckription", blank=True, null=True)
    icon = ThumbnailerImageField(upload_to='ctg_icons', blank=True, null=True)
    image = ThumbnailerImageField(upload_to='ctg_image', blank=True, null=True)
    cotalog = models.FileField(
        'Cotalog for download', upload_to='cotalog_fiels', blank=True, null=True)


# prodject
class Projects(models.Model):
    name = models.JSONField('Name', blank=True, null=True)
    description = models.JSONField('Desc', blank=True, null=True)
    logo = ThumbnailerImageField('Logo', upload_to='project_logos')
    image = ThumbnailerImageField(upload_to='project_images')
    categpries = models.ManyToManyField(Category, blank=True, null=True)


# short applications
class ShortApplication(models.Model):
    STATUS = [('На рассмотрении', "На рассмотрении"),
              ("Рассмотрено", "Рассмотрено"), ("Отклонено", "Отклонено")]
    TYPES = [(1, 'Веб и корпоративный'), (2, 'Bеб приложение'),
             (3, 'Мобильный'), (4, 'Брендинг логотипа')]
    BUGET = [(1, '300$'), (2, '500$ - 700$'), (3, '700$ - 1000$'), (4, 'Согласны')]

    full_name = models.CharField('Full name', max_length=255)
    nbm = models.CharField('Nbm', max_length=255)
    company = models.CharField('Company', max_length=255)
    status = models.CharField(
        'Status', default='На рассмотрении', max_length=255, choices=STATUS)
    type = models.CharField('Type', max_length=255, choices=TYPES)
    budget = models.CharField('Budget', max_length=255, choices=BUGET)
    project_idea = models.TextField('Idea', blank=True, null=True)
    know_about_you = models.TextField()
     