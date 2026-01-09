export interface User {
  id: string;
  email: string;
  username: string;
  plan: 'free' | 'pro' | 'enterprise';
  subscription_end_date?: string;
  created_at: string;
}

export interface InstagramAccount {
  id: string;
  username: string;
  instagram_user_id: string;
  profile_picture_url: string;
  followers_count: number;
  is_active: boolean;
  last_synced: string;
  created_at: string;
}

export interface Automation {
  id: string;
  instagram_account: string;
  name: string;
  trigger_type: 'comment' | 'story_mention' | 'story_reply' | 'dm_keyword';
  trigger_keywords: string[];
  trigger_match_type: 'exact' | 'contains' | 'any';
  target_posts: string[];
  dm_message: string;
  dm_buttons: Array<{ text: string; url: string }>;
  enable_comment_reply: boolean;
  comment_reply_message: string;
  require_follow: boolean;
  follow_check_message: string;
  use_ai_enhancement: boolean;
  ai_context: string;
  max_triggers_per_user: number;
  cooldown_minutes: number;
  is_active: boolean;
  priority: number;
  total_triggers: number;
  total_dms_sent: number;
  total_comment_replies: number;
  created_at: string;
  updated_at: string;
}

export interface AutomationTrigger {
  id: string;
  automation: string;
  instagram_user_id: string;
  instagram_username: string;
  post_id?: string;
  comment_id?: string;
  comment_text: string;
  status: 'pending' | 'processing' | 'sent' | 'failed' | 'skipped';
  failure_reason?: string;
  dm_sent_at?: string;
  dm_message_sent: string;
  comment_reply_sent: boolean;
  comment_reply_text: string;
  was_ai_enhanced: boolean;
  ai_modifications?: string;
  created_at: string;
}

export interface Contact {
  id: string;
  instagram_account: string;
  instagram_user_id: string;
  instagram_username: string;
  full_name: string;
  profile_picture_url: string;
  total_interactions: number;
  total_dms_received: number;
  first_interaction: string;
  last_interaction: string;
  tags: string[];
  custom_fields: Record<string, any>;
  is_follower: boolean;
  is_blocked: boolean;
}

export interface DashboardStats {
  total_automations: number;
  active_automations: number;
  total_dms_sent: number;
  total_triggers: number;
  today_triggers: number;
  success_rate: number;
  ai_enhancement_rate: number;
  daily_breakdown: Array<{
    date: string;
    triggers: number;
    dms_sent: number;
    ai_enhanced: number;
  }>;
}


