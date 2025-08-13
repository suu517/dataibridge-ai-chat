#!/usr/bin/env python3
"""
Production Secret Generator for DataiBridge AI Chat
Generates secure secrets for production deployment
"""

import secrets
import string
import base64
import os
from pathlib import Path

def generate_secure_key(length=32):
    """Generate a cryptographically secure random key"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_jwt_secret():
    """Generate JWT signing secret"""
    return base64.b64encode(secrets.token_bytes(32)).decode('utf-8')

def generate_encryption_key():
    """Generate 32-byte encryption key"""
    return base64.b64encode(secrets.token_bytes(32)).decode('utf-8')[:32]

def main():
    print("🔐 DataiBridge AI Chat - Production Secrets Generator")
    print("=" * 60)
    
    # Generate secrets
    secrets_data = {
        'SECRET_KEY': generate_secure_key(64),
        'JWT_SECRET_KEY': generate_jwt_secret(),
        'ENCRYPTION_KEY': generate_encryption_key(),
        'DATABASE_PASSWORD': generate_secure_key(32),
        'REDIS_PASSWORD': generate_secure_key(32),
    }
    
    print("\n📋 Generated Production Secrets:")
    print("-" * 40)
    
    for key, value in secrets_data.items():
        print(f"{key}={value}")
    
    print("\n" + "=" * 60)
    print("⚠️  IMPORTANT SECURITY NOTES:")
    print("1. Store these secrets securely (password manager, AWS Secrets Manager)")
    print("2. Never commit secrets to version control")
    print("3. Use environment variables or GitHub Secrets")
    print("4. Rotate secrets regularly in production")
    print("5. Different secrets for different environments")
    
    # Save to .env.production.example
    env_file = Path(__file__).parent.parent / '.env.production.example'
    
    with open(env_file, 'w') as f:
        f.write("# Production Environment Variables Template\n")
        f.write("# Copy to .env.production and update values\n")
        f.write("# DO NOT commit actual secrets to version control\n\n")
        
        f.write("# Application Secrets\n")
        for key, value in secrets_data.items():
            f.write(f"{key}={value}\n")
        
        f.write("\n# External Service Keys (UPDATE THESE)\n")
        f.write("OPENAI_API_KEY=sk-proj-your-actual-openai-key-here\n")
        f.write("AZURE_OPENAI_API_KEY=your-azure-openai-key-here\n")
        f.write("AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/\n")
        
        f.write("\n# Email Configuration (UPDATE THESE)\n")
        f.write("SMTP_HOST=smtp.mailtrap.io\n")
        f.write("SMTP_PORT=2525\n")
        f.write("SMTP_USERNAME=your-smtp-username\n")
        f.write("SMTP_PASSWORD=your-smtp-password\n")
        
        f.write("\n# AWS Configuration\n")
        f.write("AWS_REGION=ap-northeast-1\n")
        f.write("AWS_ACCESS_KEY_ID=your-aws-access-key\n")
        f.write("AWS_SECRET_ACCESS_KEY=your-aws-secret-key\n")
        
        f.write("\n# Database URLs (Will be set by Terraform)\n")
        f.write("DATABASE_URL=postgresql+asyncpg://username:password@host:5432/dbname\n")
        f.write("REDIS_URL=redis://:password@host:6379/0\n")
    
    print(f"\n📁 Secrets template saved to: {env_file}")
    print("\n🚀 Next steps:")
    print("1. Copy .env.production.example to .env.production")
    print("2. Update API keys and service credentials")
    print("3. Add secrets to GitHub repository secrets")
    print("4. Configure AWS Secrets Manager for production")

if __name__ == "__main__":
    main()