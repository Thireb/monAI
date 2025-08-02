# Minimal Theme Development Guidelines

## Page Height and Background Standards

### ✅ **Height Fix Strategy (Implemented)**
Currently, pages need individual height fixes until we perfect the global solution:
- **Base Template**: Has `page-content-wrapper` class but needs refinement
- **Theme CSS**: Has global styles but may need page-specific overrides
- **Current Approach**: Use page-specific containers with `min-height: 100vh` and background gradient

### 🎯 **For New Pages**

#### **Template Structure (Required)**
```html
{% extends "minimal/base.html" %}
{% load static %}

{% block extra_css %}
<!-- Page-specific CSS here -->
{% endblock extra_css %}

{% block content %}
<div class="[page-name]-container">
  <!-- Your page content here -->
  <!-- Add page-specific container for height fix -->
</div>
{% endblock content %}

{% block extra_js %}
<!-- Page-specific JS here -->
{% endblock extra_js %}
```

#### **CSS Guidelines**
- **DO** add height and background fixes to page-specific CSS for now
- **DO** use the existing theme classes and patterns
- **DO** follow the established folder structure:
  ```
  static/css/minimal-css/[feature]/[page].css
  static/js/minimal-js/[feature]/[page].js
  ```
- **DO** add page-specific container styles:
  ```css
  .[page-name]-container {
    min-height: 100vh;
    background: linear-gradient(135deg, #f3f6fa 0%, #e9eafc 100%) !important;
  }
  ```

### 🚫 **Common Mistakes to Avoid**

1. **Don't forget to add page-specific height containers** - Currently needed until global fix is perfected
2. **Don't override background gradients** - Use theme colors
3. **Don't use different background gradients** - Stick to the standard gradient

### ✅ **What's Already Handled**

- ✅ Full viewport height coverage
- ✅ Consistent background gradient
- ✅ Navigation height compensation
- ✅ Bottom padding for content
- ✅ Responsive behavior

### 🔧 **If You Need Custom Heights**

For special cases (like modals or overlays), use:
```css
.custom-overlay {
  min-height: 100vh;
  background: linear-gradient(135deg, #f3f6fa 0%, #e9eafc 100%);
}
```

### 📋 **Development Checklist**

Before creating a new page:
- [ ] Extends `minimal/base.html`
- [ ] Uses standard block structure
- [ ] No custom height/background CSS
- [ ] Follows established folder structure
- [ ] Uses theme color palette
- [ ] Includes proper meta tags

### 🎨 **Theme Color Palette**

```css
/* Primary Colors */
--primary-blue: #2196f3;
--primary-green: #4caf50;
--primary-red: #e53935;
--primary-yellow: #ffd600;

/* Background Gradients */
--bg-gradient: linear-gradient(135deg, #f3f6fa 0%, #e9eafc 100%);
```

### 📁 **File Organization**

```
templates/minimal/
├── base.html (handles height automatically)
├── [feature]/
│   └── [page].html

static/css/minimal-css/
├── theme/theme.css (global styles)
├── [feature]/
│   └── [page].css

static/js/minimal-js/
├── [feature]/
│   └── [page].js
```

### 🔄 **Migration Guide**

If you find old pages with custom height fixes:

1. **Remove page-specific height CSS**
2. **Remove custom container classes**
3. **Ensure page extends `minimal/base.html`**
4. **Test that height still works correctly**

### 🧪 **Testing Checklist**

- [ ] Page background extends to full height
- [ ] No white space at bottom
- [ ] Content is properly spaced
- [ ] Responsive on mobile/desktop
- [ ] Navigation works correctly
- [ ] Theme colors are consistent

---

**Remember**: The base template now handles all height and background issues automatically. Focus on your page's unique functionality, not layout basics!
