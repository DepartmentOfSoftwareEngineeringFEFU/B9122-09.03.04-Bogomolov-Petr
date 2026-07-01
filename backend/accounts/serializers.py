from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    student_class_name = serializers.CharField(source='student_class.name', read_only=True, default=None)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'phone', 'role', 'role_display',
            'telegram_id', 'student_class', 'student_class_name', 'is_active',
        ]
        read_only_fields = ['id']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'phone', 'role', 'student_class', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
