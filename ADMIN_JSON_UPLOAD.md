# Admin JSON Upload Feature

## Overview

The Exam Stellar admin interface now includes a professional, styled design and a JSON upload feature that allows administrators to upload complete test banks with questions, answer options, and explanations in a single JSON file.

## Features

### 1. Professional Admin Styling
- Modern, clean design with Exam Stellar branding
- Gradient headers and buttons
- Improved form styling and user experience
- Responsive layout

### 2. JSON Upload Functionality
- Upload complete test banks via JSON file
- Import questions with multiple answer options
- Include explanations for correct answers
- Support for updating existing test banks

## How to Use JSON Upload

### Step 1: Access the Upload Page

1. Log in to the admin panel at `http://localhost:8000/admin/`
2. Navigate to **Catalog** → **Test Banks**
3. Click the **"📤 Upload JSON Test Bank"** button at the top right

### Step 2: Prepare Your JSON File

Your JSON file should follow this structure:

```json
{
  "test_bank": {
    "title": "Your Test Bank Title",
    "description": "Description of the test bank",
    "category": "category-slug",
    "certification": "certification-slug",
    "certification_domain": "Information Technology",
    "organization": "CompTIA",
    "official_url": "https://www.example.com/certification",
    "certification_details": "Additional details about the certification",
    "difficulty_level": "easy",
    "price": 0.00,
    "is_active": true
  },
  "questions": [
    {
      "question_text": "Your question text here",
      "question_type": "mcq_single",
      "explanation": "Explanation of the correct answer",
      "order": 1,
      "is_active": true,
      "options": [
        {
          "option_text": "Option A",
          "is_correct": true,
          "order": 1
        },
        {
          "option_text": "Option B",
          "is_correct": false,
          "order": 2
        }
      ]
    }
  ]
}
```

### Step 3: Required Fields

#### Test Bank Section:
- **title** (required): The title of the test bank
- **description** (required): Description of the test bank
- **category**: Name or slug of category (will be created if doesn't exist)
- **certification**: Name or slug of certification (optional, requires category, will be created if doesn't exist). **Note:** The same certification name can exist multiple times under the same category, but each must have a different `difficulty_level`. For example, "PMP" can exist as both "PMP (Easy)" and "PMP (Advanced)" under the same category.
- **certification_domain** (optional, metadata field): Subject area text field for certification metadata (e.g., "Information Technology", "Healthcare", "Finance")
- **organization** (optional): Organization or body that issues the certification (e.g., "CompTIA", "Microsoft", "PMI")
- **official_url** (optional): Official website URL for the certification or organization
- **certification_details** (optional): Additional details about the certification, requirements, or exam information
- **difficulty_level**: "easy", "medium", or "advanced" (default: "easy"). Also accepts "beginner" (maps to "easy"), "intermediate" (maps to "medium"), or "hard" (maps to "advanced")
- **price**: Price in decimal format (default: 0.00)
- **is_active**: true or false (default: true)

**Note:** Categories and certifications are automatically created if they don't exist. You can use either the name (e.g., "Vocational") or slug (e.g., "vocational").

**Important:** When creating certifications, the `difficulty_level` field determines uniqueness. The same certification name (e.g., "PMP") can exist multiple times under the same category, but each instance must have a different difficulty level. The system will automatically create separate certification entries for "PMP (Easy)", "PMP (Medium)", and "PMP (Advanced)" if you upload test banks with the same certification name but different difficulty levels.

#### Question Section:
- **question_text** (required): The question content
- **question_type**: "mcq_single", "mcq_multi", or "true_false" (default: "mcq_single")
- **explanation**: Explanation shown after answering (optional)
- **order**: Order number for the question (default: auto-incremented)
- **is_active**: true or false (default: true)
- **options** (required): Array of answer options

#### Answer Option Section:
- **option_text** (required): The text of the answer option
- **is_correct**: true or false (default: false)
- **order**: Order number for the option (default: auto-incremented)

### Step 4: Upload the File

1. Click **"Choose File"** and select your JSON file
2. (Optional) Select an existing test bank to update instead of creating a new one
3. Click **"Upload & Import"**
4. The system will:
   - Validate the JSON structure
   - Create or update the test bank
   - Import all questions and answer options
   - Show success/error messages

## Question Types

### MCQ Single (`mcq_single`)
Multiple choice question with exactly one correct answer.

Example:
```json
{
  "question_text": "What is 2 + 2?",
  "question_type": "mcq_single",
  "options": [
    {"option_text": "3", "is_correct": false, "order": 1},
    {"option_text": "4", "is_correct": true, "order": 2},
    {"option_text": "5", "is_correct": false, "order": 3}
  ]
}
```

### MCQ Multi (`mcq_multi`)
Multiple choice question with multiple correct answers.

Example:
```json
{
  "question_text": "Which are programming languages?",
  "question_type": "mcq_multi",
  "options": [
    {"option_text": "Python", "is_correct": true, "order": 1},
    {"option_text": "JavaScript", "is_correct": true, "order": 2},
    {"option_text": "HTML", "is_correct": false, "order": 3}
  ]
}
```

### True/False (`true_false`)
Boolean question with True/False options.

Example:
```json
{
  "question_text": "Django is a Python framework.",
  "question_type": "true_false",
  "options": [
    {"option_text": "True", "is_correct": true, "order": 1},
    {"option_text": "False", "is_correct": false, "order": 2}
  ]
}
```

## Important Notes

1. **Hierarchy Requirements**: At least one of `category` or `certification` must be specified. They will be automatically created if they don't exist.

2. **Name or Slug**: You can use either the name (e.g., "Vocational") or slug (e.g., "vocational") for category and certification. The system will find existing ones or create new ones automatically.

3. **Auto-Creation**: Categories and certifications are automatically created if they don't exist. This makes it easy to import test banks without pre-creating the hierarchy.

4. **Updating Existing Test Banks**: If you select an existing test bank to update, all existing questions will be deleted and replaced with the new ones from the JSON file.

5. **File Size**: Maximum file size is 10MB.

6. **Encoding**: JSON files must be UTF-8 encoded.

7. **Validation**: The system validates:
   - JSON structure
   - Required fields
   - Hierarchy relationships (subcategory requires category, certification requires subcategory)
   - Question and option data integrity

## Example JSON File

See `test_bank_template.json` in the project root for a complete example.

## Troubleshooting

### Error: "Category with slug 'xxx' not found"
- This error should no longer occur as categories are auto-created
- If you see this, check your JSON syntax
- Make sure the category field is a string, not null or empty

### Error: "Invalid JSON format"
- Validate your JSON using a JSON validator
- Check for missing commas, brackets, or quotes
- Ensure proper UTF-8 encoding

### Error: "No questions were imported"
- Check that your questions array is not empty
- Verify that each question has at least one option
- Ensure all required fields are present

### Questions imported but some have errors
- Check the warning messages displayed after upload
- Review the question/option data for the indicated question numbers
- Fix the errors and re-upload

## Admin Styling

The admin interface has been enhanced with:
- **Branding**: Exam Stellar logo and colors
- **Modern Design**: Gradient headers, rounded corners, shadows
- **Better Forms**: Improved input styling and focus states
- **Professional Look**: Clean, modern interface matching the main site

All admin pages now feature the Exam Stellar branding and color scheme (#8FABD4, #4A70A9, #EFECE3).

