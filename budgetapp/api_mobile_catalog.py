"""Mobile sync pull/push API views for catalog entities."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from budgetapp.models import BillReminder, Budget, Category, Expense, SubExpense, Tag, TagTransfer

from .serializers_mobile import (
    MobileBillReminderPushItemSerializer,
    MobileBillReminderSyncSerializer,
    MobileCategoryPushItemSerializer,
    MobileCategorySyncSerializer,
    MobileExpensePushItemSerializer,
    MobileExpenseSyncSerializer,
    MobileSubExpensePushItemSerializer,
    MobileSubExpenseSyncSerializer,
    MobileTagPushItemSerializer,
    MobileTagSyncSerializer,
    MobileTagTransferPushItemSerializer,
    MobileTagTransferSyncSerializer,
    save_bill_reminder_for_user,
    save_category_for_user,
    save_tag_for_user,
)


def _parse_updated_after(raw: str | None) -> datetime | None:
    """Parse an ISO-8601 ``updated_after`` query parameter into an aware datetime."""
    if not raw:
        return None
    parsed = parse_datetime(raw)
    if parsed is None:
        return None
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _collect_unknown_category_ids(
    user: AbstractBaseUser,
    validated_items: list[dict[str, Any]],
) -> list[int]:
    """Return category ids referenced in push data that do not belong to the user."""
    unknown: list[int] = []
    for item in validated_items:
        cid = item.get("id")
        if cid is None:
            continue
        if not Category.objects.filter(pk=cid, user=user).exists():
            unknown.append(cid)
    return unknown


def _collect_unknown_tag_ids(
    user: AbstractBaseUser,
    validated_items: list[dict[str, Any]],
) -> list[int]:
    """Return tag ids referenced in push data that do not belong to the user."""
    unknown: list[int] = []
    for item in validated_items:
        tid = item.get("id")
        if tid is None:
            continue
        if not Tag.objects.filter(pk=tid, user=user).exists():
            unknown.append(tid)
    return unknown


def _collect_unknown_expense_ids(
    user: AbstractBaseUser,
    validated_items: list[dict[str, Any]],
) -> list[int]:
    """Return expense ids referenced in push data that do not belong to the user."""
    unknown: list[int] = []
    for item in validated_items:
        eid = item.get("id")
        if eid is None:
            continue
        if item.get("deleted") and not Expense.objects.filter(pk=eid).exists():
            continue
        if not Expense.objects.filter(pk=eid, budget__user=user).exists():
            unknown.append(eid)
    return unknown


def _collect_unknown_subexpense_ids(
    user: AbstractBaseUser,
    validated_items: list[dict[str, Any]],
) -> list[int]:
    """Return sub-expense ids referenced in push data that do not belong to the user."""
    unknown: list[int] = []
    for item in validated_items:
        sid = item.get("id")
        if sid is None:
            continue
        if item.get("deleted") and not SubExpense.objects.filter(pk=sid).exists():
            continue
        if not SubExpense.objects.filter(pk=sid, expense__budget__user=user).exists():
            unknown.append(sid)
    return unknown


def _collect_unknown_bill_reminder_ids(
    user: AbstractBaseUser,
    validated_items: list[dict[str, Any]],
) -> list[int]:
    """Return bill reminder ids referenced in push data that do not belong to the user."""
    unknown: list[int] = []
    for item in validated_items:
        rid = item.get("id")
        if rid is None:
            continue
        if item.get("deleted") and not BillReminder.objects.filter(pk=rid).exists():
            continue
        if not BillReminder.objects.filter(pk=rid, user=user).exists():
            unknown.append(rid)
    return unknown


class MobileCategoryPullView(APIView):
    """GET categories changed after optional ``?updated_after=`` timestamp."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Return categories for the authenticated user."""
        user = request.user
        qs = Category.objects.filter(user=user).order_by("updated_at", "id")
        updated_after = _parse_updated_after(request.query_params.get("updated_after"))
        if updated_after is not None:
            qs = qs.filter(updated_at__gt=updated_after)
        data = MobileCategorySyncSerializer(qs, many=True).data
        return Response({"categories": data})


class MobileCategoryPushView(APIView):
    """Apply category upserts from the mobile client."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Create or update categories from a JSON list under the ``categories`` key."""
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
        created_ids: list[int] = []
        server_ids: list[int] = []
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
    """GET tags changed after optional ``?updated_after=`` timestamp."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Return tags for the authenticated user."""
        user = request.user
        qs = Tag.objects.filter(user=user).order_by("updated_at", "id")
        updated_after = _parse_updated_after(request.query_params.get("updated_after"))
        if updated_after is not None:
            qs = qs.filter(updated_at__gt=updated_after)
        data = MobileTagSyncSerializer(qs, many=True).data
        return Response({"tags": data})


class MobileTagPushView(APIView):
    """Apply tag upserts from the mobile client."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Create or update tags from a JSON list under the ``tags`` key."""
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
        created_ids: list[int] = []
        server_ids: list[int] = []
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
    """GET expenses changed after optional ``?updated_after=`` timestamp."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Return expenses for budgets owned by the authenticated user."""
        user = request.user
        qs = (
            Expense.objects.filter(budget__user=user)
            .select_related("budget")
            .order_by("updated_at", "id")
        )
        updated_after = _parse_updated_after(request.query_params.get("updated_after"))
        if updated_after is not None:
            qs = qs.filter(updated_at__gt=updated_after)
        data = MobileExpenseSyncSerializer(qs, many=True).data
        return Response({"expenses": data})


class MobileExpensePushView(APIView):
    """Apply expense upserts and deletions from the mobile client."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Create, update, or delete expenses from a JSON list under ``expenses``."""
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
            if item.get("deleted"):
                continue
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
            brm = item.get("bill_reminder_id")
            if brm is not None and not BillReminder.objects.filter(pk=brm, user=user).exists():
                return Response(
                    {"detail": "Unknown bill_reminder_id.", "bill_reminder_id": brm},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        unknown = _collect_unknown_expense_ids(user, ser.validated_data)
        if unknown:
            return Response(
                {"detail": "Unknown expense id(s).", "unknown_ids": unknown},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_ids: list[int] = []
        server_ids: list[int] = []
        with transaction.atomic():
            for item in ser.validated_data:
                if item.get("deleted"):
                    eid = item["id"]
                    e = Expense.objects.filter(pk=eid, budget__user=user).first()
                    server_ids.append(eid)
                    if e is not None:
                        e.delete()
                    continue
                eid = item.get("id")
                budget = Budget.objects.get(pk=item["budget_id"], user=user)
                name = item["name"]
                amount = item["amount"]
                is_rec = item.get("is_recurring", False)
                cat = item.get("category_id")
                tag = item.get("tag_id")
                brm = item.get("bill_reminder_id")
                if eid is None:
                    e = Expense.objects.create(
                        budget=budget,
                        name=name,
                        amount=amount,
                        is_recurring=is_rec,
                        category_id=cat,
                        tag_foreign_key_id=tag,
                        bill_reminder_id=brm,
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
                    e.bill_reminder_id = brm
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
    """GET sub-expenses changed after optional ``?updated_after=`` timestamp."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Return sub-expenses for expenses owned by the authenticated user."""
        user = request.user
        qs = SubExpense.objects.filter(expense__budget__user=user).order_by("updated_at", "id")
        updated_after = _parse_updated_after(request.query_params.get("updated_after"))
        if updated_after is not None:
            qs = qs.filter(updated_at__gt=updated_after)
        data = MobileSubExpenseSyncSerializer(qs, many=True).data
        return Response({"sub_expenses": data})


class MobileSubExpensePushView(APIView):
    """Apply sub-expense upserts and deletions from the mobile client."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Create, update, or delete sub-expenses from a JSON list under ``sub_expenses``."""
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
            if item.get("deleted"):
                continue
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

        created_ids: list[int] = []
        server_ids: list[int] = []
        with transaction.atomic():
            for item in ser.validated_data:
                if item.get("deleted"):
                    sid = item["id"]
                    sub = SubExpense.objects.filter(pk=sid, expense__budget__user=user).first()
                    server_ids.append(sid)
                    if sub is not None:
                        sub.delete()
                    continue
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


class MobileBillReminderPullView(APIView):
    """GET bill reminders changed after optional ``?updated_after=`` timestamp."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Return bill reminders for the authenticated user."""
        user = request.user
        qs = BillReminder.objects.filter(user=user).order_by("updated_at", "id")
        updated_after = _parse_updated_after(request.query_params.get("updated_after"))
        if updated_after is not None:
            qs = qs.filter(updated_at__gt=updated_after)
        data = MobileBillReminderSyncSerializer(qs, many=True).data
        return Response({"bill_reminders": data})


class MobileBillReminderPushView(APIView):
    """Apply bill reminder upserts and deletions from the mobile client."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Create, update, or delete bill reminders from a JSON list under ``bill_reminders``."""
        user = request.user
        raw_list = request.data.get("bill_reminders")
        if not isinstance(raw_list, list):
            return Response(
                {"detail": "Expected key 'bill_reminders' with a list."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ser = MobileBillReminderPushItemSerializer(data=raw_list, many=True)
        ser.is_valid(raise_exception=True)
        unknown = _collect_unknown_bill_reminder_ids(user, ser.validated_data)
        if unknown:
            return Response(
                {"detail": "Unknown bill reminder id(s).", "unknown_ids": unknown},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for item in ser.validated_data:
            if item.get("deleted"):
                continue
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

        created_ids: list[int] = []
        server_ids: list[int] = []
        with transaction.atomic():
            for item in ser.validated_data:
                if item.get("deleted"):
                    rid = item["id"]
                    br = BillReminder.objects.filter(pk=rid, user=user).first()
                    server_ids.append(rid)
                    if br is not None:
                        br.delete()
                    continue
                obj, created = save_bill_reminder_for_user(user, item)
                if obj is None:
                    continue
                if created:
                    created_ids.append(obj.id)
                server_ids.append(obj.id)
        return Response(
            {"created_ids": created_ids, "server_ids": server_ids},
            status=status.HTTP_200_OK,
        )


class MobileTagTransferPullView(APIView):
    """GET tag transfers changed after optional ``?updated_after=`` timestamp."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Return tag transfers for budgets owned by the authenticated user."""
        user = request.user
        qs = (
            TagTransfer.objects.filter(budget__user=user)
            .select_related("budget", "from_tag", "to_tag")
            .order_by("updated_at", "id")
        )
        updated_after = _parse_updated_after(request.query_params.get("updated_after"))
        if updated_after is not None:
            qs = qs.filter(updated_at__gt=updated_after)
        data = MobileTagTransferSyncSerializer(qs, many=True).data
        return Response({"tag_transfers": data})


class MobileTagTransferPushView(APIView):
    """Apply tag-transfer upserts and deletions from the mobile client."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Create, update, or delete transfers under ``tag_transfers``."""
        user = request.user
        raw_list = request.data.get("tag_transfers")
        if not isinstance(raw_list, list):
            return Response(
                {"detail": "Expected key 'tag_transfers' with a list."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ser = MobileTagTransferPushItemSerializer(data=raw_list, many=True)
        ser.is_valid(raise_exception=True)

        for item in ser.validated_data:
            if item.get("deleted"):
                continue
            bid = item["budget_id"]
            if not Budget.objects.filter(pk=bid, user=user).exists():
                return Response(
                    {
                        "detail": "Unknown budget_id for this user.",
                        "budget_id": bid,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            for key in ("from_tag_id", "to_tag_id"):
                tid = item[key]
                if not Tag.objects.filter(pk=tid, user=user).exists():
                    return Response(
                        {"detail": f"Unknown {key}.", key: tid},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        for item in ser.validated_data:
            tid = item.get("id")
            if tid is None:
                continue
            if item.get("deleted") and not TagTransfer.objects.filter(pk=tid).exists():
                continue
            if not TagTransfer.objects.filter(pk=tid, budget__user=user).exists():
                return Response(
                    {"detail": "Unknown transfer id(s).", "unknown_ids": [tid]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        created_ids: list[int] = []
        server_ids: list[int] = []
        with transaction.atomic():
            for item in ser.validated_data:
                if item.get("deleted"):
                    tid = item["id"]
                    obj = TagTransfer.objects.filter(
                        pk=tid, budget__user=user
                    ).first()
                    server_ids.append(tid)
                    if obj is not None:
                        obj.delete()
                    continue
                budget = Budget.objects.get(pk=item["budget_id"], user=user)
                from_tag = Tag.objects.get(pk=item["from_tag_id"], user=user)
                to_tag = Tag.objects.get(pk=item["to_tag_id"], user=user)
                amount = item["amount"]
                note = item.get("note") or ""
                xfer_date = item.get("date")
                tid = item.get("id")
                if tid is None:
                    kwargs: dict[str, Any] = {
                        "budget": budget,
                        "from_tag": from_tag,
                        "to_tag": to_tag,
                        "amount": amount,
                        "note": note,
                    }
                    if xfer_date is not None:
                        kwargs["date"] = xfer_date
                    obj = TagTransfer(**kwargs)
                    obj.save()
                    created_ids.append(obj.id)
                    server_ids.append(obj.id)
                else:
                    obj = TagTransfer.objects.get(pk=tid, budget__user=user)
                    obj.budget = budget
                    obj.from_tag = from_tag
                    obj.to_tag = to_tag
                    obj.amount = amount
                    obj.note = note
                    if xfer_date is not None:
                        obj.date = xfer_date
                    obj.save()
                    server_ids.append(obj.id)
        return Response(
            {"created_ids": created_ids, "server_ids": server_ids},
            status=status.HTTP_200_OK,
        )
