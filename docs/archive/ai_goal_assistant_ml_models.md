# AI Goal Assistant - ML Models Specification

This document details the machine learning models used in the AI-based financial goal assistant feature. All models are implemented using free, open-source libraries to ensure no external API costs.

## Overview of ML Components

The AI goal assistant uses three core machine learning models:

1. **Expense Classification Model**: Categorizes expenses as essential vs. discretionary
2. **Spending Pattern Model**: Detects patterns and anomalies in spending behavior
3. **Recommendation Prioritization Model**: Ranks potential savings opportunities

Each model is designed to run efficiently on the application server without requiring specialized hardware or external APIs.

## Model 1: Expense Classification

### Purpose
Automatically classify expenses as "essential" (needs) or "discretionary" (wants) to identify areas where spending can be reduced without impacting necessities.

### Input Features
| Feature | Type | Description |
|---------|------|-------------|
| expense_amount | Numeric | The amount of the expense |
| expense_category | Categorical | Category assigned to the expense (mapped to numeric) |
| expense_frequency | Numeric | How often this expense occurs (1=one-time, 2=occasional, 3=monthly, etc.) |
| day_of_month | Numeric | Day of month when expense typically occurs |
| description_tokens | Text/Embeddings | Vectorized keywords from expense descriptions |
| has_sub_expenses | Boolean | Whether the expense has sub-items |
| is_recurring | Boolean | Whether expense is marked as recurring |
| user_income_ratio | Numeric | Expense amount as percentage of user's income |

### Architecture
- **Model Type**: Random Forest Classifier
- **Library**: scikit-learn
- **Pre-processing**: StandardScaler for numeric features, OneHotEncoder for categorical features

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

# Feature preprocessing
numeric_features = ['expense_amount', 'expense_frequency', 'day_of_month', 'user_income_ratio']
categorical_features = ['expense_category']

numeric_transformer = StandardScaler()
categorical_transformer = OneHotEncoder(handle_unknown='ignore')

preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features)
    ])

# Model pipeline
expense_classifier = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
])
```

### Training Approach
- Initial training on manually labeled user expense data
- Fine-tuning based on user feedback
- Regular retraining (weekly) as more data becomes available

### Performance Metrics
- Target accuracy: >85%
- Target precision (essential): >90% (avoid misclassifying essential as discretionary)
- Target recall (discretionary): >80% (identify most discretionary expenses)

### Implementation Notes
- Model will be serialized using joblib for fast loading
- Pre-trained with generic expense data then personalized per user
- Category importance features will help explain classifications

## Model 2: Spending Pattern Detection

### Purpose
Identify patterns, trends, and anomalies in user spending behavior to detect potential savings opportunities and unusual expenses.

### Input Features
| Feature | Type | Description |
|---------|------|-------------|
| expense_amount | Numeric | Amount of each expense |
| expense_category | Categorical | Category of expense |
| date | Date | Date of expense (transformed into multiple features) |
| day_of_week | Categorical | Day of week (0-6) |
| week_of_month | Numeric | Week number within month (1-5) |
| month | Categorical | Month (1-12) |
| is_weekend | Boolean | Whether expense occurred on weekend |
| is_holiday | Boolean | Whether expense occurred on/near holiday |
| rolling_avg_7day | Numeric | 7-day rolling average for this category |
| rolling_avg_30day | Numeric | 30-day rolling average for this category |

### Architecture
- **Pattern Detection**: K-means clustering with time-series features
- **Anomaly Detection**: Isolation Forest for outlier detection
- **Trend Analysis**: ARIMA for time-series forecasting

```python
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from statsmodels.tsa.arima.model import ARIMA
import pandas as pd

# Pattern detection with K-means clustering
def detect_spending_patterns(expense_data):
    # Feature engineering
    expense_data = add_time_features(expense_data)

    # Group by category
    categories = expense_data['expense_category'].unique()
    patterns = {}

    for category in categories:
        cat_data = expense_data[expense_data['expense_category'] == category]
        if len(cat_data) >= 10:  # Need sufficient data
            # Normalize features
            features = cat_data[['expense_amount', 'day_of_week', 'week_of_month', 'month']]
            features_scaled = StandardScaler().fit_transform(features)

            # Apply clustering
            kmeans = KMeans(n_clusters=min(3, len(cat_data) // 3), random_state=42)
            cat_data['cluster'] = kmeans.fit_predict(features_scaled)

            # Store patterns
            patterns[category] = analyze_clusters(cat_data, kmeans)

    return patterns

# Anomaly detection with Isolation Forest
def detect_anomalies(expense_data, contamination=0.05):
    # Group by category
    categories = expense_data['expense_category'].unique()
    anomalies = {}

    for category in categories:
        cat_data = expense_data[expense_data['expense_category'] == category]
        if len(cat_data) >= 20:  # Need sufficient data
            features = cat_data[['expense_amount', 'rolling_avg_30day']]
            features_scaled = StandardScaler().fit_transform(features)

            # Apply Isolation Forest
            iso_forest = IsolationForest(contamination=contamination, random_state=42)
            cat_data['is_anomaly'] = iso_forest.fit_predict(features_scaled)

            # Extract anomalies (outliers are marked as -1)
            anomalies[category] = cat_data[cat_data['is_anomaly'] == -1]

    return anomalies
```

### Training Approach
- Unsupervised learning using historical expense data
- Incremental training as new expenses are added
- Personalized detection thresholds based on user spending variability

### Performance Tuning
- Clustering: Silhouette score optimization for k-means
- Anomaly detection: Contamination parameter tuned per category
- Forecast accuracy: MAPE (Mean Absolute Percentage Error) < 20%

### Implementation Notes
- Time-series models retrained monthly
- Isolation Forest parameters adjusted seasonally
- Results cached to improve performance

## Model 3: Recommendation Prioritization

### Purpose
Rank and prioritize potential savings recommendations based on their impact, feasibility, and personalization to user preferences.

### Input Features
| Feature | Type | Description |
|---------|------|-------------|
| potential_savings | Numeric | Estimated savings amount |
| difficulty_score | Numeric | How difficult to implement (1-5 scale) |
| impact_on_goal | Numeric | Impact as percentage of goal amount |
| time_to_implement | Numeric | Estimated days to implement |
| success_probability | Numeric | Probability of successful implementation |
| category_preference | Numeric | User's preference for this category (derived) |
| previous_similar_applied | Boolean | Whether user applied similar recommendations before |
| days_to_goal | Numeric | Days remaining until goal deadline |
| goal_priority | Numeric | Priority of the linked goal (1-3) |

### Architecture
- **Base Model**: Decision Tree with rule-based enhancements
- **Ensemble Method**: Extra Trees for robustness

```python
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.preprocessing import MinMaxScaler

class RecommendationPrioritizer:
    def __init__(self):
        self.model = ExtraTreesRegressor(n_estimators=50, random_state=42)
        self.scaler = MinMaxScaler()

    def fit(self, features, priorities):
        """Train the model on past recommendation data with known priorities."""
        scaled_features = self.scaler.fit_transform(features)
        self.model.fit(scaled_features, priorities)
        return self

    def predict(self, features):
        """Predict priority scores for new recommendations."""
        scaled_features = self.scaler.transform(features)
        return self.model.predict(scaled_features)

    def prioritize_recommendations(self, recommendations, user_context):
        """Generate priority scores and rank recommendations."""
        # Extract features from recommendations and context
        features = self._extract_features(recommendations, user_context)

        # Get priority scores
        priority_scores = self.predict(features)

        # Apply business rules for adjustments
        adjusted_scores = self._apply_business_rules(
            recommendations, priority_scores, user_context)

        # Sort and return
        sorted_indices = np.argsort(adjusted_scores)[::-1]  # Descending
        return [recommendations[i] for i in sorted_indices], adjusted_scores[sorted_indices]
```

### Rule-Based Enhancements
The model incorporates several business rules to adjust raw scores:

1. **Goal deadline proximity**: Increase priority as deadline approaches
2. **Quick wins first**: Prioritize easy, high-impact recommendations
3. **Category diversification**: Avoid multiple recommendations in same category
4. **User preference adaptation**: Adjust based on past user behavior
5. **Time-sensitive opportunities**: Prioritize time-limited opportunities

### Training Approach
- Initial training on synthetic recommendation data
- Refinement based on user feedback and acceptance rates
- Continual learning approach with feedback loop

### Performance Metrics
- Key metric: Recommendation acceptance rate
- Target: >25% of recommendations implemented by users
- Secondary: User-reported satisfaction with recommendations

## Integration Architecture

The three models work together in the following pipeline:

```
┌─────────────────┐    ┌─────────────────┐    ┌────────────────────┐
│                 │    │                 │    │                    │
│  Expense        │───▶│  Spending       │───▶│  Recommendation    │
│  Classification │    │  Pattern        │    │  Prioritization    │
│  Model          │    │  Model          │    │  Model             │
│                 │    │                 │    │                    │
└─────────────────┘    └─────────────────┘    └────────────────────┘
        │                      │                       │
        │                      │                       │
        ▼                      ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                 Recommendation Generator                        │
│                 (Rule-based integration layer)                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │                          │
                  │  User Interface          │
                  │                          │
                  └──────────────────────────┘
```

## Deployment Strategy

### Server Requirements
- Python 3.8+ with scikit-learn, pandas, and statsmodels
- 2GB RAM minimum for model operations
- Models run in background via Django-Q

### Containerization
- Models packaged as separate service if needed
- Modular design allows scaling of prediction service

### Monitoring
- Model drift detection for retraining needs
- Performance metrics tracking
- Recommendation success/failure logging

## Data Privacy and Security

- All user data processed on server, not transmitted externally
- Models trained on anonymized data
- No personal identifying information used in model features
- Feature extraction processes filter sensitive information

## Fallback Mechanisms

In case of model failure:
1. Rule-based recommendations as backup
2. Generic recommendations based on category averages
3. User-based manual recommendation system
