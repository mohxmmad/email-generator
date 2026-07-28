from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from groq import APIError

from .serializers import GenerateEmailSerializer
from .services import generate_email


class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class GenerateEmailView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GenerateEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            generated = generate_email(serializer.validated_data)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except APIError as exc:
            return Response(
                {"detail": f"AI provider error: {str(exc)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(generated, status=status.HTTP_200_OK)
