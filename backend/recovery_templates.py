"""
Recovery Task Templates — Pre-built checklists per platform
============================================================
Each template defines recovery tasks with:
  - task_key: unique identifier
  - title: user-facing title
  - description: step-by-step instructions
  - help_url: direct link to platform's security settings page
"""

from typing import List, Dict

# Each task is a dict: { task_key, title, description, help_url, sort_order }
RECOVERY_TEMPLATES: Dict[str, List[dict]] = {
    "google": [
        {
            "task_key": "change_password",
            "title": "Change your Google password",
            "description": "Go to your Google Account → Security → Password. Choose a strong, unique password that you don't use anywhere else.",
            "help_url": "https://myaccount.google.com/signinoptions/password",
            "sort_order": 1,
        },
        {
            "task_key": "enable_2fa",
            "title": "Enable 2-Step Verification",
            "description": "Go to Security → 2-Step Verification → Get started. Use an authenticator app (Google Authenticator, Authy) instead of SMS for better security.",
            "help_url": "https://myaccount.google.com/signinoptions/two-step-verification",
            "sort_order": 2,
        },
        {
            "task_key": "revoke_sessions",
            "title": "Review & revoke active sessions",
            "description": "Go to Security → Your devices. Sign out from any device you don't recognize. Also check 'Recent security activity' for suspicious login attempts.",
            "help_url": "https://myaccount.google.com/security#activity",
            "sort_order": 3,
        },
        {
            "task_key": "check_forwarding",
            "title": "Check email forwarding rules",
            "description": "Open Gmail → Settings (⚙️) → See all settings → Forwarding and POP/IMAP. Make sure no unknown forwarding address is set up. Also check Filters for rules that auto-forward or delete emails.",
            "help_url": "https://mail.google.com/mail/u/0/#settings/fwdandpop",
            "sort_order": 4,
        },
        {
            "task_key": "review_app_access",
            "title": "Remove suspicious third-party apps",
            "description": "Go to Security → Third-party apps with account access. Remove any apps you don't recognize or no longer use.",
            "help_url": "https://myaccount.google.com/permissions",
            "sort_order": 5,
        },
        {
            "task_key": "update_recovery",
            "title": "Update recovery email & phone",
            "description": "Go to Security → Ways we can verify it's you. Make sure your recovery email and phone are current and yours.",
            "help_url": "https://myaccount.google.com/signinoptions/rescuephone",
            "sort_order": 6,
        },
    ],

    "facebook": [
        {
            "task_key": "change_password",
            "title": "Change your Facebook password",
            "description": "Go to Settings → Security and Login → Change password. Use a strong, unique password.",
            "help_url": "https://www.facebook.com/settings?tab=security",
            "sort_order": 1,
        },
        {
            "task_key": "enable_2fa",
            "title": "Enable Two-Factor Authentication",
            "description": "Go to Settings → Security and Login → Two-Factor Authentication. Use an authenticator app for best security.",
            "help_url": "https://www.facebook.com/security/2fac/settings/",
            "sort_order": 2,
        },
        {
            "task_key": "revoke_sessions",
            "title": "Review active sessions",
            "description": "Go to Settings → Security and Login → 'Where You're Logged In'. End any sessions you don't recognize.",
            "help_url": "https://www.facebook.com/settings?tab=security",
            "sort_order": 3,
        },
        {
            "task_key": "review_app_access",
            "title": "Remove suspicious apps",
            "description": "Go to Settings → Apps and Websites. Remove apps you don't use or trust.",
            "help_url": "https://www.facebook.com/settings?tab=applications",
            "sort_order": 4,
        },
        {
            "task_key": "update_recovery",
            "title": "Update contact info",
            "description": "Go to Settings → General → Contact. Make sure your email and phone number are correct.",
            "help_url": "https://www.facebook.com/settings?tab=general",
            "sort_order": 5,
        },
    ],

    "microsoft": [
        {
            "task_key": "change_password",
            "title": "Change your Microsoft password",
            "description": "Go to account.microsoft.com → Security → Change password. Use a strong, unique password.",
            "help_url": "https://account.microsoft.com/security",
            "sort_order": 1,
        },
        {
            "task_key": "enable_2fa",
            "title": "Set up Two-Step Verification",
            "description": "Go to Security → Advanced security options → Two-step verification → Turn on. Use Microsoft Authenticator app.",
            "help_url": "https://account.microsoft.com/security/advanced",
            "sort_order": 2,
        },
        {
            "task_key": "revoke_sessions",
            "title": "Review sign-in activity",
            "description": "Go to Security → Sign-in activity. Check for unfamiliar locations or devices and revoke any suspicious sessions.",
            "help_url": "https://account.microsoft.com/security#activity",
            "sort_order": 3,
        },
        {
            "task_key": "check_forwarding",
            "title": "Check Outlook forwarding rules",
            "description": "Open Outlook.com → Settings → Mail → Forwarding. Disable forwarding if you didn't set it up. Also check Rules for anything suspicious.",
            "help_url": "https://outlook.live.com/mail/0/options/mail/forwarding",
            "sort_order": 4,
        },
        {
            "task_key": "update_recovery",
            "title": "Update security info",
            "description": "Go to Security → Update info. Make sure your recovery email and phone are current.",
            "help_url": "https://account.microsoft.com/security",
            "sort_order": 5,
        },
    ],

    "instagram": [
        {
            "task_key": "change_password",
            "title": "Change your Instagram password",
            "description": "Open Instagram → Settings → Security → Password. Use a unique password not shared with other accounts.",
            "help_url": "https://www.instagram.com/accounts/password/change/",
            "sort_order": 1,
        },
        {
            "task_key": "enable_2fa",
            "title": "Enable Two-Factor Authentication",
            "description": "Go to Settings → Security → Two-Factor Authentication. Use an authentication app instead of SMS.",
            "help_url": "https://www.instagram.com/accounts/two_factor_authentication/",
            "sort_order": 2,
        },
        {
            "task_key": "revoke_sessions",
            "title": "Check login activity",
            "description": "Go to Settings → Security → Login Activity. Log out of any sessions you don't recognize.",
            "help_url": "https://www.instagram.com/session/login_activity/",
            "sort_order": 3,
        },
        {
            "task_key": "review_app_access",
            "title": "Remove authorized apps",
            "description": "Go to Settings → Security → Apps and Websites. Revoke access for apps you no longer use.",
            "help_url": "https://www.instagram.com/accounts/manage_access/",
            "sort_order": 4,
        },
    ],

    "apple": [
        {
            "task_key": "change_password",
            "title": "Change your Apple ID password",
            "description": "Go to appleid.apple.com → Sign-In and Security → Password. Choose a strong password.",
            "help_url": "https://appleid.apple.com/account/manage/security/password",
            "sort_order": 1,
        },
        {
            "task_key": "enable_2fa",
            "title": "Enable Two-Factor Authentication",
            "description": "Go to Sign-In and Security → Two-Factor Authentication. This is highly recommended for your Apple ID.",
            "help_url": "https://appleid.apple.com/account/manage/security/twofactor",
            "sort_order": 2,
        },
        {
            "task_key": "revoke_sessions",
            "title": "Review trusted devices",
            "description": "Go to Devices section. Remove any devices you don't recognize from your Apple ID.",
            "help_url": "https://appleid.apple.com/account/manage/devices",
            "sort_order": 3,
        },
        {
            "task_key": "review_app_access",
            "title": "Check Sign in with Apple apps",
            "description": "Go to Sign-In and Security → Apps Using Apple ID. Revoke access for apps you no longer use.",
            "help_url": "https://appleid.apple.com/account/manage/security/appspecific",
            "sort_order": 4,
        },
    ],

    "github": [
        {
            "task_key": "change_password",
            "title": "Change your GitHub password",
            "description": "Go to Settings → Password and authentication → Change password. Use a strong, unique password.",
            "help_url": "https://github.com/settings/security",
            "sort_order": 1,
        },
        {
            "task_key": "enable_2fa",
            "title": "Enable Two-Factor Authentication",
            "description": "Go to Settings → Password and authentication → Two-factor authentication. Use a TOTP app or security key.",
            "help_url": "https://github.com/settings/two_factor_authentication/setup/intro",
            "sort_order": 2,
        },
        {
            "task_key": "revoke_sessions",
            "title": "Review active sessions",
            "description": "Go to Settings → Sessions. Revoke any sessions from unfamiliar locations or devices.",
            "help_url": "https://github.com/settings/sessions",
            "sort_order": 3,
        },
        {
            "task_key": "review_ssh_keys",
            "title": "Audit SSH & GPG keys",
            "description": "Go to Settings → SSH and GPG keys. Remove any keys you didn't add or no longer use.",
            "help_url": "https://github.com/settings/keys",
            "sort_order": 4,
        },
        {
            "task_key": "review_app_access",
            "title": "Review authorized OAuth apps",
            "description": "Go to Settings → Applications → Authorized OAuth Apps. Revoke access for apps you don't trust.",
            "help_url": "https://github.com/settings/applications",
            "sort_order": 5,
        },
        {
            "task_key": "review_pat",
            "title": "Rotate personal access tokens",
            "description": "Go to Settings → Developer settings → Personal access tokens. Delete old tokens and create new ones if needed.",
            "help_url": "https://github.com/settings/tokens",
            "sort_order": 6,
        },
    ],

    "banking": [
        {
            "task_key": "change_password",
            "title": "Change your online banking password",
            "description": "Log into your bank's website or app. Go to Security Settings and change your password immediately. Use a unique, strong password.",
            "help_url": None,
            "sort_order": 1,
        },
        {
            "task_key": "enable_2fa",
            "title": "Enable Two-Factor Authentication",
            "description": "Most banks support SMS or app-based 2FA. Enable it in your security settings. Contact your bank if you can't find the option.",
            "help_url": None,
            "sort_order": 2,
        },
        {
            "task_key": "review_transactions",
            "title": "Review recent transactions",
            "description": "Check your transaction history for any unauthorized charges. Report any suspicious activity to your bank immediately.",
            "help_url": None,
            "sort_order": 3,
        },
        {
            "task_key": "update_contact",
            "title": "Verify contact information",
            "description": "Make sure your email, phone number, and mailing address are correct on your bank account. Attackers may change these to intercept alerts.",
            "help_url": None,
            "sort_order": 4,
        },
        {
            "task_key": "freeze_credit",
            "title": "Consider a credit freeze",
            "description": "If financial data was exposed, consider placing a credit freeze with major bureaus (Equifax, Experian, TransUnion) to prevent new accounts from being opened in your name.",
            "help_url": None,
            "sort_order": 5,
        },
    ],
}


def get_recovery_template(platform: str) -> List[dict]:
    """Get the recovery task template for a given platform.
    Returns empty list if platform is unknown.
    """
    return RECOVERY_TEMPLATES.get(platform.lower(), [])


def get_supported_platforms() -> List[str]:
    """Return all platform keys that have recovery templates."""
    return list(RECOVERY_TEMPLATES.keys())
