from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from budgetapp.models import Budget, Category, Expense, SubExpense, Tag

from .serializers_mobile import (
    MobileCategoryPushItemSerializer,
    MobileCategorySyncSerializer,
    MobileExpensePushItemSerializer,
    MobileExpenseSyncSerializer,
    MobileSubExpensePushItemSerializer,
    MobileSubExpenseSyncSerializer,
    MobileTagPushItemSerializer,
    MobileTagSyncSerializer,
    save_category_for_user,
    save_tag_for_user,
)


def _parse_updated_after(raw):
    if not raw:
        return None
    parsed = parse_datetime(raw)
    if parsed is None:
        return None
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _collect_unknown_category_ids(user, validated_items):
    unknown = []
    for item in validated_items:
        cid = item.get("id")
        if cid is None:
            continue
        if not Category.objects.filter(pk=cid, user=user).exists():
            unknown.append(cid)
    return unknown


def _collect_unknown_tag_ids(user, validated_items):
    unknown = []
    for item in validated_items:
        tid = item.get("id")
        if tid is None:
            continue
        if not Tag.objects.filter(pk=tid, user=user).exists():
            unknown.append(tid)
    return unknown


def _collect_unknown_expense_ids(user, validated_items):
    unknown = []
    for item in validated_items:
        eid = item.get("id")
        if eid is None:
            continue
        if not Expense.objects.filter(pk=eid, budget__user=user).exists():
            unknown.append(eid)
    return unknown


def _collect_unknown_subexpense_ids(user, validated_items):
    unknown = []
    for item in validated_items:
        sid = item.get("id")
        if sid is None:
            continue
        if not SubExpense.objects.filter(pk=sid, expense__budget__user=user).exists():
            unknown.append(sid)
    return unknown


class MobileCategoryPullView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        qs = Category.objects.filter(user=user).order_by("updated_at", "id")
        updated_after = _parse_updated_after(request.query_params.get("updated_after"))
        if updated_after is not None:
            qs = qs.filter(updated_at__gt=updated_after)
        data = MobileCategorySyncSerializer(qs, many=True).data
        return Response({"categories": data})


class MobileCategoryPushView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        raw_list = request.data.get("categories")
        if not isinstance(raw_list, list):
            return Response(
                {"detail": "Expected key 'categories' with a list."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ser = MobileCategoryPushItemSerializer(data=raw_list, many=True)
        ser.is_valid(raise_exception=True)
        unknown = _collect_unknown_category_ids(user, ser.validated_data)
        if unknown:
            return Response(
                {"detail": "Unknown category id(s).", "unknown_ids": unknown},
                status=status.HTTP_400_BAD_REQUEST,
            )
        created_ids = []
        server_ids = []
        with transaction.atomic():
            for item in ser.validated_data:
                obj, created = save_category_for_user(user, item)
                if obj is None:
                    continue
                if created:
                    created_ids.append(obj.id)
                server_ids.append(obj.id)
        return Response(
            {"created_ids": created_ids, "server_ids": server_ids},
            status=status.HTTP_200_OK,
        )


class MobileTagPullView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        qs = Tag.objects.filter(user=user).order_by("updated_at", "id")
        updated_after = _parse_updated_after(request.query_params.get("updated_after"))
        if updated_after is not None:
            qs = qs.filter(updated_at__gt=updated_after)
        data = MobileTagSyncSerializer(qs, many=True).data
        return Response({"tags": data})


class MobileTagPushView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        raw_list = request.data.get("tags")
        if not isinstance(raw_list, list):
            return Response(
                {"detail": "Expected key 'tags' with a list."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ser = MobileTagPushItemSerializer(data=raw_list, many=True)
        ser.is_valid(raise_exception=True)
        unknown = _collect_unknown_tag_ids(user, ser.validated_data)
        if unknown:
            return Response(
                {"detail": "Unknown tag id(s).", "unknown_ids": unknown},
                status=status.HTTP_400_BAD_REQUEST,
            )
        created_ids = []
        server_ids = []
        with transaction.atomic():
            for item in ser.validated_data:
                obj, created = save_tag_for_user(user, item)
                if obj is None:
                    continue
                if created:
                    created_ids.append(obj.id)
                server_ids.append(obj.id)
        return Response(
            {"created_ids": created_ids, "server_ids": server_ids},
            status=status.HTTP_200_OK,
        )


class MobileExpensePullView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        qs = Expense.objects.filter(budget__user=user).select_related("budget").order_by(
            "updated_at", "id"
        )
        updated_after = _parse_updated_after(request.query_params.get("updated_after"))
        if updated_after is not None:
            qs = qs.filter(updated_at__gt=updated_after)
        data = MobileExpenseSyncSerializer(qs, many=True).data
        return Response({"expenses": data})


class MobileExpensePushView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        raw_list = request.data.get("expenses")
        if not isinstance(raw_list, list):
            return Response(
                {"detail": "Expected key 'expenses' with a list."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ser = MobileExpensePushItemSerializer(data=raw_list, many=True)
        ser.is_valid(raise_exception=True)

        for item in ser.validated_data:
            bid = item["budget_id"]
            if not Budget.objects.filter(pk=bid, user=user).exists():
                return Response(
                    {"detail": "Unknown budget_id for this user.", "budget_id": bid},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            cat = item.get("category_id")
            if cat is not None and not Category.objects.filter(pk=cat, user=user).exists():
                return Response(
                    {"detail": "Unknown category_id.", "category_id": cat},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            tag = item.get("tag_id")
            if tag is not None and not Tag.objects.filter(pk=tag, user=user).exists():
                return Response(
                    {"detail": "Unknown tag_id.", "tag_id": tag},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        unknown = _collect_unknown_expense_ids(user, ser.validated_data)
        if unknown:
            return Response(
                {"detail": "Unknown expense id(s).", "unknown_ids": unknown},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_ids = []
        server_ids = []
        with transaction.atomic():
            for item in ser.validated_data:
                eid = item.get("id")
                budget = Budget.objects.get(pk=item["budget_id"], user=user)
                name = item["name"]
                amount = item["amount"]
                is_rec = item.get("is_recurring", False)
                cat = item.get("category_id")
                tag = item.get("tag_id")
                if eid is None:
                    e = Expense.objects.create(
                        budget=budget,
                        name=name,
                        amount=amount,
                        is_recurring=is_rec,
                        category_id=cat,
                        tag_foreign_key_id=tag,
                    )
                    created_ids.append(e.id)
                    server_ids.append(e.id)
                else:
                    e = Expense.objects.get(pk=eid, budget__user=user)
                    e.budget = budget
                    e.name = name
                    e.amount = amount
                    e.is_recurring = is_rec
                    e.category_id = cat
                    e.tag_foreign_key_id = tag
                    e.save()
                    server_ids.append(e.id)
        return Response(
            {
                "created_ids": created_ids,
                "server_ids": server_ids,
            },
            status=status.HTTP_200_OK,
        )


class MobileSubExpensePullView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        qs = SubExpense.objects.filter(expense__budget__user=user).order_by(
            "updated_at", "id"
        )
        updated_after = _parse_updated_after(request.query_params.get("updated_after"))
        if updated_after is not None:
            qs = qs.filter(updated_at__gt=updated_after)
        data = MobileSubExpenseSyncSerializer(qs, many=True).data
        return Response({"sub_expenses": data})


class MobileSubExpensePushView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        raw_list = request.data.get("sub_expenses")
        if not isinstance(raw_list, list):
            return Response(
                {"detail": "Expected key 'sub_expenses' with a list."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ser = MobileSubExpensePushItemSerializer(data=raw_list, many=True)
        ser.is_valid(raise_exception=True)

        for item in ser.validated_data:
            exp_id = item["expense_id"]
            if not Expense.objects.filter(pk=exp_id, budget__user=user).exists():
                return Response(
                    {
                        "detail": "Unknown expense_id for this user.",
                        "expense_id": exp_id,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        unknown = _collect_unknown_subexpense_ids(user, ser.validated_data)
        if unknown:
            return Response(
                {"detail": "Unknown sub-expense id(s).", "unknown_ids": unknown},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_ids = []
        server_ids = []
        with transaction.atomic():
            for item in ser.validated_data:
                sid = item.get("id")
                expense = Expense.objects.get(pk=item["expense_id"], budget__user=user)
                name = item["name"]
                amount = item["amount"]
                is_ret = item.get("is_return", False)
                if sid is None:
                    sub = SubExpense.objects.create(
                        expense=expense,
                        name=name,
                        amount=amount,
                        is_return=is_ret,
                    )
                    created_ids.append(sub.id)
                    server_ids.append(sub.id)
                else:
                    sub = SubExpense.objects.get(pk=sid, expense__budget__user=user)
                    sub.expense = expense
                    sub.name = name
                    sub.amount = amount
                    sub.is_return = is_ret
                    sub.save()
                    server_ids.append(sub.id)
        return Response(
            {
                "created_ids": created_ids,
                "server_ids": server_ids,
            },
            status=status.HTTP_200_OK,
        )
