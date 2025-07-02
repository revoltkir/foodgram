from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.db import transaction

from api.fields import SmartImageField

from recipes.models import (
    Tag, Ingredient, RecipeIngredient,
    Recipe, Favorite, ShoppingCart
)
from users.models import FoodgramUser, Subscription


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор регистрации пользователя с валидацией пароля."""
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=FoodgramUser.objects.all())]
    )
    username = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=FoodgramUser.objects.all())]
    )
    password = serializers.CharField(write_only=True, required=True,
                                     validators=[validate_password])
    password2 = serializers.CharField(write_only=True,
                                      label='Подтверждение пароля')

    class Meta:
        model = FoodgramUser
        fields = (
            'email', 'username', 'first_name',
            'last_name', 'password', 'password2'
        )

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Пароли не совпадают."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = FoodgramUser(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя с флагом подписки."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = FoodgramUser
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or user.is_anonymous:
            return False

        # Кешируем author_id, на которых подписан текущий пользователь
        if not hasattr(self, '_subscribed_ids'):
            self._subscribed_ids = set(
                Subscription.objects.filter(user=user).values_list('author_id',
                                                                   flat=True)
            )
        return obj.id in self._subscribed_ids


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


class UserSubscriptionSerializer(UserSerializer):
    """Расширенный сериализатор пользователя с рецептами и количеством."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes_qs = obj.recipe_set.all()

        if limit and limit.isdigit():
            recipes_qs = recipes_qs[:int(limit)]

        serializer = RecipeShortSerializer(recipes_qs, many=True,
                                           context=self.context)
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipe_set.count()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(source='recipe_ingredients',
                                             many=True, read_only=True)
    author = UserSerializer(read_only=True)
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
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False

        if not hasattr(self, '_favorite_ids'):
            self._favorite_ids = set(
                Favorite.objects.filter(user=user).values_list('recipe_id',
                                                               flat=True)
            )

        return obj.id in self._favorite_ids

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False

        if not hasattr(self, '_shopping_cart_ids'):
            self._shopping_cart_ids = set(
                ShoppingCart.objects.filter(user=user).values_list('recipe_id',
                                                                   flat=True)
            )

        return obj.id in self._shopping_cart_ids


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
            raise serializers.ValidationError('Укажите хотя бы один тег.')
        if not ingredients:
            raise serializers.ValidationError('Укажите ингредиенты.')
        if cooking_time < 1:
            raise serializers.ValidationError(
                'Время приготовления должно быть не менее 1 минуты.')

        ids = [item['id'].id for item in ingredients]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.')

        return data

    @staticmethod
    def create_ingredients(recipe, ingredients):
        objs = [
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
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
