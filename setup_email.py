#!/usr/bin/env python3
"""
DockSafe Email Configuration Setup Script
This script helps you configure SMTP settings for DockSafe email functionality.
"""

import os
import sys
from getpass import getpass


def setup_email_config():
    """Interactive setup for email configuration"""
    print("🔧 DockSafe Email Configuration Setup")
    print("=" * 50)

    # Check if .env file exists
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"✅ Found existing {env_file} file")
        overwrite = input(
            "Do you want to update the email configuration? (y/N): "
        ).lower()
        if overwrite != "y":
            print("Configuration setup cancelled.")
            return

    # Get SMTP configuration
    print("\n📧 SMTP Configuration")
    print("Choose your email provider:")
    print("1. Gmail (Recommended)")
    print("2. Outlook/Hotmail")
    print("3. Yahoo")
    print("4. Custom SMTP Server")

    choice = input("Enter your choice (1-4): ").strip()

    config = {}

    if choice == "1":  # Gmail
        config.update(
            {
                "DOCSAFE_EMAIL_SMTP_SERVER": "smtp.gmail.com",
                "DOCSAFE_EMAIL_SMTP_PORT": "587",
                "DOCSAFE_EMAIL_USERNAME": "noreply.docksafe@gmail.com",
                "DOCSAFE_EMAIL_FROM": "noreply.docksafe@gmail.com",
                "DOCSAFE_EMAIL_USE_TLS": "true",
            }
        )
        print("\n📝 Gmail Configuration:")
        print("You'll need to:")
        print("1. Enable 2-Factor Authentication on noreply.docksafe@gmail.com")
        print("2. Generate an App Password")
        print("3. Use the App Password (not your regular password)")

    elif choice == "2":  # Outlook
        config.update(
            {
                "DOCSAFE_EMAIL_SMTP_SERVER": "smtp-mail.outlook.com",
                "DOCSAFE_EMAIL_SMTP_PORT": "587",
                "DOCSAFE_EMAIL_USERNAME": input("Enter your Outlook email: "),
                "DOCSAFE_EMAIL_FROM": input("Enter sender email: "),
                "DOCSAFE_EMAIL_USE_TLS": "true",
            }
        )

    elif choice == "3":  # Yahoo
        config.update(
            {
                "DOCSAFE_EMAIL_SMTP_SERVER": "smtp.mail.yahoo.com",
                "DOCSAFE_EMAIL_SMTP_PORT": "587",
                "DOCSAFE_EMAIL_USERNAME": input("Enter your Yahoo email: "),
                "DOCSAFE_EMAIL_FROM": input("Enter sender email: "),
                "DOCSAFE_EMAIL_USE_TLS": "true",
            }
        )

    elif choice == "4":  # Custom
        config.update(
            {
                "DOCSAFE_EMAIL_SMTP_SERVER": input("Enter SMTP server: "),
                "DOCSAFE_EMAIL_SMTP_PORT": input("Enter SMTP port (default 587): ")
                or "587",
                "DOCSAFE_EMAIL_USERNAME": input("Enter SMTP username: "),
                "DOCSAFE_EMAIL_FROM": input("Enter sender email: "),
                "DOCSAFE_EMAIL_USE_TLS": input("Use TLS? (y/N): ").lower() == "y"
                and "true"
                or "false",
            }
        )

    else:
        print("Invalid choice. Exiting.")
        return

    # Get password
    print(f"\n🔐 Password for {config['DOCSAFE_EMAIL_USERNAME']}:")
    password = getpass("Enter password (will be hidden): ")
    config["DOCSAFE_EMAIL_PASSWORD"] = password

    # Write to .env file
    env_content = []

    # Read existing .env if it exists
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            existing_lines = f.readlines()

        # Filter out existing email config lines
        for line in existing_lines:
            if not any(key in line for key in config.keys()):
                env_content.append(line)

    # Add new email configuration
    env_content.append("\n# DockSafe Email Configuration\n")
    for key, value in config.items():
        env_content.append(f"{key}={value}\n")

    # Write to .env file
    with open(env_file, "w") as f:
        f.writelines(env_content)

    print(f"\n✅ Email configuration saved to {env_file}")
    print("\n🧪 Testing email configuration...")

    # Test the configuration
    test_email_config()


def test_email_config():
    """Test the email configuration"""
    try:
        # Load environment variables
        from dotenv import load_dotenv

        load_dotenv()

        # Test SMTP connection
        import smtplib
        import ssl

        smtp_server = os.getenv("DOCSAFE_EMAIL_SMTP_SERVER")
        smtp_port = int(os.getenv("DOCSAFE_EMAIL_SMTP_PORT", 587))
        username = os.getenv("DOCSAFE_EMAIL_USERNAME")
        password = os.getenv("DOCSAFE_EMAIL_PASSWORD")
        use_tls = os.getenv("DOCSAFE_EMAIL_USE_TLS", "true").lower() == "true"

        print(f"Testing connection to {smtp_server}:{smtp_port}...")

        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if use_tls:
                server.starttls(context=context)
            server.login(username, password)
            print("✅ SMTP connection successful!")

    except Exception as e:
        print(f"❌ SMTP connection failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check your email and password")
        print("2. For Gmail, make sure you're using an App Password")
        print("3. Check if 2FA is enabled")
        print("4. Verify SMTP server and port settings")


if __name__ == "__main__":
    setup_email_config()
