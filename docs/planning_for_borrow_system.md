# Debt System - Implementation Plan

## Overview

The Debt System allows users to track money borrowed from external sources (friends, family, banks, etc.) and manage repayments through their existing budget system. Users add expenses in monthly budgets using debt-specific tags, and the system automatically tracks repayment progress. When a debt is fully repaid, the tracking tag is automatically disabled while preserving historical data.

## Core Features

1. **Debt Creation**: Create debt records with automatic tag generation
2. **Flexible Borrowing**: Borrow money in multiple installments
3. **Natural Repayments**: Add expenses in monthly budgets using debt tags
4. **Automatic Progress Tracking**: System calculates repayment progress from expenses
5. **Tag Management**: Automatic tag disabling when debt is fully repaid
6. **Debt Management**: View all debts, active and completed

## Database Models

### 1. Debt Model
```python
class Debt(models.Model):
    name = models.CharField(max_length=200)  # e.g., "Motherboard Purchase"
    description = models.TextField(blank=True)  # e.g., "Borrowed from friend for new motherboard"
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)  # e.g., 27,000
    borrowed_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # e.g., 4,000
    debt_tag = models.ForeignKey(Tag, on_delete=models.PROTECT, related_name='debts')  # Auto-generated tag
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    @property
    def repaid_amount(self):
        """Calculate total repaid from expenses with this tag"""
        return self.debt_tag.expenses.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')

    @property
    def remaining_to_repay(self):
        return self.borrowed_amount - self.repaid_amount

    @property
    def repayment_progress_percentage(self):
        if self.borrowed_amount == 0:
            return 0
        return min(100, int((self.repaid_amount / self.borrowed_amount) * 100))

    @property
    def is_fully_repaid(self):
        return self.repaid_amount >= self.borrowed_amount
```

### 2. DebtTransaction Model
```python
class DebtTransaction(models.Model):
    debt = models.ForeignKey(Debt, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### 3. Tag Model Enhancement
```python
class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#2196f3")
    is_active = models.BooleanField(default=True)  # NEW FIELD for debt management
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

## Implementation Checklist

### Phase 1: Database and Models ✅
- [x] Create Debt model with automatic tag generation
- [x] Create DebtTransaction model
- [x] Add is_active field to Tag model
- [x] Add model properties (repaid_amount, remaining_to_repay, progress_percentage)
- [ ] Create database migrations
- [x] Register models in admin.py
- [x] Add automatic tag disabling logic

### Phase 2: Backend Views and Forms ✅
- [x] Create Django views for web interface
- [x] Create forms for debt creation and editing
- [x] Create forms for borrowing transactions
- [x] Add URL routing
- [x] Implement automatic tag generation in Debt.save()
- [x] Add automatic tag disabling when debt is fully repaid

### Phase 3: Frontend Templates ✅
- [x] Create debt list template (similar to goals)
- [x] Create debt detail template
- [x] Create debt creation form
- [x] Create debt editing form
- [x] Create borrowing transaction form
- [x] Add navigation link in base template

### Phase 4: JavaScript Functionality ✅
- [x] Create debt.js for form handling and UI interactions
- [x] Implement form validation
- [x] Add success/error notifications
- [x] Implement real-time progress updates
- [x] Add modal functionality for forms
- [x] Handle form submissions and page updates

### Phase 5: Styling and UI ✅
- [x] Create debt-specific CSS
- [x] Style debt cards and progress bars
- [x] Style forms and modals
- [x] Add responsive design
- [x] Implement consistent theme with existing UI
- [x] Add animations for interactions

### Phase 6: Integration and Testing ✅
- [x] Test debt creation workflow
- [x] Test borrowing transactions
- [x] Test automatic tag generation
- [x] Test progress calculations from expenses
- [x] Test edge cases (zero amounts, over-borrowing, etc.)
- [x] Test automatic tag disabling when debt is fully repaid
- [x] Test tag integration with existing expense system
- [x] Test form validation and error handling

### Phase 7: Documentation and Polish ✅
- [x] Create user documentation
- [x] Add inline code comments
- [x] Create usage examples
- [x] Add error handling improvements
- [x] Performance optimization
- [x] Modular file structure (separate CSS/JS files)
- [x] Clean up main budgetapp files (removed debt forms, views, URLs)
- [x] Create minimal/forms.py with debt forms
- [x] Fix linting issues (line length, template endblock names, inline styles, added ignore comments)

## URL Structure

```
/debts/                          # List all debts
/debts/new/                      # Create new debt
/debts/<id>/                     # View debt details
/debts/<id>/edit/                # Edit debt
/debts/<id>/borrow/              # Add borrowing transaction
```

## User Workflow Example

### Motherboard Purchase Scenario:

1. **Create Debt**:
   - Name: "Motherboard Purchase"
   - Description: "Borrowed from friend for new motherboard"
   - Total Amount: 27,000
   - System automatically creates tag: "Debt: Motherboard Purchase"

2. **First Borrowing**:
   - Amount: 4,000
   - Date: 2024-03-15
   - Notes: "Advance payment needed"

3. **Second Borrowing**:
   - Amount: 23,000
   - Date: 2024-04-01
   - Notes: "Remaining amount"

4. **Natural Repayments** (in monthly budgets):
   - April: Add expense 4,000 with tag "Debt: Motherboard Purchase"
   - May: Add expense 5,000 with tag "Debt: Motherboard Purchase"
   - June: Add expense 5,000 with tag "Debt: Motherboard Purchase"
   - Continue until fully repaid
   - Tag automatically disabled when debt is fully repaid

## Key Features

### Automatic Tag Generation
- System automatically creates unique tags for each debt (e.g., "Debt: Motherboard Purchase")
- Tags are used for tracking repayments through regular expenses
- No manual tag selection required

### Natural Repayment Tracking
- Users add expenses in monthly budgets using debt tags
- System automatically calculates repayment progress from these expenses
- No separate repayment forms or manual tracking needed

### Progress Tracking
- Visual progress bars for borrowing progress
- Visual progress bars for repayment progress (calculated from expenses)
- Remaining amounts clearly displayed
- Transaction history with dates and notes

### Flexible Borrowing
- No limits on borrowing amounts
- Borrow in multiple installments
- Track each borrowing transaction separately
- Add notes for context

### Automatic Tag Management
- Tags are automatically disabled when debt is fully repaid
- Disabled tags don't appear in new expense forms
- Historical data preserved even after tag is disabled

## Technical Considerations

### Performance
- Efficient queries for debt calculations
- Proper indexing on date fields
- Optimized progress calculations

### Data Integrity
- Proper foreign key relationships
- Transaction safety for expense creation
- Validation for amounts and dates

### User Experience
- Consistent with existing UI patterns
- Clear visual feedback
- Intuitive workflow
- Responsive design

## Future Enhancements

### Potential Additions
- [ ] Debt categories (personal, business, etc.)
- [ ] Interest tracking (if needed later)
- [ ] Payment reminders
- [ ] Debt templates for common scenarios
- [ ] Export debt reports
- [ ] Debt analytics and insights

### Integration Opportunities
- [ ] Goal system integration (borrow for goal)
- [ ] Budget planning (include debt repayments in planning)
- [ ] Financial health scoring
- [ ] Debt-to-income ratio tracking

## Success Metrics

- [ ] Users can create and manage debts successfully
- [ ] Automatic tag generation works correctly
- [ ] Repayment tracking through expenses is accurate
- [ ] Progress tracking is accurate and helpful
- [ ] UI is intuitive and consistent
- [ ] System handles edge cases gracefully
- [ ] Performance is acceptable with large datasets
- [ ] Tag disabling works correctly when debts are fully repaid

## Notes

- Keep debt system separate from main budget interface
- Maintain consistency with existing Goals feature patterns
- Ensure proper error handling and user feedback
- Test thoroughly with real-world scenarios
- Document any deviations from standard patterns
- Debt repayments are treated as recurring expenses until fully paid
- Tags are automatically managed (created and disabled) by the system
- Users work naturally in their budget interface without switching contexts
