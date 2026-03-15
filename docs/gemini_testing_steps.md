# Gemini API Integration Testing Guide

This document outlines the steps to verify the Gemini API integration and the dynamic AI provider switching capabilities from the Django Admin Panel. The implementation allows swapping between OpenRouter and Gemini and handles automatic key rotation for Gemini (rotating every minute).

## Prerequisites
1. Ensure your Django environment is set up.
2. The implementation uses `httpx` for making API requests to Gemini (which should already be installed).
3. Apply migrations to create the new `AISettings` table for the admin panel controls:
   ```bash
   python manage.py makemigrations automations
   python manage.py migrate
   ```

## Step 1: Configure AI Provider via Admin Panel
1. Start the Django development server: `python manage.py runserver`
    - Also start your celery worker: `celery -A core worker -l info`
2. Open the Django Admin Panel in your browser (e.g., `http://localhost:8000/admin`).
3. Under the **Automations** section, locate **AI Settings** and click "Add".
4. Set **Provider** to `Gemini Flash Free`.
5. In the **Gemini api keys** field, enter your Gemini API keys separated by commas (e.g., `YOUR_KEY_1, YOUR_KEY_2, YOUR_KEY_3`).
6. Click **Save**.

## Step 2: Set Up a Test Automation
1. Still in the Admin Panel, navigate to **Automations**.
2. Select an existing automation or create a new one.
3. Ensure **Use ai enhancement** is checked.
4. Provide an **Ai context** (e.g., "We are a fitness brand offering workout tips").
5. Save the automation.

## Step 3: Trigger the Automation
1. Trigger a comment on the target Instagram post (or simulate it).
2. The system should pick up the comment and queue the task `process_automation_trigger_async`.
3. Check your **Celery worker logs**. You should see logs indicating:
   - `[GeminiKeyPool] Initialized with X API key(s).`
   - `Trying Gemini model: Gemini 1.5 Flash`
   - `✓ Success with Gemini 1.5 Flash`

## Step 4: Verify Key Rotation & Rate Limiting (Every 1 Minute)
The `GeminiKeyPool` is designed to rotate keys every 60 seconds and cap at 15 requests per minute per key.
1. Send multiple DM triggers over a few minutes.
2. In the Celery logs, observe the key rotation messages:
   - `[GeminiKeyPool] Rotated to key index X (key: ...<last6chars>)`
   - You will see the index incrementing every 60 seconds as the rotation window hits.
   - If you send more than 15 requests within 60 seconds on a single key, it will automatically skip to the next available key.
   - If all keys are maxed out, it will log: `[GeminiKeyPool] All keys at capacity. Waiting 2s before retry...`

## Step 5: Switch Back to OpenRouter
1. Go back to the **AI Settings** in the Admin panel.
2. Change the **Provider** to `OpenRouter`.
3. (Optional) Provide your OpenRouter API keys in the specific field if you want to override the ones in `settings.py`.
4. Save the changes.
5. Trigger another automation and observe the logs. It should now output logs indicating the use of `OpenRouter` instead without needing a server restart.

## Troubleshooting
- **Missing `AISettings` table**: Make sure you successfully applied migrations.
- **API Errors (`401/403`)**: Ensure your Gemini API keys are valid and active.
- **Worker not picking up new provider**: If the celery worker doesn't immediately use the new provider, ensure the worker is pulling from the database properly instead of holding cached states. The implementation fetches `AISettings.load()` per-request, so it should be dynamic.
