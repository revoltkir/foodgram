from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.db import transaction

from drf_extra_fields.fields import Base64ImageField

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
    password2 = serializers.CharField(write_only=True, required=True,
                                      label='Подтверждение пароля')

    class Meta:
        model = FoodgramUser
        fields = ('email', 'username', 'first_name', 'last_name', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают."})
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
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(user=request.user, author=obj).exists()


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписок."""
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    author = serializers.PrimaryKeyRelatedField(queryset=FoodgramUser.objects.all())

    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, data):
        user = self.context['request'].user
        author = data['author']

        if user == author:
            raise serializers.ValidationError('Нельзя подписаться на самого себя.')

        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError('Вы уже подписаны на этого пользователя.')

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
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes_qs = obj.recipe_set.all()

        if limit and limit.isdigit():
            recipes_qs = recipes_qs[:int(limit)]

        serializer = RecipeShortSerializer(recipes_qs, many=True, context=self.context)
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
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(source='recipe_ingredients', many=True, read_only=True)
    author = UserSerializer(read_only=True)
    image = Base64ImageField()
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
        user = request.user
        return user.is_authenticated and Favorite.objects.filter(recipe=obj, user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        user = request.user
        return user.is_authenticated and ShoppingCart.objects.filter(recipe=obj, user=user).exists()


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

    def validate_amount(self, value):
        if value < 1:
            raise serializers.ValidationError('Количество должно быть больше 0.')
        return value


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField()

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
            raise serializers.ValidationError('Время приготовления не может быть меньше 1 минуты.')

        unique_ids = set()
        duplicates = []

        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            # Проверяем, что ингредиент существует в базе
            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise serializers.ValidationError(f'Ингредиент с id={ingredient_id} не найден.')
            if ingredient_id in unique_ids:
                duplicates.append(ingredient_id)
            else:
                unique_ids.add(ingredient_id)

        if duplicates:
            raise serializers.ValidationError(
                f'Ингредиенты {duplicates} повторяются. Увеличьте количество вместо дублирования.'
            )

        # Проверяем, что теги существуют
        for tag in tags:
            if not Tag.objects.filter(id=tag.id).exists():
                raise serializers.ValidationError(f'Тег с id={tag.id} не найден.')

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
    image = Base64ImageField()

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
        return RecipeShortSerializer(instance.recipe, context=self.context).data


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
        return RecipeShortSerializer(instance.recipe, context=self.context).data
