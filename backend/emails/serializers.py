from rest_framework import serializers


class GenerateEmailSerializer(serializers.Serializer):
    sender_name = serializers.CharField(max_length=120)
    sender_role = serializers.CharField(max_length=120, required=False, allow_blank=True)
    recipient_name = serializers.CharField(max_length=120)
    recipient_role = serializers.CharField(max_length=120, required=False, allow_blank=True)
    company = serializers.CharField(max_length=120, required=False, allow_blank=True)
    purpose = serializers.CharField(max_length=500)
    key_points = serializers.CharField(max_length=2500)
    additional_context = serializers.CharField(required=False, allow_blank=True)
    call_to_action = serializers.CharField(max_length=500, required=False, allow_blank=True)
    tone = serializers.ChoiceField(
        choices=["Professional", "Friendly", "Persuasive", "Formal", "Concise"]
    )
    length = serializers.ChoiceField(choices=["Short", "Medium", "Long"])
    language = serializers.CharField(max_length=80, required=False, default="English")
