import "package:flutter/material.dart";

import "../theme/minimal_theme.dart";
import "../utils/budget_format.dart";

class MoneyText extends StatelessWidget {
  const MoneyText(
    this.amount, {
    super.key,
    this.currency = "PKR",
    this.style,
  });

  final double amount;
  final String currency;
  final TextStyle? style;

  @override
  Widget build(BuildContext context) {
    final base = style ?? Theme.of(context).textTheme.titleMedium;
    return Text(
      formatMoneyLine(currency, amount),
      style: base?.copyWith(
        fontWeight: FontWeight.w700,
        color: MinimalColors.textPrimary,
      ),
    );
  }
}
