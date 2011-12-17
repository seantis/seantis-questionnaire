from django.db import models
from django.core.urlresolvers import reverse
from transmeta import TransMeta

class Page(models.Model):
    __metaclass__ = TransMeta

    slug = models.SlugField(unique=True, primary_key=True)
    title = models.CharField(max_length=256)
    body = models.TextField()
    public = models.BooleanField(default=True)

    def __unicode__(self):
        return u"Page[%s]" % self.slug

    def get_absolute_url(self):
        return reverse('page.views.page', kwargs={'page':self.slug})
        

    class Meta:
        pass
        translate = ('title','body',)
