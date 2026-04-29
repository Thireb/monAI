from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from budgetapp.models import Budget

from .serializers_mobile import MobileBudgetPushItemSerializer, MobileBudgetSyncSerializer


def _parse_updated_after(raw):
    if not raw:
        return None
    parsed = parse_datetime(raw)
    if parsed is None:
        return None
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


class MobileBudgetPullView(APIView):
    """GET budgets changed after optional ?updated_after= ISO-8601 (timezone-aware)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        qs = Budget.objects.filter(user=user).order_by("updated_at", "id")
        updated_after = _parse_updated_after(request.query_params.get("updated_after"))
        if updated_after is not None:
            qs = qs.filter(updated_at__gt=updated_after)
        data = MobileBudgetSyncSerializer(qs, many=True).data
        return Response({"budgets": data})


class MobileBudgetPushView(APIView):
    """Apply budget upserts from the mobile client (last-write-wins for v1)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        raw_list = request.data.get("budgets")
        if not isinstance(raw_list, list):
            return Response(
                {"detail": "Expected key 'budgets' with a list."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ser = MobileBudgetPushItemSerializer(data=raw_list, many=True)
        ser.is_valid(raise_exception=True)

        unknown_ids = []
        for item in ser.validated_data:
            budget_id = item.get("id")
            if budget_id is None:
                continue
            if not Budget.objects.filter(pk=budget_id, user=user).exists():
                unknown_ids.append(budget_id)
        if unknown_ids:
            return Response(
                {"detail": "Unknown budget id(s) for this user.", "unknown_ids": unknown_ids},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_ids = []
        updated_ids = []
        server_ids = []
        with transaction.atomic():
            for item in ser.validated_data:
                budget_id = item.get("id")
                month = item["month"]
                income = item["income"]
                currency = item["currency"]
                is_archived = item.get("is_archived", False)
                if budget_id is None:
                    b = Budget.objects.create(
                        user=user,
                        month=month,
                        income=income,
                        currency=currency,
                        is_archived=is_archived,
                    )
                    created_ids.append(b.id)
                    server_ids.append(b.id)
                else:
                    try:
                        b = Budget.objects.get(pk=budget_id, user=user)
                    except Budget.DoesNotExist:
                        continue
                    b.month = month
                    b.income = income
                    b.currency = currency
                    b.is_archived = is_archived
                    b.save()
                    updated_ids.append(b.id)
                    server_ids.append(b.id)
        return Response(
            {
                "created_ids": created_ids,
                "updated_ids": updated_ids,
                "server_ids": server_ids,
            },
            status=status.HTTP_200_OK,
        )
