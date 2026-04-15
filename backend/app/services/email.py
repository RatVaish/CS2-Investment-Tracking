import random
import string
import httpx
from app.core.config import settings


def generate_otp() -> str:
    """Generate a 6-digit OTP code."""
    return ''.join(random.choices(string.digits, k=6))


def send_verification_email(to_email: str, code: str, username: str) -> bool:
    """Send a verification OTP email via Resend. Returns True on success."""
    if not settings.RESEND_API_KEY:
        print(f"[EMAIL] No RESEND_API_KEY set. OTP for {to_email}: {code}")
        return True  # Don't hard-fail in dev

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0;padding:0;background:#0a0f1a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0f1a;padding:40px 20px;">
        <tr>
          <td align="center">
            <table width="480" cellpadding="0" cellspacing="0" style="background:#111827;border:1px solid #1f2937;border-radius:16px;overflow:hidden;">
              <!-- Header -->
              <tr>
                <td style="padding:32px 40px 24px;border-bottom:1px solid #1f2937;">
                  <span style="font-size:22px;font-weight:700;color:#ffffff;letter-spacing:-0.5px;">Floatbase</span>
                </td>
              </tr>
              <!-- Body -->
              <tr>
                <td style="padding:32px 40px;">
                  <p style="margin:0 0 8px;font-size:13px;color:#6b7280;text-transform:uppercase;letter-spacing:1px;">Email Verification</p>
                  <h1 style="margin:0 0 16px;font-size:24px;font-weight:700;color:#ffffff;">Hi {username},</h1>
                  <p style="margin:0 0 28px;font-size:15px;color:#9ca3af;line-height:1.6;">
                    Use the code below to verify your email address. It expires in <strong style="color:#e5e7eb;">15 minutes</strong>.
                  </p>
                  <!-- OTP Code -->
                  <div style="background:#0a0f1a;border:1px solid #1f2937;border-radius:12px;padding:28px;text-align:center;margin-bottom:28px;">
                    <span style="font-size:40px;font-weight:800;letter-spacing:12px;color:#22d3ee;font-family:'Courier New',monospace;">{code}</span>
                  </div>
                  <p style="margin:0;font-size:13px;color:#4b5563;line-height:1.5;">
                    If you didn't request this, you can safely ignore this email.
                    Never share this code with anyone.
                  </p>
                </td>
              </tr>
              <!-- Footer -->
              <tr>
                <td style="padding:20px 40px;border-top:1px solid #1f2937;">
                  <p style="margin:0;font-size:12px;color:#374151;">
                    © 2026 Floatbase · <a href="https://floatbase.app" style="color:#6b7280;text-decoration:none;">floatbase.app</a>
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """

    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": settings.RESEND_FROM_EMAIL,
                "to": [to_email],
                "subject": f"{code} — Your Floatbase verification code",
                "html": html_body,
            },
            timeout=10,
        )
        return response.status_code == 200
    except Exception as e:
        print(f"[EMAIL] Failed to send to {to_email}: {e}")
        return False
