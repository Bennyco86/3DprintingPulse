# Project Status: Quality3Ds Auto-Publisher (3DprintingPulse)

**Last Updated:** Wednesday, 14 January 2026
**Agent:** Codex CLI

## Purpose
The goal of this project is to automate the daily curation and publishing of 3D printing news ("Quality3Ds Daily Pulse") to:
1. **Facebook Page:** [Quality3Ds](https://www.facebook.com/Quality3Ds)
2. **Website:** GoDaddy Website Builder (integration method TBD)

The system is intended to run daily via Windows Task Scheduler, generating a summary of news (focused on Medical, Aerospace, Construction, and key industry players like Bambu Lab) and publishing it automatically.

## Current State
- **File Structure:** Files have been reorganized into the 3DprintingPulse folder.
- **Content Generation:** A basic PowerShell script (`run_daily.ps1`) exists to generate a markdown template.
- **Integration:**
  - **Facebook:** Access setup is in progress. The user needs to acquire:
    - App ID
    - App Secret
    - Page ID
    - Long-lived Page Access Token
  - **Website:** Not yet started.

## Facebook Access (How to Grant Codex Publishing Access)
1. **Verify Page Access:** Your Facebook user must have Full control (admin) for the Quality3Ds Page in Meta Business Suite.
2. **Create a Meta App:** On [Meta for Developers](https://developers.facebook.com/), create a Business app and add **Facebook Login** and **Pages API**.
3. **Request Permissions:** In App Review > Permissions and Features, enable:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `pages_show_list`
4. **Generate a User Token:** Use the Graph API Explorer to create a User Access Token with those scopes.
5. **Exchange for Long-Lived User Token:** Convert the short-lived token to a long-lived token.
6. **Get the Page Token:** Call `/me/accounts` to retrieve:
   - Page ID
   - Page Access Token (long-lived)
7. **Store Secrets Locally:** Save the credentials in `.env` or your OS secret store (do not commit):
   - `FB_APP_ID`
   - `FB_APP_SECRET`
   - `FB_PAGE_ID`
   - `FB_PAGE_ACCESS_TOKEN`
8. **Keep Tokens Current:** Long-lived tokens expire; repeat steps 4-6 before expiration.

## Immediate Next Steps (To Resume)
1. **Complete Facebook Credentials Setup** using the checklist above.
2. **Develop Publishing Script** that reads the daily content and posts it to the Facebook Page using the stored credentials.
3. **Website Integration**: Determine the best method to post to the GoDaddy site (RSS, API, or alternative).

## Context for Future Agent
- The user was guided through the "Phase 1" to "Phase 4" steps of getting Facebook credentials but had not yet completed them.
- A screenshot named "developer.facebook.com i dont see what you say.jpg" indicates previous difficulty navigating the Facebook Developer portal.
- The Expense Claims folder in the parent directory is unrelated and should be ignored.
