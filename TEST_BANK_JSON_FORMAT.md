# 📋 Test Bank JSON Format Specification

**Version:** 2.0  
**Last Updated:** February 23, 2026  
**Reference File:** `test_bank_template.json`

---

## Complete JSON Structure

```json
{
  "test_bank": {
    "title": "Your Test Bank Title",
    "description": "Description of the test bank",
    "category": "category-name-or-slug",
    "certification": "certification-name-or-slug",
    "certification_domain": "Information Technology",
    "organization": "CompTIA",
    "official_url": "https://www.example.com/certification",
    "certification_details": "Additional details about the certification",
    "difficulty_level": "easy",
    "price": 0.00,
    "time_limit_minutes": 60,
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

---

## Test Bank Object Fields

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `title` | string | Title of the test bank | `"CompTIA Security+ Practice Exam"` |
| `description` | string | Detailed description | `"Comprehensive practice questions for CompTIA Security+ certification exam"` |

### Optional Fields

| Field | Type | Description | Default | Example |
|-------|------|-------------|---------|---------|
| `category` | string | Category name or slug | `null` | `"Vocational"` or `"vocational"` |
| `certification` | string | Certification name or slug | `null` | `"CompTIA Security+"` |
| `certification_url` | string | Official URL for the certification (saved to Certification model) | `null` | `"https://www.comptia.org/certifications/security"` |
| `certification_domain` | string | Subject area (metadata) | `null` | `"Information Technology"` |
| `organization` | string | Issuing organization | `null` | `"CompTIA"`, `"Microsoft"`, `"PMI"` |
| `official_url` | string | Official URL for test bank (saved to TestBank model) | `null` | `"https://www.comptia.org/certifications/security"` |
| `certification_details` | string | Additional certification details | `null` | `"Globally recognized certification..."` |
| `difficulty_level` | string | Difficulty level | `"easy"` | `"easy"`, `"medium"`, `"advanced"` |
| `price` | number | Price in decimal | `0.00` | `29.99`, `0.00` |
| `time_limit_minutes` | integer | Time limit for exam (minutes) | `null` (unlimited) | `60`, `90`, `120` |
| `is_active` | boolean | Whether test bank is active | `true` | `true`, `false` |

### Field Details

#### `category`
- **Type:** String (name or slug)
- **Behavior:** Auto-created if doesn't exist
- **Examples:** `"Vocational"`, `"vocational"`, `"Professional"`

#### `certification`
- **Type:** String (name or slug)
- **Behavior:** Auto-created if doesn't exist (requires category)
- **Note:** Same certification name can exist with different `difficulty_level` values
- **Examples:** `"CompTIA Security+"`, `"PMP"`, `"AWS Certified Solutions Architect"`

#### `certification_url`
- **Type:** String (URL)
- **Behavior:** Saved to the Certification model's `official_url` field when certification is created/updated
- **Note:** This URL is specific to the certification itself, not the test bank
- **Examples:** `"https://www.comptia.org/certifications/security"`, `"https://www.pmi.org/certifications/project-management-pmp"`
- **Fallback:** If `certification_url` is not provided, the system will use `official_url` from test_bank data

#### `difficulty_level`
- **Accepted Values:**
  - `"easy"` or `"beginner"`
  - `"medium"` or `"intermediate"`
  - `"advanced"` or `"hard"`
- **Default:** `"easy"`
- **Note:** Determines uniqueness when combined with certification name

#### `time_limit_minutes`
- **Type:** Integer (positive number)
- **Behavior:** 
  - `null` or omitted = No time limit
  - Number = Time limit in minutes
- **Examples:** `60` (1 hour), `90` (1.5 hours), `120` (2 hours)
- **Feature:** When set, practice sessions will show a timer and auto-submit when time expires

---

## Question Object Fields

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `question_text` | string | The question content | `"What is the capital of France?"` |
| `options` | array | Array of answer options | See Options section below |

### Optional Fields

| Field | Type | Description | Default | Example |
|-------|------|-------------|---------|---------|
| `question_type` | string | Type of question | `"mcq_single"` | `"mcq_single"`, `"mcq_multi"`, `"true_false"` |
| `explanation` | string | Explanation shown after answering | `""` | `"Paris is the capital..."` |
| `order` | integer | Display order | Auto-incremented | `1`, `2`, `3` |
| `is_active` | boolean | Whether question is active | `true` | `true`, `false` |

### Question Types

#### 1. MCQ Single (`mcq_single`)
- **Description:** Multiple choice with exactly one correct answer
- **Requirements:** Exactly one option must have `is_correct: true`
- **Example:**
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

#### 2. MCQ Multi (`mcq_multi`)
- **Description:** Multiple choice with multiple correct answers
- **Requirements:** At least one option must have `is_correct: true`
- **Example:**
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

#### 3. True/False (`true_false`)
- **Description:** Boolean question with True/False options
- **Requirements:** Exactly two options (True and False), one must be correct
- **Example:**
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

---

## Answer Option Object Fields

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `option_text` | string | The text of the answer option | `"Paris"` |
| `is_correct` | boolean | Whether this option is correct | `true`, `false` |

### Optional Fields

| Field | Type | Description | Default | Example |
|-------|------|-------------|---------|---------|
| `order` | integer | Display order | Auto-incremented | `1`, `2`, `3` |

---

## Complete Example

```json
{
  "test_bank": {
    "title": "CompTIA Security+ Practice Exam",
    "description": "Comprehensive practice questions covering all domains of the CompTIA Security+ SY0-601 exam. Includes questions on network security, threats and vulnerabilities, identity and access management, and more.",
    "category": "Professional",
    "certification": "CompTIA Security+",
    "certification_url": "https://www.comptia.org/certifications/security",
    "certification_domain": "Information Technology",
    "organization": "CompTIA",
    "official_url": "https://www.comptia.org/certifications/security",
    "certification_details": "CompTIA Security+ is a globally recognized certification that validates the baseline skills necessary to perform core security functions and pursue an IT security career. The exam covers network security, compliance and operational security, threats and vulnerabilities, application, data and host security, access control and identity management, and cryptography.",
    "difficulty_level": "medium",
    "price": 29.99,
    "time_limit_minutes": 90,
    "is_active": true
  },
  "questions": [
    {
      "question_text": "What is the primary purpose of a firewall?",
      "question_type": "mcq_single",
      "explanation": "A firewall is a network security device that monitors and filters incoming and outgoing network traffic based on an organization's previously established security policies. Its primary purpose is to create a barrier between a trusted internal network and untrusted external networks.",
      "order": 1,
      "is_active": true,
      "options": [
        {
          "option_text": "To prevent unauthorized access to a network",
          "is_correct": true,
          "order": 1
        },
        {
          "option_text": "To encrypt data in transit",
          "is_correct": false,
          "order": 2
        },
        {
          "option_text": "To store backup data",
          "is_correct": false,
          "order": 3
        },
        {
          "option_text": "To manage user passwords",
          "is_correct": false,
          "order": 4
        }
      ]
    },
    {
      "question_text": "Which of the following are types of malware? (Select all that apply)",
      "question_type": "mcq_multi",
      "explanation": "Malware includes various types of malicious software. Viruses attach themselves to legitimate programs and replicate when executed. Worms are self-replicating malware that spread across networks. Trojans disguise themselves as legitimate software. Ransomware encrypts files and demands payment. Spyware collects information without user knowledge.",
      "order": 2,
      "is_active": true,
      "options": [
        {
          "option_text": "Virus",
          "is_correct": true,
          "order": 1
        },
        {
          "option_text": "Worm",
          "is_correct": true,
          "order": 2
        },
        {
          "option_text": "Trojan",
          "is_correct": true,
          "order": 3
        },
        {
          "option_text": "Firewall",
          "is_correct": false,
          "order": 4
        },
        {
          "option_text": "Antivirus",
          "is_correct": false,
          "order": 5
        }
      ]
    },
    {
      "question_text": "Multi-factor authentication requires at least two different authentication factors.",
      "question_type": "true_false",
      "explanation": "Multi-factor authentication (MFA) requires users to provide two or more different authentication factors from different categories: something you know (password), something you have (token), or something you are (biometric).",
      "order": 3,
      "is_active": true,
      "options": [
        {
          "option_text": "True",
          "is_correct": true,
          "order": 1
        },
        {
          "option_text": "False",
          "is_correct": false,
          "order": 2
        }
      ]
    }
  ]
}
```

---

## Validation Rules

### Test Bank Validation
- ✅ `title` must be provided and non-empty
- ✅ `description` must be provided and non-empty
- ✅ At least one of `category` or `certification` must be provided
- ✅ `difficulty_level` must be one of: `"easy"`, `"medium"`, `"advanced"` (or aliases)
- ✅ `price` must be a non-negative number
- ✅ `time_limit_minutes` must be a positive integer if provided
- ✅ `is_active` must be boolean

### Question Validation
- ✅ `question_text` must be provided and non-empty
- ✅ `question_type` must be one of: `"mcq_single"`, `"mcq_multi"`, `"true_false"`
- ✅ `options` array must contain at least 2 options
- ✅ For `mcq_single`: Exactly one option must be correct
- ✅ For `mcq_multi`: At least one option must be correct
- ✅ For `true_false`: Exactly two options required, one correct

### Option Validation
- ✅ `option_text` must be provided and non-empty
- ✅ `is_correct` must be boolean
- ✅ `order` should be unique within a question

---

## Auto-Creation Behavior

### Categories
- If category doesn't exist, it will be automatically created
- You can use either name (`"Vocational"`) or slug (`"vocational"`)
- Slug is auto-generated from name if not provided

### Certifications
- If certification doesn't exist, it will be automatically created
- Requires a category (will use test bank's category if not specified)
- Same certification name can exist with different `difficulty_level` values
- Example: "PMP" can exist as:
  - "PMP (Easy)" with `difficulty_level: "easy"`
  - "PMP (Medium)" with `difficulty_level: "medium"`
  - "PMP (Advanced)" with `difficulty_level: "advanced"`

---

## Usage Instructions

### 1. Create JSON File
- Use UTF-8 encoding
- Follow the structure above
- Validate JSON syntax before uploading

### 2. Upload via Admin
1. Log in to admin panel: `http://localhost:8000/admin/`
2. Navigate to **Catalog** → **Test Banks**
3. Click **"📤 Upload JSON Test Bank"** button
4. Select your JSON file
5. (Optional) Select existing test bank to update
6. Click **"Upload & Import"**

### 3. Verify Import
- Check success/error messages
- Review imported test bank in admin
- Test questions in practice session

---

## Tips & Best Practices

1. **Use Descriptive Titles**: Make test bank titles clear and specific
2. **Provide Explanations**: Always include explanations for better learning
3. **Order Questions**: Use `order` field to control question sequence
4. **Time Limits**: Set appropriate `time_limit_minutes` for timed exams
5. **Test Before Upload**: Validate JSON structure and test with sample data
6. **Backup Data**: Keep backups of your JSON files
7. **Version Control**: Use version control for your JSON files

---

## Troubleshooting

### Common Errors

**"Invalid JSON format"**
- Validate JSON using a JSON validator
- Check for missing commas, brackets, or quotes
- Ensure proper UTF-8 encoding

**"Category not found"**
- Categories are auto-created, so this shouldn't occur
- Check JSON syntax and field names

**"No questions imported"**
- Ensure `questions` array is not empty
- Verify each question has at least 2 options
- Check that all required fields are present

**"Invalid question type"**
- Use only: `"mcq_single"`, `"mcq_multi"`, or `"true_false"`
- Check spelling and case sensitivity

**"No correct answer specified"**
- Ensure at least one option has `is_correct: true`
- For `mcq_single`, exactly one must be correct

---

## File Reference

- **Template File:** `test_bank_template.json`
- **Documentation:** `ADMIN_JSON_UPLOAD.md`
- **Import Function:** `catalog/utils.py` → `import_test_bank_from_json()`

---

*Last Updated: February 23, 2026*  
*Format Version: 2.0*
