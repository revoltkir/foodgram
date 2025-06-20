from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import RecipeViewSet
from django.conf import settings

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router.urls)),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]