# Email Service Testing Guide

This guide explains how to test the email service functionality.

## 📋 Prerequisites

1. **Install test dependencies:**
```bash
pip install -r requirements-test.txt
```

2. **Set up environment variables** (for real email tests):
```bash
# Add to your .env file
APP_AWS_ACCESS_KEY_ID=your_aws_key
APP_AWS_SECRET_ACCESS_KEY=your_aws_secret
APP_AWS_REGION=us-east-1
APP_SES_SENDER_EMAIL=noreply@yourdomain.com
APP_EMAIL_TEMPLATES_DIR=templates/emails
```

## 🚀 Quick Start

### Option 1: Run All Tests with Mock (Safest)
```bash
python tests/run_email_tests.py --mode mock
```

### Option 2: Run Pytest Unit Tests
```bash
pytest tests/test_email_service.py -v
```

### Option 3: Run Specific Test
```bash
pytest tests/test_email_service.py::test_send_simple_email -v
```

## 📝 Test Modes

### 1. Mock Mode (Safe - No Real Emails)
Tests email functionality with mocked AWS SES. **Recommended for development.**

```bash
python tests/run_email_tests.py --mode mock
```

**What it tests:**
- ✅ Email service initialization
- ✅ Email sending logic
- ✅ Error handling
- ✅ Context preparation
- ✅ Integration between services

**What it doesn't do:**
- ❌ Send real emails
- ❌ Connect to AWS
- ❌ Use actual credentials

### 2. Real Mode (Sends Actual Emails)
Tests with real AWS SES. **Use with caution!**

```bash
python tests/run_email_tests.py --mode real
```

**Requirements:**
- Valid AWS credentials in `.env`
- Verified sender email in AWS SES
- Verified recipient email (if in sandbox mode)

**Warning:** This will send real emails and may incur AWS charges.

### 3. Unit Test Mode (Pytest)
Runs comprehensive pytest test suite.

```bash
python tests/run_email_tests.py --mode unittest
# or
pytest tests/test_email_service.py -v
```

### 4. All Modes
Runs all test modes sequentially.

```bash
python tests/run_email_tests.py --mode all
```

## 🧪 Available Tests

### EmailService Tests
```bash
pytest tests/test_email_service.py::TestEmailService -v
```

Tests:
- ✅ Service initialization
- ✅ Successful email sending
- ✅ Email sending failures
- ✅ Template rendering
- ✅ Error handling

### NotificationService Tests
```bash
pytest tests/test_email_service.py::TestNotificationService -v
```

Tests:
- ✅ Email log creation
- ✅ Template email sending
- ✅ Failure logging
- ✅ Database integration

### PaymentService Email Tests
```bash
pytest tests/test_email_service.py::TestPaymentServiceEmail -v
```

Tests:
- ✅ Thank you email sending
- ✅ Safe error handling
- ✅ Email context formatting
- ✅ Payment-email integration
- ✅ Email retry functionality

### Integration Tests
```bash
pytest tests/test_email_service.py::TestEmailIntegration -v
```

Tests:
- ✅ Complete donation-to-email flow
- ✅ Database operations
- ✅ Service interactions

## 📊 Test Coverage

Generate coverage report:
```bash
pytest tests/test_email_service.py --cov=apps.notifications --cov=core.notifications --cov-report=html
```

View report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## 🔍 Running Specific Tests

### Run only email service tests:
```bash
pytest tests/test_email_service.py::TestEmailService -v
```

### Run only one test function:
```bash
pytest tests/test_email_service.py::TestEmailService::test_send_email_success -v
```

### Run tests by marker:
```bash
pytest -m email  # Only email tests
pytest -m unit   # Only unit tests
pytest -m "not slow"  # Skip slow tests
```

## 🐛 Debugging Tests

### Run with verbose output:
```bash
pytest tests/test_email_service.py -vv
```

### Show print statements:
```bash
pytest tests/test_email_service.py -s
```

### Stop on first failure:
```bash
pytest tests/test_email_service.py -x
```

### Run last failed tests:
```bash
pytest tests/test_email_service.py --lf
```

### Enter debugger on failure:
```bash
pytest tests/test_email_service.py --pdb
```

## 📧 Testing Email Templates

### Test template rendering:
```python
from core.notifications.email import EmailService

service = EmailService(
    aws_access_key_id="mock",
    aws_secret_access_key="mock",
    aws_region="us-east-1",
    sender_email="test@example.com",
    templates_dir="templates/emails"
)

context = {
    "full_name": "Test User",
    "order_id": "SK-123",
    "amount": "1,000.00",
    # ... other context
}

html, text = service.render_template("donation_thank_you.html", context)
print(html)  # View rendered HTML
```

### Validate template variables:
```bash
# Create a test script
cat > validate_template.py << 'EOF'
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('templates/emails'))
template = env.get_template('donation_thank_you.html')

# Find all variables used in template
from jinja2 import meta
source = env.loader.get_source(env, 'donation_thank_you.html')[0]
parsed = env.parse(source)
variables = meta.find_undeclared_variables(parsed)

print("Template variables:", variables)
EOF

python validate_template.py
```

## 🎯 Best Practices

### 1. Always run mock tests first
```bash
python tests/run_email_tests.py --mode mock
```

### 2. Use pytest markers for organization
```python
@pytest.mark.email
@pytest.mark.unit
async def test_something():
    pass
```

### 3. Test error conditions
```python
async def test_email_failure():
    # Mock service to fail
    # Verify error handling
    pass
```

### 4. Clean up test data
```python
@pytest.fixture
async def sample_data(async_session):
    # Create test data
    yield data
    # Clean up
    await async_session.rollback()
```

### 5. Use descriptive test names
```python
def test_send_email_creates_log_with_correct_status():
    pass  # Clear what this tests
```

## 🔒 Testing in CI/CD

### GitHub Actions Example:
```yaml
name: Email Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.12
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests
        run: pytest tests/test_email_service.py -v
```

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [AWS SES Testing](https://docs.aws.amazon.com/ses/latest/dg/send-email-simulator.html)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)

## ❓ FAQ

**Q: Can I test without AWS credentials?**  
A: Yes! Use mock mode: `python tests/run_email_tests.py --mode mock`

**Q: How do I test with real emails safely?**  
A: Use AWS SES sandbox mode and verify recipient emails first.

**Q: Tests are slow, how to speed up?**  
A: Run specific tests: `pytest tests/test_email_service.py::TestClass::test_method`

**Q: How do I test email templates?**  
A: Use the template validation script or render templates directly.

**Q: Email tests fail in CI/CD?**  
A: Make sure to run in mock mode in CI/CD pipelines.

## 🆘 Troubleshooting

### Issue: "AWS credentials not found"
**Solution:** Set credentials in `.env` or use mock mode.

### Issue: "Template not found"
**Solution:** Check `EMAIL_TEMPLATES_DIR` path and template file location.

### Issue: "Email not received"
**Solution:** 
- Check spam folder
- Verify email in AWS SES (if in sandbox)
- Check AWS SES sending limits

### Issue: "Tests hang"
**Solution:** Check for async/await issues, ensure proper cleanup.

---

**Last Updated:** 2025-01-06  
**Maintained By:** Development Team