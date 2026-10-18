"""Query-string serializers for the dashboard, reports and insights endpoints."""
import calendar

from django.utils import timezone
from rest_framework import serializers


class PeriodSerializer(serializers.Serializer):
    """?start_date=&end_date= (send both or neither; neither means the current month)."""

    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)

    def validate(self, attrs):
        start, end = attrs.get("start_date"), attrs.get("end_date")
        if (start is None) != (end is None):
            raise serializers.ValidationError({"end_date": ["Send both start_date and end_date, or neither."]})
        if start and end and start > end:
            raise serializers.ValidationError({"start_date": ["Start date must not be after end date."]})
        return attrs

    def period(self):
        """(start, end) from the request, or the current month in the app's time zone."""
        v = self.validated_data
        if "start_date" in v:
            return v["start_date"], v["end_date"]
        today = timezone.localdate()
        last_day = calendar.monthrange(today.year, today.month)[1]
        return today.replace(day=1), today.replace(day=last_day)


class ReportQuerySerializer(PeriodSerializer):
    granularity = serializers.ChoiceField(choices=["day", "week", "month"], default="month")

    def validate(self, attrs):
        attrs = super().validate(attrs)
        start, end = attrs.get("start_date"), attrs.get("end_date")
        if start and end and attrs["granularity"] == "day" and (end - start).days > 366:
            raise serializers.ValidationError({"granularity": ["Daily detail is limited to one year. Use week or month."]})
        return attrs