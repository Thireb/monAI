# AI Goal Assistant - UI Wireframes

This document provides descriptions of the key UI components for the AI-based goal assistant feature.

## 1. Goal Dashboard

The goal dashboard will be integrated into the existing budget detail view, showing the user's active financial goals and their progress.

```
┌───────────────────────────────────────────────────────────────────┐
│ Financial Goals                                       [+ NEW GOAL] │
├───────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────┐  ┌─────────────────────────┐          │
│ │ Vacation Fund           │  │ Emergency Fund          │          │
│ │                         │  │                         │          │
│ │ $2,500 / $5,000         │  │ $1,200 / $3,000         │          │
│ │ [===========50%========]│  │ [====40%===============]│          │
│ │                         │  │                         │          │
│ │ Due: Jul 15, 2023       │  │ Due: Ongoing            │          │
│ │                         │  │                         │          │
│ │ [VIEW DETAILS]  [ADVICE]│  │ [VIEW DETAILS]  [ADVICE]│          │
│ └─────────────────────────┘  └─────────────────────────┘          │
│                                                                   │
│ ┌─────────────────────────┐                                       │
│ │ New Laptop              │                                       │
│ │                         │                                       │
│ │ $400 / $1,500           │                                       │
│ │ [===27%================]│                                       │
│ │                         │                                       │
│ │ Due: Dec 1, 2023        │                                       │
│ │                         │                                       │
│ │ [VIEW DETAILS]  [ADVICE]│                                       │
│ └─────────────────────────┘                                       │
└───────────────────────────────────────────────────────────────────┘
```

## 2. Goal Creation Wizard

A step-by-step interface for creating new financial goals.

```
┌───────────────────────────────────────────────────────────────────┐
│ Create a New Goal                                     [Step 1 of 4]│
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  What are you saving for?                                         │
│                                                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │
│  │  Vacation   │ │  Emergency  │ │  Education  │ │   Housing   │  │
│  │    Fund     │ │    Fund     │ │             │ │             │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘  │
│                                                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │
│  │  Vehicle    │ │ Electronics │ │   Medical   │ │    Other    │  │
│  │             │ │             │ │   Expense   │ │             │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘  │
│                                                                   │
│  Goal Name: [________________________________]                    │
│                                                                   │
│                                                                   │
│                                      [CANCEL]    [NEXT STEP ->]   │
└───────────────────────────────────────────────────────────────────┘
```

## 3. Goal Detail View

Detailed view of a single goal with progress and recommendations.

```
┌───────────────────────────────────────────────────────────────────┐
│ Vacation Fund                                        [EDIT] [BACK] │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Target: $5,000                       Current: $2,500 (50%)       │
│  [=====================50%==================================]      │
│                                                                   │
│  Started: Jan 15, 2023                Due: Jul 15, 2023           │
│  Time Elapsed: 3 months (50%)         Time Remaining: 3 months    │
│                                                                   │
│  Monthly Contribution: $833           Priority: High              │
│                                                                   │
├───────────────────────────────────────────────────────────────────┤
│ AI Advisor Recommendations                                        │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Based on your spending patterns, here are 3 ways to reach your   │
│  goal faster:                                                     │
│                                                                   │
│  1. Reduce dining out expenses by $100/month                      │
│     → Would add $300 to your goal by deadline                     │
│     [IMPLEMENT THIS]                                              │
│                                                                   │
│  2. Pause subscription services temporarily ($45/month)           │
│     → Would add $135 to your goal by deadline                     │
│     [IMPLEMENT THIS]                                              │
│                                                                   │
│  3. Allocate 50% of your recent tax return ($400)                 │
│     → Would add $400 to your goal immediately                     │
│     [IMPLEMENT THIS]                                              │
│                                                                   │
│  [GET MORE RECOMMENDATIONS]                                       │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

## 4. Recommendation Detail View

Detailed view of a single recommendation with implementation options.

```
┌───────────────────────────────────────────────────────────────────┐
│ Recommendation Details                                     [CLOSE] │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Reduce dining out expenses by $100/month                         │
│  ────────────────────────────────────────────────                 │
│                                                                   │
│  Current monthly spending: $350/month                             │
│  Recommended reduction: $100/month (28% less)                     │
│  Potential impact: +$300 to your Vacation Fund by Jul 15          │
│                                                                   │
│  Why this recommendation?                                         │
│  Your dining out expenses are 40% higher than your 6-month        │
│  average and represent a discretionary spending category.         │
│                                                                   │
│  Suggested Implementation:                                        │
│  • Reduce eating out from 8 to 5 times per month                  │
│  • Opt for lunch specials instead of dinner when eating out       │
│  • Consider meal prepping to reduce weekday takeout               │
│                                                                   │
│  How would you like to implement this?                            │
│  [X] Add a budget alert when I exceed $250 in dining out          │
│  [ ] Automatically categorize excess as goal contribution         │
│  [ ] Just track manually                                          │
│                                                                   │
│  Was this recommendation helpful?                                 │
│  [★][★][★][★][☆]                                                 │
│                                                                   │
│  [IMPLEMENT THIS RECOMMENDATION]    [SKIP THIS RECOMMENDATION]    │
└───────────────────────────────────────────────────────────────────┘
```

## 5. AI Advisor Chat Interface

Conversational interface for interacting with the AI advisor.

```
┌───────────────────────────────────────────────────────────────────┐
│ Financial AI Advisor                                       [CLOSE] │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  BOT: Hello! I can help you reach your financial goals faster.    │
│       What would you like to discuss today?                       │
│       [My Goals] [Spending Advice] [Recommendation History]       │
│                                                                   │
│  YOU: I want advice on reaching my vacation fund goal faster.     │
│                                                                   │
│  BOT: I see you want to save $5,000 for your vacation by July 15. │
│       You're currently 50% of the way there with $2,500 saved.    │
│                                                                   │
│       Based on your current rate, you'll reach your goal on       │
│       time, but here are some ways to boost your savings:         │
│                                                                   │
│       1. Dining out spending could be reduced                     │
│       2. You might consider pausing some subscriptions            │
│       3. Your recent tax return could contribute to this goal     │
│                                                                   │
│       Which would you like more details on?                       │
│                                                                   │
│  YOU: Tell me more about the dining out suggestion.               │
│                                                                   │
│  BOT: You currently spend about $350/month on dining out.         │
│       This is 40% higher than your 6-month average.               │
│                                                                   │
│       If you reduce this by $100/month (to $250), you could       │
│       add $300 to your vacation fund by the deadline.             │
│                                                                   │
│       Would you like some specific strategies to help reduce      │
│       this expense category?                                      │
│                                                                   │
│  [Type your message here...]                          [SEND] [MIC]│
└───────────────────────────────────────────────────────────────────┘
```

## 6. Recommendation History

A view showing past recommendations and their impact.

```
┌───────────────────────────────────────────────────────────────────┐
│ Recommendation History                                     [BACK]  │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Applied Recommendations                                          │
│  ───────────────────────                                          │
│                                                                   │
│  • Reduce dining out expenses by $100/month                       │
│    Applied on: Feb 10, 2023                                       │
│    Goal impact: +$250 so far                                      │
│    Status: On track (spending reduced by $85/month on average)    │
│    [VIEW DETAILS]                                                 │
│                                                                   │
│  • Allocated 50% of tax return to vacation fund                   │
│    Applied on: Mar 5, 2023                                        │
│    Goal impact: +$400 (one-time)                                  │
│    Status: Completed                                              │
│    [VIEW DETAILS]                                                 │
│                                                                   │
│  Skipped Recommendations                                          │
│  ──────────────────────                                           │
│                                                                   │
│  • Pause subscription services temporarily                        │
│    Skipped on: Feb 10, 2023                                       │
│    Potential impact: +$135 by Jul 15                              │
│    [RECONSIDER]                                                   │
│                                                                   │
│  • Reduce grocery spending by using more coupons                  │
│    Skipped on: Jan 22, 2023                                       │
│    Potential impact: +$120 by Jul 15                              │
│    [RECONSIDER]                                                   │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

## 7. Goal Progress Timeline

A visualization of goal progress over time with projected completion.

```
┌───────────────────────────────────────────────────────────────────┐
│ Goal Timeline: Vacation Fund                              [CLOSE]  │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  $5,000 ┌───────────────────────────────────────────┐             │
│         │                                     ·····/│             │
│  $4,000 │                               ·····/     /│             │
│         │                         ·····/           /│             │
│  $3,000 │                   ·····/                 /│             │
│         │              ····/                      /│              │
│  $2,000 │        ·····/                          /│               │
│         │   ····/                               /│                │
│  $1,000 │··/                                   /│                 │
│         │/                                    /│                  │
│       $0┼───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐            │
│         Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec           │
│                                                                   │
│         ── Current progress                                       │
│         ·· Original projection                                    │
│         // New projection with recommendations                    │
│                                                                   │
│  With your current savings rate:                                  │
│  • You will reach your goal by: Jul 15, 2023 (on time)            │
│                                                                   │
│  With implemented recommendations:                                 │
│  • You will reach your goal by: Jun 22, 2023 (23 days earlier)    │
│  • Extra savings potential: $835                                  │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

## 8. Recommendation Impact Calculator

An interactive tool to calculate the impact of different savings strategies.

```
┌───────────────────────────────────────────────────────────────────┐
│ Savings Impact Calculator                                 [CLOSE]  │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Adjust the sliders to see how different changes affect your goal.│
│                                                                   │
│  Monthly dining out budget:                                       │
│  $150 [===========|==============] $500    Current: $350          │
│                                                                   │
│  Monthly entertainment budget:                                    │
│  $50 [======|===================] $300    Current: $120           │
│                                                                   │
│  Monthly subscription services:                                   │
│  $0 [============|=============] $150    Current: $45             │
│                                                                   │
│  One-time contribution from savings:                              │
│  $0 [==========|===============] $1,000  Current: $0              │
│                                                                   │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Impact Summary:                                                  │
│                                                                   │
│  Total monthly savings: $175                                      │
│  One-time contribution: $500                                      │
│                                                                   │
│  Goal completion date: June 1, 2023 (45 days earlier)             │
│  Potential extra savings: $1,025                                  │
│                                                                   │
│  [SAVE THESE SETTINGS]  [RESET]  [IMPLEMENT RECOMMENDATIONS]      │
└───────────────────────────────────────────────────────────────────┘
```

## Implementation Notes

1. All UI components should follow the existing Material Design aesthetic of the application
2. Mobile responsiveness is essential - wireframes should adapt to smaller screens
3. The AI advisor interface should feel conversational but not overly anthropomorphized
4. All numerical recommendations should be accompanied by visual indicators
5. Interactive elements should provide immediate feedback
6. Color coding should be used consistently (green for positive progress, etc.)
