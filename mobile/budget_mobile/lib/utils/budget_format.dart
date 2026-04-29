const List<String> _monthNames = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

/// Human-readable label for stored budget month (`YYYY-MM-DD` or `YYYY-MM-01`).
String formatBudgetMonthLabel(String monthRaw) {
  final trimmed = monthRaw.trim();
  if (trimmed.length >= 10) {
    final parsed = DateTime.tryParse(trimmed.substring(0, 10));
    if (parsed != null) {
      return "${_monthNames[parsed.month - 1]} ${parsed.year}";
    }
  }
  final parsed = DateTime.tryParse(trimmed);
  if (parsed != null) {
    return "${_monthNames[parsed.month - 1]} ${parsed.year}";
  }
  return monthRaw;
}

/// First day of month as `YYYY-MM-DD` for API / DB.
String monthFirstDayIso(DateTime d) {
  final y = d.year.toString().padLeft(4, "0");
  final m = d.month.toString().padLeft(2, "0");
  return "$y-$m-01";
}

/// Parse stored month string to DateTime (first of month), or null.
DateTime? parseBudgetMonth(String monthRaw) {
  final t = monthRaw.trim();
  if (t.length >= 10) {
    return DateTime.tryParse(t.substring(0, 10));
  }
  return DateTime.tryParse(t);
}
