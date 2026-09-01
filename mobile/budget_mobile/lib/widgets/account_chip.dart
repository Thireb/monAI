import "package:flutter/material.dart";

import "../theme/minimal_theme.dart";

class AccountChip extends StatelessWidget {
  const AccountChip({
    super.key,
    required this.label,
    required this.selected,
    this.color,
    this.onTap,
  });

  final String label;
  final bool selected;
  final Color? color;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final accent = color ?? MinimalColors.primaryBlue;
    return FilterChip(
      label: Text(label),
      selected: selected,
      onSelected: onTap == null ? null : (_) => onTap!(),
      selectedColor: accent.withValues(alpha: 0.22),
      checkmarkColor: accent,
      labelStyle: TextStyle(
        fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
        color: MinimalColors.textPrimary,
      ),
      side: BorderSide(
        color: selected ? accent : MinimalColors.neutralGray,
      ),
    );
  }
}
