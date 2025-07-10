from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response


class ItemActionMixin:
    """Миксин для добавления и удаления рецептов в избранное и корзину."""

    def get_recipe(self, model, pk):
        recipe_model = model._meta.get_field('recipe').related_model
        return get_object_or_404(recipe_model, pk=pk)

    def add_item(self, model, serializer_class, request, pk=None):
        recipe = self.get_recipe(model, pk)
        user = request.user
        if model.objects.filter(user=user, recipe=recipe).exists():
            return Response({'message': 'Рецепт уже добавлен'},
                            status=status.HTTP_400_BAD_REQUEST)
        model.objects.create(user=user, recipe=recipe)
        serializer = serializer_class(recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_item(self, model, request, pk=None):
        recipe = self.get_recipe(model, pk)
        item = model.objects.filter(user=request.user, recipe=recipe)
        if not item.exists():
            return Response({'message': 'Рецепт не найден в списке.'},
                            status=status.HTTP_400_BAD_REQUEST)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
