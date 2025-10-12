# 📧 DockSafe Email Configuration Guide

## 🚀 Quick Setup

### Option 1: Using the Setup Script (Recommended)
```bash
cd /Users/glenveigas437/Documents/Code/Flask\ Apps/DockSafe/DockSafe
source ../venv/bin/activate
python3 setup_email.py
```

### Option 2: Manual Configuration

1. **Create a `.env` file** in the DockSafe directory:
```bash
touch .env
```

2. **Add SMTP configuration** to `.env`:
```env
# DockSafe Email Configuration
DOCSAFE_EMAIL_SMTP_SERVER=smtp.gmail.com
DOCSAFE_EMAIL_SMTP_PORT=587
DOCSAFE_EMAIL_USERNAME=noreply.docksafe@gmail.com
DOCSAFE_EMAIL_PASSWORD=your-app-password-here
DOCSAFE_EMAIL_FROM=noreply.docksafe@gmail.com
DOCSAFE_EMAIL_USE_TLS=true
```

## 🔐 Gmail Setup (Recommended)

### Step 1: Enable 2-Factor Authentication
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Step Verification
3. Follow the setup process

### Step 2: Generate App Password
1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Select "Mail" and "Other (Custom name)"
3. Enter "DockSafe" as the name
4. Copy the generated 16-character password
5. Use this password in your `.env` file

### Step 3: Configure Environment
```env
DOCSAFE_EMAIL_PASSWORD=abcd efgh ijkl mnop
```

## 📧 Alternative Email Providers

### Outlook/Hotmail
```env
DOCSAFE_EMAIL_SMTP_SERVER=smtp-mail.outlook.com
DOCSAFE_EMAIL_SMTP_PORT=587
DOCSAFE_EMAIL_USERNAME=your-email@outlook.com
DOCSAFE_EMAIL_PASSWORD=your-password
DOCSAFE_EMAIL_FROM=your-email@outlook.com
DOCSAFE_EMAIL_USE_TLS=true
```

### Yahoo Mail
```env
DOCSAFE_EMAIL_SMTP_SERVER=smtp.mail.yahoo.com
DOCSAFE_EMAIL_SMTP_PORT=587
DOCSAFE_EMAIL_USERNAME=your-email@yahoo.com
DOCSAFE_EMAIL_PASSWORD=your-app-password
DOCSAFE_EMAIL_FROM=your-email@yahoo.com
DOCSAFE_EMAIL_USE_TLS=true
```

### Custom SMTP Server
```env
DOCSAFE_EMAIL_SMTP_SERVER=your-smtp-server.com
DOCSAFE_EMAIL_SMTP_PORT=587
DOCSAFE_EMAIL_USERNAME=your-username
DOCSAFE_EMAIL_PASSWORD=your-password
DOCSAFE_EMAIL_FROM=noreply@yourdomain.com
DOCSAFE_EMAIL_USE_TLS=true
```

## 🧪 Testing Email Configuration

### Test SMTP Connection
```bash
cd /Users/glenveigas437/Documents/Code/Flask\ Apps/DockSafe/DockSafe
source ../venv/bin/activate
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

import smtplib
import ssl

smtp_server = os.getenv('DOCSAFE_EMAIL_SMTP_SERVER')
smtp_port = int(os.getenv('DOCSAFE_EMAIL_SMTP_PORT', 587))
username = os.getenv('DOCSAFE_EMAIL_USERNAME')
password = os.getenv('DOCSAFE_EMAIL_PASSWORD')

try:
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls(context=context)
        server.login(username, password)
        print('✅ SMTP connection successful!')
except Exception as e:
    print(f'❌ SMTP connection failed: {e}')
"
```

### Test DockSafe Email Service
```bash
python3 -c "
import os
import sys
sys.path.append('.')
from app import create_app
from app.services.email_service import EmailService

app = create_app()
with app.app_context():
    token = EmailService.generate_verification_token()
    success = EmailService.send_verification_email('test@example.com', token, 'Test User')
    print(f'Email test: {\"✅ Success\" if success else \"❌ Failed\"}')
"
```

## 🔧 Troubleshooting

### Common Issues

1. **"Authentication failed"**
   - Check username and password
   - For Gmail, use App Password, not regular password
   - Ensure 2FA is enabled

2. **"Connection refused"**
   - Check SMTP server and port
   - Verify firewall settings
   - Try different port (465 for SSL, 587 for TLS)

3. **"TLS/SSL errors"**
   - Set `DOCSAFE_EMAIL_USE_TLS=true`
   - Check if server supports STARTTLS

4. **"Email not delivered"**
   - Check spam folder
   - Verify sender email is valid
   - Check SMTP server logs

### Debug Mode
Enable debug logging to see detailed SMTP information:
```env
LOG_LEVEL=DEBUG
```

## 📋 Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `DOCSAFE_EMAIL_SMTP_SERVER` | SMTP server hostname | `smtp.gmail.com` |
| `DOCSAFE_EMAIL_SMTP_PORT` | SMTP server port | `587` |
| `DOCSAFE_EMAIL_USERNAME` | SMTP username | `noreply.docksafe@gmail.com` |
| `DOCSAFE_EMAIL_PASSWORD` | SMTP password | None (required) |
| `DOCSAFE_EMAIL_FROM` | Sender email address | `noreply.docksafe@gmail.com` |
| `DOCSAFE_EMAIL_USE_TLS` | Use TLS encryption | `true` |

## 🎯 Next Steps

1. **Configure SMTP** using one of the methods above
2. **Test the configuration** using the test scripts
3. **Restart DockSafe** to load new environment variables
4. **Send a test email** through the profile page
5. **Check your inbox** for the verification email

## 📞 Support

If you encounter issues:
1. Check the application logs for detailed error messages
2. Verify your SMTP credentials
3. Test with a simple SMTP client first
4. Contact your email provider for SMTP settings
