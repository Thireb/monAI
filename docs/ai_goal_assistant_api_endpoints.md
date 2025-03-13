# AI Goal Assistant - API Endpoints

This document describes the API endpoints for the AI-based goal assistant feature.

## Goals API

### List/Create Goals
- **URL**: `/api/goals/`
- **Methods**: `GET`, `POST`
- **Authentication**: Required
- **Description**: List all goals for the current user or create a new goal

#### GET Response
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Vacation Fund",
      "description": "Saving for summer vacation to Italy",
      "target_amount": "5000.00",
      "current_amount": "2500.00",
      "start_date": "2023-01-15",
      "target_date": "2023-07-15",
      "category": "vacation",
      "priority": "high",
      "is_active": true,
      "progress_percentage": 50,
      "days_remaining": 90,
      "created_at": "2023-01-15T10:30:00Z",
      "updated_at": "2023-04-15T14:45:30Z"
    },
    {
      "id": 2,
      "name": "Emergency Fund",
      "description": "Building emergency savings",
      "target_amount": "3000.00",
      "current_amount": "1200.00",
      "start_date": "2023-02-01",
      "target_date": null,
      "category": "emergency",
      "priority": "medium",
      "is_active": true,
      "progress_percentage": 40,
      "days_remaining": null,
      "created_at": "2023-02-01T08:15:00Z",
      "updated_at": "2023-04-10T11:20:15Z"
    }
  ]
}
```

#### POST Request
```json
{
  "name": "New Laptop",
  "description": "Saving for a MacBook Pro",
  "target_amount": "1500.00",
  "current_amount": "400.00",
  "start_date": "2023-04-01",
  "target_date": "2023-12-01",
  "category": "electronics",
  "priority": "medium"
}
```

### Goal Detail
- **URL**: `/api/goals/{id}/`
- **Methods**: `GET`, `PUT`, `DELETE`
- **Authentication**: Required
- **Description**: Retrieve, update, or delete a specific goal

#### GET Response
```json
{
  "id": 1,
  "name": "Vacation Fund",
  "description": "Saving for summer vacation to Italy",
  "target_amount": "5000.00",
  "current_amount": "2500.00",
  "start_date": "2023-01-15",
  "target_date": "2023-07-15",
  "category": "vacation",
  "priority": "high",
  "is_active": true,
  "progress_percentage": 50,
  "days_remaining": 90,
  "monthly_contribution_needed": "833.33",
  "created_at": "2023-01-15T10:30:00Z",
  "updated_at": "2023-04-15T14:45:30Z",
  "recent_contributions": [
    {
      "id": 12,
      "amount": "300.00",
      "date": "2023-04-01",
      "source": "direct"
    },
    {
      "id": 10,
      "amount": "250.00",
      "date": "2023-03-01",
      "source": "direct"
    }
  ]
}
```

### Goal Statistics
- **URL**: `/api/goals/{id}/statistics/`
- **Methods**: `GET`
- **Authentication**: Required
- **Description**: Get detailed statistics about a goal's progress

#### GET Response
```json
{
  "goal_id": 1,
  "goal_name": "Vacation Fund",
  "average_monthly_contribution": "312.50",
  "contribution_consistency": 87.5,
  "projected_completion_date": "2023-07-18",
  "on_track": false,
  "days_behind_schedule": 3,
  "monthly_contribution_needed": "833.33",
  "progress_by_month": [
    {"month": "Jan 2023", "amount": "500.00"},
    {"month": "Feb 2023", "amount": "750.00"},
    {"month": "Mar 2023", "amount": "1000.00"},
    {"month": "Apr 2023", "amount": "2500.00"}
  ]
}
```

### Goal Contributions
- **URL**: `/api/goals/{id}/contributions/`
- **Methods**: `GET`, `POST`
- **Authentication**: Required
- **Description**: List or add contributions to a specific goal

#### POST Request
```json
{
  "amount": "250.00",
  "date": "2023-04-15",
  "source": "savings",
  "notes": "Transferred from checking account"
}
```

## Recommendations API

### List Recommendations
- **URL**: `/api/goals/{id}/recommendations/`
- **Methods**: `GET`
- **Authentication**: Required
- **Description**: Get AI-generated recommendations for a specific goal

#### GET Response
```json
{
  "goal_id": 1,
  "goal_name": "Vacation Fund",
  "recommendations": [
    {
      "id": 5,
      "title": "Reduce dining out expenses",
      "description": "Reducing dining out by $100/month could save $300 by your goal date",
      "category": "dining",
      "potential_impact": "300.00",
      "difficulty_level": "medium",
      "implementation_steps": [
        "Reduce eating out from 8 to 5 times per month",
        "Opt for lunch specials instead of dinner when eating out",
        "Consider meal prepping to reduce weekday takeout"
      ],
      "is_implemented": false,
      "created_at": "2023-04-14T09:45:00Z"
    },
    {
      "id": 6,
      "title": "Pause subscription services",
      "description": "Temporarily pausing subscriptions could save $135 by your goal date",
      "category": "subscriptions",
      "potential_impact": "135.00",
      "difficulty_level": "easy",
      "implementation_steps": [
        "Review all current subscriptions",
        "Identify non-essential services",
        "Pause services for 3 months"
      ],
      "is_implemented": false,
      "created_at": "2023-04-14T09:45:30Z"
    }
  ]
}
```

### Recommendation Detail
- **URL**: `/api/recommendations/{id}/`
- **Methods**: `GET`, `PUT`
- **Authentication**: Required
- **Description**: Get details or update status of a specific recommendation

#### PUT Request (to mark as implemented)
```json
{
  "is_implemented": true
}
```

### Recommendation Feedback
- **URL**: `/api/recommendations/{id}/feedback/`
- **Methods**: `POST`
- **Authentication**: Required
- **Description**: Provide feedback on a recommendation

#### POST Request
```json
{
  "was_helpful": true,
  "rating": 4,
  "comments": "This was a useful suggestion that I hadn't thought of."
}
```

## AI Advisor API

### Generate Custom Advice
- **URL**: `/api/advisor/advice/`
- **Methods**: `POST`
- **Authentication**: Required
- **Description**: Get custom advice based on specific parameters

#### POST Request
```json
{
  "goal_id": 1,
  "question": "How can I reach my vacation goal faster?",
  "context": {
    "consider_categories": ["dining", "entertainment", "subscriptions"],
    "max_monthly_impact": "200.00"
  }
}
```

#### POST Response
```json
{
  "advice_id": 42,
  "goal_id": 1,
  "recommendations": [
    {
      "title": "Reduce dining out expenses",
      "description": "You currently spend $350/month on dining out. This is 40% higher than your 6-month average. If you reduce this by $100/month (to $250), you could add $300 to your vacation fund by the deadline.",
      "potential_impact": "300.00",
      "difficulty_level": "medium",
      "implementation_steps": [
        "Reduce eating out from 8 to 5 times per month",
        "Opt for lunch specials instead of dinner when eating out",
        "Consider meal prepping to reduce weekday takeout"
      ]
    },
    {
      "title": "Create a temporary entertainment budget",
      "description": "Setting a monthly entertainment budget of $100 (reduced from your average of $175) could save $225 by your goal date.",
      "potential_impact": "225.00",
      "difficulty_level": "medium",
      "implementation_steps": [
        "Look for free or low-cost entertainment options",
        "Set a weekly spending limit",
        "Consider hosting gatherings at home instead of going out"
      ]
    }
  ],
  "generated_at": "2023-04-15T15:30:45Z"
}
```

### Simulate Goal Impact
- **URL**: `/api/advisor/simulate/`
- **Methods**: `POST`
- **Authentication**: Required
- **Description**: Simulate the impact of various savings strategies on goal completion

#### POST Request
```json
{
  "goal_id": 1,
  "strategies": [
    {"category": "dining", "monthly_reduction": "100.00"},
    {"category": "entertainment", "monthly_reduction": "75.00"},
    {"category": "subscriptions", "monthly_reduction": "45.00"}
  ],
  "one_time_contribution": "500.00"
}
```

#### POST Response
```json
{
  "simulation_id": 23,
  "goal_id": 1,
  "original_completion_date": "2023-07-15",
  "new_completion_date": "2023-06-01",
  "days_saved": 45,
  "total_monthly_savings": "220.00",
  "total_one_time_contribution": "500.00",
  "total_impact": "1160.00",
  "breakdown": [
    {"category": "dining", "monthly_savings": "100.00", "total_impact": "300.00"},
    {"category": "entertainment", "monthly_savings": "75.00", "total_impact": "225.00"},
    {"category": "subscriptions", "monthly_savings": "45.00", "total_impact": "135.00"},
    {"category": "one_time", "amount": "500.00", "total_impact": "500.00"}
  ],
  "simulated_at": "2023-04-15T15:45:30Z"
}
```

## Analytics API

### Spending Analysis
- **URL**: `/api/analytics/spending/`
- **Methods**: `GET`
- **Authentication**: Required
- **Description**: Get analysis of spending patterns

#### GET Response
```json
{
  "user_id": 42,
  "analysis_period": "last_6_months",
  "total_spending": "12450.00",
  "essential_spending": "7670.00",
  "discretionary_spending": "4780.00",
  "discretionary_percentage": 38.4,
  "top_categories": [
    {"category": "housing", "amount": "4800.00", "percentage": 38.6, "is_essential": true},
    {"category": "dining", "amount": "2100.00", "percentage": 16.9, "is_essential": false},
    {"category": "groceries", "amount": "1450.00", "percentage": 11.6, "is_essential": true},
    {"category": "entertainment", "amount": "1050.00", "percentage": 8.4, "is_essential": false},
    {"category": "transportation", "amount": "950.00", "percentage": 7.6, "is_essential": true}
  ],
  "savings_opportunities": [
    {"category": "dining", "typical_monthly": "350.00", "suggested_monthly": "250.00", "potential_savings": "100.00"},
    {"category": "subscriptions", "typical_monthly": "85.00", "suggested_monthly": "40.00", "potential_savings": "45.00"}
  ],
  "generated_at": "2023-04-15T00:05:00Z"
}
```

### Goal Progress Report
- **URL**: `/api/analytics/goals/progress/`
- **Methods**: `GET`
- **Authentication**: Required
- **Description**: Get a progress report for all active goals

#### GET Response
```json
{
  "user_id": 42,
  "total_goals": 3,
  "total_target_amount": "9500.00",
  "total_current_amount": "4100.00",
  "overall_progress_percentage": 43.2,
  "goals": [
    {
      "id": 1,
      "name": "Vacation Fund",
      "target_amount": "5000.00",
      "current_amount": "2500.00",
      "progress_percentage": 50,
      "status": "on_track",
      "days_remaining": 90
    },
    {
      "id": 2,
      "name": "Emergency Fund",
      "target_amount": "3000.00",
      "current_amount": "1200.00",
      "progress_percentage": 40,
      "status": "ongoing",
      "days_remaining": null
    },
    {
      "id": 3,
      "name": "New Laptop",
      "target_amount": "1500.00",
      "current_amount": "400.00",
      "progress_percentage": 26.7,
      "status": "at_risk",
      "days_remaining": 230
    }
  ],
  "generated_at": "2023-04-15T00:05:00Z"
}
```
