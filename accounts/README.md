# Accounts and the newsletter: switching them on

Everything is built and sits switched off until these are filled in.

1. **Domain.** Point it at the site, and set `accounts.site_url` in `config.json` to the new address.
2. **Account service (Supabase).** Create a project. In the SQL Editor, paste all of `accounts/setup.sql` and press Run.
   Under Authentication > URL Configuration, set the Site URL to the site address and add `<site address>/account/` as a redirect URL.
   Copy the Project URL and the public ("anon" / publishable) key into `accounts.supabase_url` and `accounts.supabase_key` in `config.json`.
   These two are meant to be public. The **service role key is secret**: it goes only in the GitHub secret `SUPABASE_SERVICE_KEY`.
3. **Mail service (Resend).** Verify the domain. Put the API key in the GitHub secret `RESEND_API_KEY`.
   In Supabase, Authentication > Emails > SMTP Settings, enter the Resend SMTP details so sign-in links come from the domain.
   Set `accounts.from` in `config.json`, for example `Floor Record <hello@yourdomain.com>`.
4. **Before the first sponsored email:** set `accounts.postal_address`. Sponsor text goes in `accounts.sponsor`.
5. **Reword the promise** on the About page and footer before switching on: the site will now keep email addresses.

Try an email without sending it:
`python -m floorrecord.newsletter --edition friday --dry out/ --rep M001184 --state KY`
