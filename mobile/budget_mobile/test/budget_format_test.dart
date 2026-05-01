import "package:flutter_test/flutter_test.dart";

import "package:budget_mobile/utils/budget_format.dart";

void main() {
  group("formatBudgetMonthLabel", () {
    test("parses YYYY-MM-DD prefix", () {
      expect(formatBudgetMonthLabel("2025-03-01"), "March 2025");
    });

    test("trims whitespace", () {
      expect(formatBudgetMonthLabel("  2024-12-01  "), "December 2024");
    });

    test("returns original when unparseable", () {
      expect(formatBudgetMonthLabel("not-a-date"), "not-a-date");
    });
  });

  group("monthFirstDayIso", () {
    test("pads year and month", () {
      expect(monthFirstDayIso(DateTime(2025, 7, 15)), "2025-07-01");
    });
  });

  group("parseBudgetMonth", () {
    test("uses first 10 chars when long string", () {
      expect(
        parseBudgetMonth("2025-01-01T12:00:00Z"),
        DateTime(2025, 1, 1),
      );
    });

    test("returns null for invalid input", () {
      expect(parseBudgetMonth("xyz"), isNull);
    });
  });

  group("formatCurrencyAmount", () {
    test("adds thousands separators and two decimals", () {
      expect(formatCurrencyAmount(1234567.89), "1,234,567.89");
    });

    test("formats negative values", () {
      expect(formatCurrencyAmount(-99.5), "-99.50");
    });
  });

  group("formatMoneyLine", () {
    test("combines currency and amount", () {
      expect(formatMoneyLine("PKR", 1000), "PKR 1,000.00");
    });
  });
}
