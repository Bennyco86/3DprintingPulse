# Publishing Setup Checklist

## Facebook Page (Quality3Ds)
Provide or create:
- Facebook App ID and App Secret
- Page ID for https://www.facebook.com/Quality3Ds
- Long-lived Page Access Token
- Confirm permissions granted: pages_manage_posts, pages_read_engagement

Notes:
- Posting requires the Facebook Graph API.
- Tokens must be kept secure (do not commit to repo).

## GoDaddy Website Builder
Please confirm which publishing method is available:
- API access (unlikely for Website Builder)
- RSS import capability
- HTML embed widget
- Manual posting only

If none are supported, options are:
- Switch to a platform with a public API (e.g., WordPress)
- Export to static HTML and deploy to a host that supports SFTP or Git-based deploys

## Local Scheduler (Windows Task Scheduler)
- Command: powershell.exe -ExecutionPolicy Bypass -File "D:\Software\AI_Projects\Quality3Ds\run_daily.ps1"
- Start in: D:\Software\AI_Projects\Quality3Ds
- Trigger: daily at your preferred time
