# Material Design Components Guide

This guide documents the reusable Material Design components available in the Budget Tracker application and how to use them effectively.

## Available Components

### 1. Action Button (`components/action_button.html`)
A versatile button component that supports Material Design icons and various styles.

#### Usage
```html
{% include "material/components/action_button.html" with
    button_type="button|submit"
    button_class="btn-raised btn-primary"  {# Use btn-raised for elevated Material style #}
    button_id="button_id"
    button_name="button_name"
    button_value="button_value"
    button_icon="material_icon_name"
    button_text="Button Text"
    button_title="Tooltip text"
    data_attributes="data-attr1='val1' data-attr2='val2'"
    onclick="javascript_function"
%}
```

#### Style Guidelines
- Use `btn-raised btn-primary` for primary actions
- Always include a Material icon for consistency
- Keep button text concise and action-oriented

### 2. Card (`components/card.html`)
A Material Design card component for grouping related information.

#### Usage
```html
{% include "material/components/card.html" with
    card_title="Card Title"
    card_subtitle="Optional Subtitle"
    card_icon="material_icon_name"
    card_class="additional-classes"
    card_header_class="header-classes"
    card_body_class="body-classes"
    card_actions=True  {# Enable action buttons in header #}
%}
```

### 3. Form Field (`components/form_field.html`)
A standardized form field component supporting various input types.

#### Usage
```html
{% include "material/components/form_field.html" with
    field_type="text|number|select|checkbox|textarea"
    field_id="field_id"
    field_name="field_name"
    field_label="Field Label"
    field_value=value
    field_placeholder="Placeholder text"
    field_required=True
    field_help_text="Help text below field"
    field_options=options_list  {# For select fields #}
%}
```

### 4. Modal (`components/modal.html`)
A Material Design modal dialog component.

#### Usage
```html
{% include "material/components/modal.html" with
    modal_id="uniqueModalId"
    modal_title="Modal Title"
    modal_class="additional-classes"
    modal_size="modal-lg|modal-sm"
    modal_static=True  {# Prevents closing on backdrop click #}
    show_close_button=True
    modal_footer=True  {# Include standard footer #}
%}
```

### 5. Stats Card (`components/stats_card.html`)
A specialized card for displaying statistical information.

#### Usage
```html
{% include "material/components/stats_card.html" with
    stat_label="Statistic Label"
    stat_value=value
    stat_currency=currency_code
    stat_class="text-success|text-danger"
    stat_icon="material_icon_name"
    stat_help_text="Additional context"
%}
```

## Best Practices

### Button Hierarchy
1. **Primary Actions**
   - Use `btn-raised btn-primary` class
   - Include relevant Material icon
   - Example: "Update Income", "Add Expense"

2. **Secondary Actions**
   - Use `btn-secondary` class
   - Include icon for consistency
   - Example: "Cancel", "Back"

### Form Guidelines
1. Always include:
   - Clear labels
   - Helpful placeholder text
   - Help text for context
   - Proper validation attributes

2. Use consistent field spacing:
   - `mb-3` for field groups
   - `gap-2` for button groups

### Modal Implementation
1. Static Modals:
   - Use for important forms
   - Prevent accidental dismissal
   - Example: Income update form

2. Regular Modals:
   - Use for information display
   - Allow easy dismissal
   - Include clear close button

### Stats Display
1. Use Stats Cards for:
   - Key metrics
   - Financial summaries
   - Progress indicators

2. Consistent Formatting:
   - Use currency symbols
   - Include thousands separators
   - Show relevant icons

## Component Integration

### Template Structure
```html
{% extends "material/base.html" %}
{% load humanize %}
{% load budget_filters %}

{% block content %}
    {# Cards for main content #}
    <div class="card mb-4">
        {% include "material/components/card.html" with ... %}
    </div>

    {# Forms with proper styling #}
    <form method="post">
        {% include "material/components/form_field.html" with ... %}
        {% include "material/components/action_button.html" with ... %}
    </form>

    {# Modals for interactive features #}
    {% include "material/components/modal.html" with ... %}
{% endblock %}
```

### Required Template Tags
- Always load `humanize` for number formatting
- Include `budget_filters` for custom filters
- Load `static` when using static assets

## Example Implementations

### Budget Detail Page
```html
{# Income Details Card #}
<div class="card mb-4">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h3 class="mb-0">Income Details</h3>
        {% include "material/components/action_button.html" with
            button_type="button"
            button_class="btn-raised btn-primary"
            button_icon="edit"
            button_text="Update Income"
            data_attributes="data-bs-toggle='modal' data-bs-target='#incomeModal'"
        %}
    </div>
    <div class="card-body">
        {% include "material/components/stats_card.html" with
            stat_label="Monthly Income"
            stat_value=budget.income
            stat_currency=budget.currency
        %}
    </div>
</div>
```

## Maintenance and Updates

### Adding New Components
1. Create component template in `templates/material/components/`
2. Document usage in component header
3. Update this guide with new component
4. Maintain consistent styling

### Modifying Existing Components
1. Preserve backward compatibility
2. Update all instances of component
3. Document changes in component header
4. Update this guide accordingly

## Troubleshooting

### Common Issues
1. **Missing Icons**
   - Ensure Material Icons font is loaded
   - Verify icon name in Material Icons library

2. **Styling Inconsistencies**
   - Check proper class usage
   - Verify Bootstrap/Material Design classes

3. **Template Errors**
   - Load required template tags
   - Check parameter names and values
   - Verify context variables exist
