from django.db import models
from django.conf import settings
from imaging.legacy.models import Image
from imaging.fields import GalleryField
from django.db.models.signals import class_prepared

DEFAULT_IMAGING_SETTINGS = {
        'image_upload_path' : 'imaging_photos',
        }

try:
    IMAGING_SETTINGS = settings.IMAGING_SETTINGS
except AttributeError:
    IMAGING_SETTINGS = DEFAULT_IMAGING_SETTINGS

class GalleryAbstract(models.Model):
    order = models.PositiveIntegerField()

    def _get_foreign_models(self):
        '''Returns a list of all models that are referred in foreign keys'''
        result = []
        for field in self._meta.fields:
            if isinstance(field, models.ForeignKey):
                result.append({'name': field.name, 'model': field.related.parent_model})
        return result

    def __init__(self, *args, **kwargs):
        super(GalleryAbstract, self).__init__(*args, **kwargs)
        foreign_models = self._get_foreign_models()
        # we need to know which foreign keys relate to our image
        # and which to our gallery so we can later on sort them properly
        self._IMAGE_FIELD = None
        self._GALLERY = None
        for field in foreign_models:
            # if a model inherits from ImageAbstract it must be our image model
            if ImageAbstract in field['model'].__bases__:
                self._IMAGE_FIELD = field['name']
            # otherwise lets check if model has a GalleryField
            # TODO: add some hasattr/getattr checks in case something unexpected happens
            elif len(field['model']._meta.many_to_many):
                for f in field['model']._meta.many_to_many:
                    if isinstance(f, GalleryField):
                        self._GALLERY = field['name']

    def print_gallery_info(self):
        print "Gallery:", self._GALLERY, "Image:", self._IMAGE_FIELD

    class Meta:
        abstract = True
        auto_created = True # without this django admin won't show GalleryField!

class ImageAbstract(models.Model):
    image = models.ImageField(upload_to=IMAGING_SETTINGS['image_upload_path'])

    @classmethod
    def get_form(cls):
        '''
        This class method should return a custom modelform to use
        in imaging_gallery_iframe_form
        '''
        return False

    class Meta:
        abstract = True

def register_gallery(sender, **kwargs):
    if issubclass(sender, ImageAbstract):
        from imaging import galleries
        galleries.register(sender)

class_prepared.connect(register_gallery)
