# AI Goal Assistant - Data Flow

This document outlines the data flow for the AI-based goal recommendation system.

## Data Sources

1. **Historical Expense Data**
   - Category-wise expenses
   - Spending patterns over time
   - Recurring vs. one-time expenses

2. **Budget Information**
   - Income
   - Planned expenses by category
   - Available discretionary funds

3. **Goal Parameters**
   - Target amount
   - Deadline
   - Priority level
   - Purpose/category

4. **User Behavior**
   - Savings rate history
   - Recommendation acceptance rate
   - Expense modification patterns

## Data Processing Pipeline

```
┌─────────────────┐     ┌────────────────────┐     ┌─────────────────────┐
│                 │     │                    │     │                     │
│  Raw Expense    │────▶│  Data Preparation  │────▶│  Pattern Detection  │
│  Data           │     │  & Preprocessing   │     │  & Feature Extraction│
│                 │     │                    │     │                     │
└─────────────────┘     └────────────────────┘     └─────────────────────┘
                                                              │
                                                              ▼
┌─────────────────┐     ┌────────────────────┐     ┌─────────────────────┐
│                 │     │                    │     │                     │
│  Recommendation │◀────│  Decision Engine   │◀────│  ML Models          │
│  Generation     │     │                    │     │  (Classification,   │
│                 │     │                    │     │   Prediction)       │
└─────────────────┘     └────────────────────┘     └─────────────────────┘
        │
        ▼
┌─────────────────┐     ┌────────────────────┐
│                 │     │                    │
│  User Interface │     │  Feedback          │
│  & Presentation │────▶│  Collection        │
│                 │     │                    │
└─────────────────┘     └────────────────────┘
                                │
                                ▼
                        ┌─────────────────┐
                        │                 │
                        │  Model Update   │
                        │  & Refinement   │
                        │                 │
                        └─────────────────┘
```

## Machine Learning Models

### 1. Expense Classification Model

**Purpose**: Classify expenses as essential or discretionary

**Features**:
- Expense amount
- Category
- Frequency
- Name/description keywords
- Time of month

**Algorithm**: Random Forest Classifier

### 2. Spending Pattern Model

**Purpose**: Identify patterns and anomalies in spending

**Features**:
- Historical spending by category
- Day of month/week
- Seasonal patterns

**Algorithm**: K-means clustering + Isolation Forest for anomaly detection

### 3. Recommendation Prioritization Model

**Purpose**: Rank potential savings opportunities

**Features**:
- Estimated savings amount
- Ease of implementation
- Impact on quality of life
- Previous recommendation success

**Algorithm**: Decision tree + rule-based system

## Recommendation Generation Flow

1. **Data Collection**
   - Gather user's expense history
   - Analyze current budget allocation
   - Check goal details and timeline

2. **Pattern Analysis**
   - Identify spending categories above average
   - Detect discretionary expenses
   - Find recurring patterns and anomalies

3. **Opportunity Identification**
   - Generate potential expense reduction options
   - Calculate impact of each option on goal timeline
   - Compare with standard expense benchmarks

4. **Recommendation Creation**
   - Select top 3-5 opportunities based on impact
   - Generate natural language recommendations
   - Pair with visualization of expected impact

5. **Feedback Integration**
   - Collect user feedback on recommendations
   - Track which recommendations are followed
   - Update recommendation models based on feedback

## User Feedback Loop

1. User receives recommendations
2. User rates usefulness (1-5 stars)
3. User either applies or ignores recommendation
4. System tracks actual impact of applied recommendations
5. ML models updated based on feedback and impact data
6. Future recommendations refined based on this data

## Data Privacy Considerations

- All processing done locally/on-server
- No external AI APIs required
- User data remains within application
- Aggregated, anonymized patterns may be used for improving the system
