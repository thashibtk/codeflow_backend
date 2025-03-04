from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import subprocess

class CodeExecutionView(APIView):
    def post(self, request):
        code = request.data.get("code", "")
        if not code:
            return Response({"error": "No code provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = subprocess.run(
                ["python3", "-c", code], capture_output=True, text=True, timeout=5
            )
            return Response({"output": result.stdout, "error": result.stderr})
        except subprocess.TimeoutExpired:
            return Response({"error": "Code execution timed out"}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
