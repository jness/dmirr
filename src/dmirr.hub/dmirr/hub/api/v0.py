
from django.conf.urls.defaults import url
from django.forms.models import ModelChoiceField

from tastypie import fields
from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import Authorization
from tastypie.validation import FormValidation
from tastypie.http import HttpUnauthorized
from tastypie.resources import ModelResource
from tastypie.api import Api
from tastypie.utils import trailing_slash

from dmirr.hub import db
from dmirr.hub.apps.projects.forms import ProjectForm
     

class dMirrValidation(FormValidation):
    """
    Override tastypie's standard ``FormValidation`` since this does not care
    about URI to PK conversion for ``ToOneField`` or ``ToManyField``.  Also
    properly handles unique fields on PUT.
    
    """

    def uri_to_pk(self, uri):
        """
        Returns the integer PK part of a URI.

        Assumes ``/api/v1/resource/123/`` format. If conversion fails, this just
        returns the URI unmodified.

        Also handles lists of URIs
        """

        if uri is None:
            return None

        # convert everything to lists
        multiple = not isinstance(uri, basestring)
        uris = uri if multiple else [uri]

        # handle all passed URIs
        converted = []
        for one_uri in uris:
            try:
                # hopefully /api/v1/<resource_name>/<pk>/
                converted.append(one_uri.split('/')[-2])
            except (IndexError, ValueError):
                raise ValueError(
                    "URI %s could not be converted to PK integer." % one_uri)

        # convert back to original format
        return converted if multiple else converted[0]

    def is_valid(self, bundle, request=None):
        data = bundle.data

        # Ensure we get a bound Form, regardless of the state of the bundle.
        if data is None:
            data = {}
            
        # copy data, so we don't modify the bundle
        data = data.copy()

        # convert URIs to PK integers for all relation fields
        relation_fields = [name for name, field in
                           self.form_class.base_fields.items()
                           if issubclass(field.__class__, ModelChoiceField)]

        for field in relation_fields:
            if field in data:
                data[field] = self.uri_to_pk(data[field])

        # validate and return messages on error
        if request.method == 'POST':    
            form = self.form_class(data)
        elif request.method == 'PUT':
            ### FIX ME: using resource_pk is a hack added in dehydrate()
            ### Look at: https://github.com/toastdriven/django-tastypie/issues/152
            obj = self.form_class.Meta.model.objects.get(pk=data['resource_pk'])
            form = self.form_class(data, instance=obj)
            
        if form.is_valid():
            return {}
            
        return form.errors
           

class dMirrAuthorization(Authorization):
    def __init__(self):
        super(dMirrAuthorization, self).__init__()
        
    def apply_limits(self, request, object_list):
        #request.user.has_perm('projects.change_project')
        return object_list
        
class dMirrAuthentication(ApiKeyAuthentication):
    def __init__(self):
        super(dMirrAuthentication, self).__init__()
        
    def is_authenticated(self, request, **kwargs):
        if request.user.is_authenticated():
            return True

        return super(dMirrAuthentication, self).is_authenticated(request, **kwargs)

class dMirrResource(ModelResource):    
    def dehydrate(self, bundle):
        bundle.data['resource_pk'] = bundle.obj.id
        return bundle

class UserResource(dMirrResource):    
    class Meta:
        queryset = db.User.objects.all()
        authentication = dMirrAuthentication()
        authorization = dMirrAuthorization()
        resource_name = 'users'
        excludes = ['email', 'password', 'is_active', 'is_staff', 'is_superuser']
        filtering = {}
        allowed_methods = ['get']
        
    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/schema%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/set/(?P<pk_list>\w[\w/;-]*)/$" % self._meta.resource_name, self.wrap_view('get_multiple'), name="api_get_multiple"),
            url(r"^(?P<resource_name>%s)/(?P<username>[a-zA-Z][\w\d\_\.\-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            
        ]
        
    def apply_authorization_limits(self, request, object_list):
        # just punt for now
        return object_list
    
        
class UserProfileResource(dMirrResource):
    user = fields.ToOneField(UserResource, 'user', full=True)
    
    class Meta:
        authentication = dMirrAuthentication()
        authorization = dMirrAuthorization()
        queryset = db.UserProfile.objects.all()
        resource_name = 'user_profiles'
        excludes = []
        filtering = {}
        allowed_methods = ['get']
        
    def apply_authorization_limits(self, request, object_list):
        # just punt for now
        return object_list
        
class ProjectResource(dMirrResource):
    user = fields.ToOneField(UserResource, 'user', full=True)
    
    class Meta:
        authentication = dMirrAuthentication()
        authorization = dMirrAuthorization()
        queryset = db.Project.objects.all()
        resource_name = 'projects'
        excludes = []
        filtering = {}
        allowed_methods = ['get']
        validation = dMirrValidation(form_class=ProjectForm)
        
    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<label>[a-zA-Z][\w\d_\.-]+)/$" % \
                self._meta.resource_name, 
                self.wrap_view('dispatch_detail'), 
                name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/schema%s$" % \
                (self._meta.resource_name, trailing_slash()), 
                self.wrap_view('get_schema'), 
                name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/set/(?P<pk_list>\w[\w/;-]*)/$" \
                % self._meta.resource_name, 
                self.wrap_view('get_multiple'), 
                name="api_get_multiple"),
            url(r"^(?P<resource_name>%s)/(?P<username>[a-zA-Z][\w\d_\.-]+)/$" \
                % self._meta.resource_name, self.wrap_view('dispatch_detail'), 
                  name="api_dispatch_detail"),
        ]
        
v0_api = Api(api_name='v0')
v0_api.register(UserResource())
v0_api.register(UserProfileResource())
v0_api.register(ProjectResource())
