"""JSON output that never turns money into floating-point numbers.

DRF's serializers already return Decimal fields as strings ("125.50"), but plain Decimals
inside ordinary dicts (the dashboard totals, report rows, insight data) would be written
as JSON numbers (125.5), which is how rounding errors creep in. This renderer writes
every Decimal as a string, so the whole API follows the spec: money is always "125.50".
"""
from decimal import Decimal

from rest_framework.renderers import JSONRenderer
from rest_framework.utils.encoders import JSONEncoder


class MoneySafeEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


class MoneySafeJSONRenderer(JSONRenderer):
    encoder_class = MoneySafeEncoder