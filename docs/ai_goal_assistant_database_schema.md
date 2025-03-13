# AI Goal Assistant - Database Schema

This document outlines the database schema for the AI-based financial goal assistant feature, including table relationships and indexes.

## Database Models Diagram

```
┌───────────────────────┐       ┌────────────────────────┐
│ User                  │       │ Goal                   │
├───────────────────────┤       ├────────────────────────┤
│ id (PK)               │       │ id (PK)                │
│ username              │       │ user_id (FK)           │◄─────┐
│ email                 │       │ name                   │      │
│ password              │       │ description            │      │
│ ...                   │       │ target_amount          │      │
└───────────┬───────────┘       │ current_amount         │      │
            │                   │ start_date             │      │
            │                   │ target_date            │      │
            │                   │ category               │      │
            │                   │ priority               │      │
            │                   │ is_active              │      │
            │                   │ created_at             │      │
            │                   │ updated_at             │      │
            │                   └────────────┬───────────┘      │
            │                                │                  │
            │                                │                  │
            │                                ▼                  │
            │                   ┌────────────────────────┐      │
            │                   │ GoalContribution       │      │
            │                   ├────────────────────────┤      │
            │                   │ id (PK)                │      │
            │                   │ goal_id (FK)           │──────┘
            │                   │ amount                 │
            │                   │ date                   │
            │                   │ source                 │
            │                   │ notes                  │
            │                   │ created_at             │
            │                   └────────────┬───────────┘
            │                                │
            │                                │
            ▼                                ▼
┌───────────────────────┐       ┌────────────────────────┐
│ Budget                │       │ Recommendation         │
├───────────────────────┤       ├────────────────────────┤
│ id (PK)               │       │ id (PK)                │
│ user_id (FK)          │       │ goal_id (FK)           │◄─────┐
│ name                  │       │ title                  │      │
│ start_date            │       │ description            │      │
│ end_date              │       │ category               │      │
│ ...                   │       │ potential_impact       │      │
└───────────┬───────────┘       │ difficulty_level       │      │
            │                   │ implementation_steps   │      │
            │                   │ is_implemented         │      │
            │                   │ user_feedback          │      │
            │                   │ created_at             │      │
            ▼                   └────────────┬───────────┘      │
┌───────────────────────┐                    │                  │
│ Expense               │                    │                  │
├───────────────────────┤                    │                  │
│ id (PK)               │                    ▼                  │
│ budget_id (FK)        │       ┌────────────────────────┐      │
│ name                  │       │ RecommendationFeedback │      │
│ amount                │       ├────────────────────────┤      │
│ date                  │       │ id (PK)                │      │
│ category_id (FK)      │       │ recommendation_id (FK) │──────┘
│ ...                   │       │ was_helpful            │
└───────────────────────┘       │ rating                 │
                                │ comments               │
                                │ created_at             │
                                └────────────────────────┘
```

## Model Details

### Goal

This model represents a financial goal set by a user.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | Integer | Primary key | Auto-increment |
| user_id | Integer | Foreign key to User | NOT NULL |
| name | Varchar(100) | Name of the goal | NOT NULL |
| description | Text | Description of the goal | |
| target_amount | Decimal(10,2) | Target amount to save | NOT NULL, > 0 |
| current_amount | Decimal(10,2) | Current saved amount | NOT NULL, >= 0 |
| start_date | Date | When the goal started | NOT NULL |
| target_date | Date | Deadline for the goal | NULL for ongoing goals |
| category | Varchar(50) | Category (vacation, emergency, etc.) | NOT NULL |
| priority | Varchar(20) | Priority level (high, medium, low) | NOT NULL |
| is_active | Boolean | Whether the goal is active | DEFAULT TRUE |
| created_at | Timestamp | When the goal was created | DEFAULT NOW() |
| updated_at | Timestamp | When the goal was last updated | ON UPDATE NOW() |

**Indexes:**
- PRIMARY KEY (id)
- INDEX (user_id)
- INDEX (category)
- INDEX (is_active)

### GoalContribution

This model tracks individual contributions made toward a goal.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | Integer | Primary key | Auto-increment |
| goal_id | Integer | Foreign key to Goal | NOT NULL |
| amount | Decimal(10,2) | Contribution amount | NOT NULL, > 0 |
| date | Date | When the contribution was made | NOT NULL |
| source | Varchar(50) | Source of the contribution | NOT NULL |
| notes | Text | Additional notes | |
| created_at | Timestamp | When the record was created | DEFAULT NOW() |

**Indexes:**
- PRIMARY KEY (id)
- INDEX (goal_id)
- INDEX (date)

### Recommendation

This model stores AI-generated recommendations for reaching goals.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | Integer | Primary key | Auto-increment |
| goal_id | Integer | Foreign key to Goal | NOT NULL |
| title | Varchar(100) | Short title for the recommendation | NOT NULL |
| description | Text | Detailed description | NOT NULL |
| category | Varchar(50) | Category of the recommendation | NOT NULL |
| potential_impact | Decimal(10,2) | Potential savings amount | NOT NULL |
| difficulty_level | Varchar(20) | Difficulty (easy, medium, hard) | NOT NULL |
| implementation_steps | JSON | Steps to implement the recommendation | |
| is_implemented | Boolean | Whether it has been implemented | DEFAULT FALSE |
| user_feedback | SmallInt | Numeric feedback (1-5) | NULL |
| created_at | Timestamp | When the recommendation was generated | DEFAULT NOW() |

**Indexes:**
- PRIMARY KEY (id)
- INDEX (goal_id)
- INDEX (category)
- INDEX (is_implemented)

### RecommendationFeedback

This model stores detailed feedback on recommendations.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | Integer | Primary key | Auto-increment |
| recommendation_id | Integer | Foreign key to Recommendation | NOT NULL |
| was_helpful | Boolean | Whether the recommendation was helpful | NOT NULL |
| rating | SmallInt | Rating (1-5) | NOT NULL |
| comments | Text | User comments | |
| created_at | Timestamp | When feedback was provided | DEFAULT NOW() |

**Indexes:**
- PRIMARY KEY (id)
- INDEX (recommendation_id)

## Integration with Existing Schema

The new models integrate with the existing application schema:
- The Goal model links to the User model
- Expense data from the Budget and Expense models will be analyzed to generate recommendations
- Category information will be used to classify expenses for analysis

## Django Model Definitions

```python
class Goal(models.Model):
    CATEGORY_CHOICES = [
        ('vacation', 'Vacation'),
        ('emergency', 'Emergency Fund'),
        ('education', 'Education'),
        ('housing', 'Housing'),
        ('vehicle', 'Vehicle'),
        ('electronics', 'Electronics'),
        ('medical', 'Medical Expense'),
        ('other', 'Other'),
    ]

    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_date = models.DateField()
    target_date = models.DateField(null=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]

    def progress_percentage(self):
        if self.target_amount == 0:
            return 0
        return (self.current_amount / self.target_amount) * 100

    def days_remaining(self):
        if not self.target_date:
            return None
        return (self.target_date - datetime.date.today()).days


class GoalContribution(models.Model):
    SOURCE_CHOICES = [
        ('direct', 'Direct Contribution'),
        ('savings', 'From Savings'),
        ('expense_reduction', 'Expense Reduction'),
        ('income', 'Extra Income'),
        ('other', 'Other'),
    ]

    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='contributions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['goal']),
            models.Index(fields=['date']),
        ]


class Recommendation(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='recommendations')
    title = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=50)
    potential_impact = models.DecimalField(max_digits=10, decimal_places=2)
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    implementation_steps = models.JSONField(default=list)
    is_implemented = models.BooleanField(default=False)
    user_feedback = models.SmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['goal']),
            models.Index(fields=['category']),
            models.Index(fields=['is_implemented']),
        ]


class RecommendationFeedback(models.Model):
    recommendation = models.ForeignKey(Recommendation, on_delete=models.CASCADE, related_name='feedback')
    was_helpful = models.BooleanField()
    rating = models.SmallIntegerField()
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['recommendation']),
        ]
```

## Migration Strategy

The migration strategy will be:

1. Create the Goal model
2. Create the GoalContribution model
3. Create the Recommendation model
4. Create the RecommendationFeedback model
5. Add backward-compatible fields as needed

This strategy ensures minimal disruption to the existing application while adding the new functionality.
