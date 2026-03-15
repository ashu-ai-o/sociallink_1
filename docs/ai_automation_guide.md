# AI Automation Features Guide

This guide explains how AI-powered features integrate with Instagram automations in SocialLink (DmMe), specifically focusing on AI DM Personalization and Public Comment Replies.

## Overview

SocialLink utilizes AI to transform static automated responses into personalized, engaging conversations. By leveraging the **OpenRouter** API gateway, the platform can access state-of-the-art models like Claude 3.5 Sonnet and GPT-4 to tailor messages based on user behavior and brand context.

---

## 1. AI DM Personalization

AI DM Personalization (also known as "AI Enhancement") allows the system to rewrite a base message template into a unique response for every user.

### How it Works
1. **Trigger**: An Instagram comment or DM keyword matches an active automation.
2. **Context Gathering**: The system collects:
   - The **Base Message** defined in the automation.
   - The **Business Context** (`ai_context`) provided by the user.
   - The **Follower's Comment** text.
   - The **Follower's Username**.
3. **AI Processing**: A request is sent to OpenRouter with a specialized prompt that instructs the AI to be "friendly, conversational, and personalized."
4. **Fallback Chain**: If the primary model (Claude 3.5 Sonnet) fails, the system automatically tries Claude 3 Haiku, then GPT-4, ensuring high reliability.
5. **Delivery**: The personalized message is sent as a private reply to the user.

### Configuration
Users can enable this via the **"Use AI Enhancement"** toggle in the Automation wizard.
- **AI Context**: This is the most critical field. It should describe your brand voice, goals, and any specific rules (e.g., "We are a premium coffee brand. Be helpful but don't offer discounts unless requested.").

---

## 2. Public Comment Replies

Public comment replies are the messages sent directly on the Instagram post for everyone to see.

### Current Implementation
- **Status**: Static / Templated.
- **Logic**: The system sends the `comment_reply_message` exactly as typed in settings.
- **Personalization**: Supports variable replacement like `{username}`.
- **Example**: "✅ Sent! Check your DMs for the link, {username}!"

### Future AI Expansion
While currently static, the infrastructure is in place to extend AI enhancement to public comments as well, allowing for unique public replies that acknowledge the user's specific sentiment (e.g., "Love that you liked the recipe! Sent you the ingredients list 🧑‍🍳").

---


## 3. Technical Infrastructure

### Core Components
- **`AIServiceOpenRouter`**: The backend service handling all AI requests.
- **Celery Workers**: Background tasks that execute the AI logic asynchronously to prevent latency in webhook responses.
- **OpenRouter Gateway**: Provides access to multiple LLM providers with a single API key and consolidated billing.

### Analytics & ROI
The platform tracks AI usage to provide insights into engagement:
- **AI Enhancement Rate**: Percentage of automations where AI was used.
- **Model Usage**: Breakdown of which models were used for delivery.
- **Cost Tracking**: Estimated cost per AI request for ROI calculation.

---

## 4. Best Practices for AI Context
To get the best results from the AI:
- **Be Specific**: Instead of "Be nice," say "Adopt a professional yet enthusiastic tone typical of a fitness coach."
- **Define Goals**: "Your main goal is to get the user to click the link in the message."
- **Set Boundaries**: "Never mention competitor brands and never guarantee delivery times."
