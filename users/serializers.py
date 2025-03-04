from rest_framework import serializers
from django.contrib.auth import get_user_model,authenticate
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()
    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "full_name", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
     

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data["email"]
        password = data["password"]

        # Authenticate using email
        user = authenticate(username=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid email or password.")

        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data,
        }