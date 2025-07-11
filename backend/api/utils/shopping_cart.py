from django.db.models import F, Sum
from django.http import HttpResponse

from recipes.models import RecipeIngredient


def generate_shopping_cart_text(user):
    """
    Генерирует текстовый список покупок для пользователя по его корзине.
    Возвращает строку или None, если корзина пуста.
    """
    ingredients = (
        RecipeIngredient.objects
        .filter(recipe__shoppingcart__user=user)
        .values(
            name=F('ingredient__name'),
            unit=F('ingredient__measurement_unit')
        )
        .annotate(total_amount=Sum('amount'))
        .order_by('name')
    )

    if not ingredients:
        return None

    lines = ['Список покупок:\n']
    for item in ingredients:
        lines.append(f"• {item['name']} ({item['unit']})"
                     f" — {item['total_amount']}")
    return '\n'.join(lines)


def download_shopping_cart_response(user):
    """
    Возвращает HttpResponse с текстовым файлом списка покупок для пользователя.
    Если корзина пуста — возвращает None.
    """
    content = generate_shopping_cart_text(user)
    if not content:
        return None

    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = (
        'attachment; filename="shopping_list.txt"'
    )
    return response
