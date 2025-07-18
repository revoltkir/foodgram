from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator
from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from api.fields import SmartImageField
from api.utils.auth_context_mixin import AuthContextMixin
from recipes.constants import NAME_MAX_LENGTH
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import FoodgramUser, Subscription


class CreateUserSerializer(serializers.ModelSerializer):
    """Регистрация пользователя с валидацией пароля"""
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=FoodgramUser.objects.all())]
    )
    username = serializers.CharField(
        required=True,
        max_length=NAME_MAX_LENGTH,
        validators=[
            UniqueValidator(queryset=FoodgramUser.objects.all()),
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message='Username содержит недопустимые символы.'
            )
        ]
    )
    first_name = serializers.CharField(required=True,
                                       max_length=NAME_MAX_LENGTH)
    last_name = serializers.CharField(required=True,
                                      max_length=NAME_MAX_LENGTH)
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )

    class Meta:
        model = FoodgramUser
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = FoodgramUser(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserInfoSerializer(AuthContextMixin, serializers.ModelSerializer):
    """Сериализатор пользователя с флагом подписки."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = SmartImageField(read_only=True, required=False, allow_null=True)

    class Meta:
        model = FoodgramUser
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar')

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if not instance.avatar:
            rep['avatar'] = None
        return rep

    def get_is_subscribed(self, obj):
        user = self.get_authenticated_user()
        if not user:
            return False
        return Subscription.objects.filter(user=user, author=obj).exists()


class SetUserAvatarSerializer(serializers.ModelSerializer):
    avatar = SmartImageField(
        required=True,
        error_messages={'required': 'Необходимо передать файл.'}
    )

    class Meta:
        model = FoodgramUser
        fields = ('avatar',)


class SetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True,
                                         validators=[validate_password])

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Текущий пароль неверный.")
        return value


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписок."""
    user = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    author = serializers.PrimaryKeyRelatedField(
        queryset=FoodgramUser.objects.all())

    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, data):
        user = self.context['request'].user
        author = data['author']

        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.')

        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя.')

        return data

    def create(self, validated_data):
        user = self.context['request'].user
        author = validated_data['author']
        subscription = Subscription.objects.create(user=user, author=author)
        return subscription


class UserSubscriptionSerializer(UserInfoSerializer):
    """Отображение подписки с информацией о пользователе + рецептах."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserInfoSerializer.Meta):
        fields = UserInfoSerializer.Meta.fields + (
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes_qs = obj.recipes.all()

        if limit and limit.isdigit():
            recipes_qs = recipes_qs[:int(limit)]

        serializer = RecipeShortSerializer(recipes_qs, many=True,
                                           context=self.context)
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для промежуточной модели ингредиента в рецепте."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(AuthContextMixin, serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(source='recipe_ingredients',
                                             many=True, read_only=True)
    author = UserInfoSerializer(read_only=True)
    image = SmartImageField(required=False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time',
            'is_favorited', 'is_in_shopping_cart',
        )

    def get_is_favorited(self, obj):
        user = self.get_authenticated_user()
        if not user:
            return False
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.get_authenticated_user()
        if not user:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()


class RecipeIngredientCreateSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        error_messages={'does_not_exist': 'Ингредиент не найден.'}
    )
    amount = serializers.IntegerField(
        min_value=1,
        error_messages={'min_value': 'Количество должно быть больше 0.'}
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        error_messages={
            'does_not_exist': 'Тег не найден.',
            'invalid': 'Невалидный id тега.'
        }
    )
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = SmartImageField(required=False)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def validate(self, data):
        tags = data.get('tags')
        ingredients = data.get('ingredients')
        cooking_time = data.get('cooking_time')

        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Укажите хотя бы один тег.'}
            )

        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                {'tags': 'Теги не должны повторяться.'}
            )

        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Укажите ингредиенты.'})

        ingredient_ids = [item['id'].id for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты не должны повторяться.'}
            )

        if cooking_time < 1:
            raise serializers.ValidationError(
                {
                    'cooking_time':
                        'Время приготовления должно быть не менее 1 минуты.'
                }
            )

        image = self.initial_data.get('image')
        if not image and not getattr(self.instance, 'image', None):
            raise serializers.ValidationError(
                {'image': 'Изображение обязательно.'}
            )
        return data

    @staticmethod
    def create_ingredients(recipe, ingredients):
        objs = [
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient_data['id'].id,
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients
        ]
        RecipeIngredient.objects.bulk_create(objs)

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        instance = super().update(instance, validated_data)
        instance.recipe_ingredients.all().delete()
        self.create_ingredients(instance, ingredients)
        instance.tags.set(tags)

        return instance

    def to_representation(self, instance):
        context = {'request': self.context.get('request')}
        return RecipeSerializer(instance, context=context).data


class RecipeShortSerializer(serializers.ModelSerializer):
    image = SmartImageField(required=False)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeLinkSerializer(serializers.Serializer):
    def to_representation(self, instance):
        request = self.context.get('request')
        return {
            'short-link': request.build_absolute_uri(
                instance.get_absolute_url())
        }


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в избранное.'
            )
        ]

    def to_representation(self, instance):
        return RecipeShortSerializer(instance.recipe,
                                     context=self.context).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в корзине.'
            )
        ]

    def to_representation(self, instance):
        return RecipeShortSerializer(instance.recipe,
                                     context=self.context).data
