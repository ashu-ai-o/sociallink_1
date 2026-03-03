// ============================================================================
// Edit Automation PAGE - Step-by-step wizard with post targeting
// ============================================================================

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Plus,
  X,
  Image,
  Loader2,
  ImageOff,
  Info,
  Instagram,
} from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../../hooks';
import { updateAutomation } from '../../store/slices/automationsSlice';
import { api } from '../../utils/api';
import toast from 'react-hot-toast';

interface Post {
  id: string;
  caption: string;
  media_type: string;
  thumbnail_url: string;
  timestamp: string;
  permalink: string;
}

export const EditAutomationPage = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { id } = useParams<{ id: string }>();
  const automation = useAppSelector((state) =>
    state.automations.items.find((a: any) => a.id === id)
  );

  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  // Fetch connected accounts from API (as fallback when automation.instagram_account is not set)
  const [igAccounts, setIgAccounts] = useState<any[]>([]);
  const [checkingAccounts, setCheckingAccounts] = useState(true);

  useEffect(() => {
    setCheckingAccounts(true);
    api.getInstagramAccounts().then((data: any) => {
      const allAccounts = Array.isArray(data) ? data : (data.results || []);
      setIgAccounts(allAccounts.filter((acc: any) => acc.is_active !== false));
    }).catch(console.error)
      .finally(() => setCheckingAccounts(false));
  }, []);

  // Post picker state
  const [posts, setPosts] = useState<Post[]>([]);
  const [postsLoading, setPostsLoading] = useState(false);
  const [postsError, setPostsError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    name: automation?.name || '',
    trigger_keywords: automation?.trigger_keywords?.length ? automation.trigger_keywords : [''],
    trigger_match_type: automation?.trigger_match_type || 'contains',
    target_posts: (automation as any)?.target_posts || [],
    enable_comment_reply: automation?.enable_comment_reply ?? true,
    comment_reply_message: automation?.comment_reply_message || '✅ Sent! Check your DM',
    DmMessage: automation?.DmMessage || '',
    dm_buttons: automation?.dm_buttons?.length ? automation.dm_buttons : [{ text: '', url: '' }],
    use_ai_enhancement: automation?.use_ai_enhancement || false,
    ai_context: automation?.ai_context || '',
  });

  // Fetch posts when we enter step 2
  useEffect(() => {
    if (step === 2) {
      // Prefer the account from the automation; fall back to the first connected account
      const accountId = (automation as any)?.instagram_account || igAccounts[0]?.id;
      if (accountId) fetchPosts(accountId);
    }
  }, [step, automation, igAccounts]);


  const fetchPosts = async (accountId: string) => {
    setPostsLoading(true);
    setPostsError(null);
    try {
      const data = await api.getInstagramPosts(accountId);
      setPosts(data.posts || []);
    } catch {
      setPostsError('Could not load posts. You can still save — current post targeting is preserved.');
    } finally {
      setPostsLoading(false);
    }
  };

  const togglePost = (postId: string) => {
    setFormData((f) => ({
      ...f,
      target_posts: f.target_posts.includes(postId)
        ? f.target_posts.filter((pid: string) => pid !== postId)
        : [...f.target_posts, postId],
    }));
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      await dispatch(
        updateAutomation({
          id: id!,
          data: {
            ...formData,
            trigger_keywords: formData.trigger_keywords.filter((k) => k.trim()),
            dm_buttons: formData.dm_buttons.filter((b: any) => b.text && b.url),
            trigger_type: 'comment',
          },
        })
      ).unwrap();

      toast.success('Automation updated successfully');
      navigate('/automations');
    } catch (error: any) {
      const msg =
        typeof error === 'string'
          ? error
          : error?.message || error?.response?.data?.detail || 'Failed to edit automation';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    { number: 1, title: 'Name & Triggers' },
    { number: 2, title: 'Target Posts' },
    { number: 3, title: 'Comment Reply' },
    { number: 4, title: 'DM Message' },
    { number: 5, title: 'Review' },
  ];

  const canProgress = () => {
    switch (step) {
      case 1:
        return formData.name.trim() && formData.trigger_keywords.some((k) => k.trim());
      case 2:
        return true;
      case 3:
        return !formData.enable_comment_reply || formData.comment_reply_message.trim();
      case 4:
        return formData.DmMessage.trim();
      default:
        return true;
    }
  };

  return (
    <div className="max-w-3xl mx-auto animate-fade-in">
      {/* Header */}
      <button
        onClick={() => navigate('/automations')}
        className="inline-flex items-center gap-2 text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition-colors mb-8 group"
      >
        <ArrowLeft className="w-4 h-4 transition-transform group-hover:-translate-x-1" />
        <span className="font-medium">Back to Automations</span>
      </button>

      <div className="mb-8">
        <h1 className="text-3xl font-semibold text-neutral-900 dark:text-white mb-2">Edit Automation</h1>
        <p className="text-neutral-600 dark:text-neutral-400">
          Update settings for your automated responses to Instagram comments
        </p>
      </div>

      {checkingAccounts ? (
        <div className="bg-white dark:bg-neutral-900 rounded-2xl p-12 border border-neutral-200 dark:border-neutral-800 flex flex-col items-center justify-center text-center">
          <Loader2 className="w-12 h-12 text-purple-600 animate-spin mb-4" />
          <h3 className="text-lg font-medium text-neutral-900 dark:text-white mb-1">Checking your accounts</h3>
          <p className="text-neutral-500 dark:text-neutral-400">Please wait a moment...</p>
        </div>
      ) : igAccounts.length === 0 ? (
        <div className="bg-white dark:bg-neutral-900 rounded-2xl p-12 border border-neutral-200 dark:border-neutral-800 flex flex-col items-center justify-center text-center animate-scale-in">
          <div className="w-20 h-20 rounded-full bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center mb-6">
            <Instagram className="w-10 h-10 text-neutral-400" />
          </div>
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-white mb-3">No Instagram Account Connected</h2>
          <p className="text-neutral-600 dark:text-neutral-400 mb-8 max-w-sm">
            The account associated with this automation is no longer connected. Please reconnect in settings to manage your automations.
          </p>
          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={() => navigate('/settings')}
              className="px-6 py-3 bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 rounded-xl font-medium hover:bg-neutral-800 dark:hover:bg-neutral-100 transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              Connect an Account
            </button>
            <button
              onClick={() => navigate('/automations')}
              className="px-6 py-3 bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 rounded-xl font-medium hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-all"
            >
              Go Back
            </button>
          </div>
        </div>
      ) : (
        <>
          {/* Progress Steps */}
          <div className="flex items-center justify-between mb-8 overflow-x-auto pb-2">
            {steps.map((s, i) => (
              <div key={s.number} className="flex items-center flex-1 min-w-0">
                <div className="flex flex-col items-center flex-1">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-medium text-sm transition-all flex-shrink-0 ${step > s.number
                      ? 'bg-neutral-900 dark:bg-white text-white dark:text-neutral-900'
                      : step === s.number
                        ? 'bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 ring-4 ring-neutral-200 dark:ring-neutral-800'
                        : 'bg-neutral-200 dark:bg-neutral-800 text-neutral-500 dark:text-neutral-500'
                      }`}
                  >
                    {step > s.number ? <Check className="w-5 h-5" /> : s.number}
                  </div>
                  <div className="text-xs font-medium text-neutral-600 dark:text-neutral-400 mt-2 text-center hidden sm:block whitespace-nowrap">
                    {s.title}
                  </div>
                </div>
                {i < steps.length - 1 && (
                  <div
                    className={`h-0.5 flex-1 mx-2 transition-colors ${step > s.number ? 'bg-neutral-900 dark:bg-white' : 'bg-neutral-200 dark:bg-neutral-800'
                      }`}
                  />
                )}
              </div>
            ))}
          </div>

          {/* Form Card */}
          <div className="bg-white dark:bg-neutral-900 rounded-2xl p-8 border border-neutral-200 dark:border-neutral-800 mb-8">
            {step === 1 && <Step1 formData={formData} setFormData={setFormData} />}
            {step === 2 && (
              <Step2
                formData={formData}
                posts={posts}
                postsLoading={postsLoading}
                postsError={postsError}
                onToggle={togglePost}
              />
            )}
            {step === 3 && <Step3 formData={formData} setFormData={setFormData} />}
            {step === 4 && <Step4 formData={formData} setFormData={setFormData} />}
            {step === 5 && <Step5 formData={formData} posts={posts} />}
          </div>

          {/* Navigation */}
          <div className="flex items-center justify-between">
            <button
              onClick={() => setStep(Math.max(1, step - 1))}
              disabled={step === 1}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 rounded-lg font-medium hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ArrowLeft className="w-4 h-4" />
              Previous
            </button>

            {step < 5 ? (
              <button
                onClick={() => setStep(Math.min(5, step + 1))}
                disabled={!canProgress()}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 rounded-lg font-medium hover:bg-neutral-800 dark:hover:bg-neutral-100 transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:scale-[1.02] active:scale-[0.98]"
              >
                Next Step
                <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="inline-flex items-center gap-2 px-6 py-3 bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 rounded-lg font-medium hover:bg-neutral-800 dark:hover:bg-neutral-100 transition-all disabled:opacity-50 hover:scale-[1.02] active:scale-[0.98]"
              >
                {loading ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> Saving...</>
                ) : (
                  <><Check className="w-5 h-5" /> Save Changes</>
                )}
              </button>
            )}
          </div>
        </>
      )}
    </div>
  );
};

// ─── Step 1: Name & Triggers ─────────────────────────────────────────────────
const Step1 = ({ formData, setFormData }: any) => (
  <div className="space-y-6">
    <div>
      <h2 className="text-2xl font-semibold text-neutral-900 dark:text-white mb-2">Name & Triggers</h2>
      <p className="text-neutral-600 dark:text-neutral-400">Give your automation a name and set trigger keywords</p>
    </div>

    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Automation Name</label>
        <input
          type="text"
          className="w-full px-4 py-3 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 dark:focus:ring-white transition-all"
          placeholder="e.g., Product Link Bot"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Trigger Keywords</label>
        <div className="space-y-2">
          {formData.trigger_keywords.map((keyword: string, i: number) => (
            <div key={i} className="flex gap-2">
              <input
                type="text"
                className="flex-1 px-4 py-2.5 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-lg text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 dark:focus:ring-white transition-all"
                placeholder={i === 0 ? 'e.g., link please' : 'Add another keyword...'}
                value={keyword}
                onChange={(e) => {
                  const newKeywords = [...formData.trigger_keywords];
                  newKeywords[i] = e.target.value;
                  setFormData({ ...formData, trigger_keywords: newKeywords });
                }}
              />
              {i === formData.trigger_keywords.length - 1 && (
                <button
                  onClick={() =>
                    setFormData({ ...formData, trigger_keywords: [...formData.trigger_keywords, ''] })
                  }
                  className="px-3 py-2.5 bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                </button>
              )}
              {formData.trigger_keywords.length > 1 && (
                <button
                  onClick={() => {
                    const newKeywords = formData.trigger_keywords.filter(
                      (_: string, idx: number) => idx !== i
                    );
                    setFormData({ ...formData, trigger_keywords: newKeywords });
                  }}
                  className="px-3 py-2.5 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Match Type</label>
        <select
          className="w-full px-4 py-3 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-neutral-900 dark:focus:ring-white transition-all"
          value={formData.trigger_match_type}
          onChange={(e) => setFormData({ ...formData, trigger_match_type: e.target.value })}
        >
          <option value="contains">Contains keyword (Recommended)</option>
          <option value="exact">Exact match only</option>
          <option value="any">Any comment</option>
        </select>
      </div>
    </div>
  </div>
);

// ─── Step 2: Target Posts ─────────────────────────────────────────────────────
const Step2 = ({ formData, posts, postsLoading, postsError, onToggle }: any) => (
  <div className="space-y-6">
    <div>
      <h2 className="text-2xl font-semibold text-neutral-900 dark:text-white mb-2">Target Posts</h2>
      <p className="text-neutral-600 dark:text-neutral-400">
        Choose which posts this automation applies to. Leave all unselected to trigger on <strong>any</strong> post.
      </p>
    </div>

    <div className="flex items-start gap-3 p-4 bg-blue-50 dark:bg-blue-950/30 rounded-xl border border-blue-200 dark:border-blue-900">
      <Info className="w-4 h-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
      <p className="text-sm text-blue-800 dark:text-blue-200">
        {formData.target_posts.length === 0
          ? 'No posts selected — automation will trigger on ALL posts.'
          : `${formData.target_posts.length} post${formData.target_posts.length > 1 ? 's' : ''} selected — automation will only trigger on these posts.`}
      </p>
    </div>

    {postsLoading && (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-neutral-400" />
        <span className="ml-3 text-neutral-500 dark:text-neutral-400">Loading your posts…</span>
      </div>
    )}

    {postsError && (
      <div className="flex items-start gap-3 p-4 bg-amber-50 dark:bg-amber-950/30 rounded-xl border border-amber-200 dark:border-amber-900">
        <ImageOff className="w-4 h-4 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
        <p className="text-sm text-amber-800 dark:text-amber-200">{postsError}</p>
      </div>
    )}

    {!postsLoading && !postsError && posts.length === 0 && (
      <div className="text-center py-12 text-neutral-500 dark:text-neutral-400">
        <Image className="w-12 h-12 mx-auto mb-3 opacity-30" />
        <p>No posts found on this account.</p>
      </div>
    )}

    {!postsLoading && posts.length > 0 && (
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {posts.map((post: Post) => {
          const selected = formData.target_posts.includes(post.id);
          return (
            <button
              key={post.id}
              type="button"
              onClick={() => onToggle(post.id)}
              className={`relative group rounded-xl overflow-hidden border-2 transition-all text-left ${selected
                ? 'border-purple-500 dark:border-purple-400 ring-2 ring-purple-500/30'
                : 'border-neutral-200 dark:border-neutral-700 hover:border-neutral-400 dark:hover:border-neutral-500'
                }`}
            >
              <div className="aspect-square bg-neutral-100 dark:bg-neutral-800 relative">
                {post.thumbnail_url ? (
                  <img
                    src={post.thumbnail_url}
                    alt={post.caption || 'Post'}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <Image className="w-8 h-8 text-neutral-400" />
                  </div>
                )}
                {selected && (
                  <div className="absolute inset-0 bg-purple-600/20 flex items-center justify-center">
                    <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center shadow-lg">
                      <Check className="w-4 h-4 text-white" />
                    </div>
                  </div>
                )}
              </div>
              <div className="p-2">
                <p className="text-xs text-neutral-600 dark:text-neutral-400 line-clamp-2">
                  {post.caption || <span className="italic text-neutral-400">No caption</span>}
                </p>
              </div>
            </button>
          );
        })}
      </div>
    )}
  </div>
);

// ─── Step 3: Comment Reply ────────────────────────────────────────────────────
const Step3 = ({ formData, setFormData }: any) => (
  <div className="space-y-6">
    <div>
      <h2 className="text-2xl font-semibold text-neutral-900 dark:text-white mb-2">Public Comment Reply</h2>
      <p className="text-neutral-600 dark:text-neutral-400">Respond publicly to let users know you received their comment</p>
    </div>

    <div className="bg-blue-50 dark:bg-blue-950/30 rounded-xl p-4 border border-blue-200 dark:border-blue-900">
      <p className="text-sm text-blue-900 dark:text-blue-100">This reply is visible to everyone. Keep it professional and friendly!</p>
    </div>

    <div className="space-y-4">
      <label className="flex items-center gap-3 cursor-pointer">
        <input
          type="checkbox"
          checked={formData.enable_comment_reply}
          onChange={(e) => setFormData({ ...formData, enable_comment_reply: e.target.checked })}
          className="w-5 h-5 rounded border-neutral-300 dark:border-neutral-700"
        />
        <span className="text-sm font-medium text-neutral-900 dark:text-white">Enable public comment reply</span>
      </label>

      {formData.enable_comment_reply && (
        <div>
          <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Reply Message</label>
          <input
            type="text"
            className="w-full px-4 py-3 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 dark:focus:ring-white transition-all"
            placeholder="e.g., ✅ Sent! Check your DM"
            value={formData.comment_reply_message}
            onChange={(e) => setFormData({ ...formData, comment_reply_message: e.target.value })}
          />
        </div>
      )}
    </div>
  </div>
  </div>
);

// ─── Step 4: DM Message ───────────────────────────────────────────────────────
const Step4 = ({ formData, setFormData }: any) => (
  <div className="space-y-6">
    <div>
      <h2 className="text-2xl font-semibold text-neutral-900 dark:text-white mb-2">Direct Message</h2>
      <p className="text-neutral-600 dark:text-neutral-400">Craft the private message that will be sent automatically</p>
    </div>

    <div>
      <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Message Content</label>
      <textarea
        rows={6}
        className="w-full px-4 py-3 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 dark:focus:ring-white transition-all resize-none"
        placeholder="Hey! Thanks for your interest. Here's the link you requested..."
        value={formData.DmMessage}
        onChange={(e) => setFormData({ ...formData, DmMessage: e.target.value })}
      />
    </div>

    <div>
      <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Optional: Add Button</label>
      <div className="space-y-2">
        {formData.dm_buttons.map((button: any, i: number) => (
          <div key={i} className="grid grid-cols-2 gap-2">
            <input
              type="text"
              className="px-4 py-2.5 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-lg text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 dark:focus:ring-white transition-all"
              placeholder="Button text"
              value={button.text}
              onChange={(e) => {
                const newButtons = [...formData.dm_buttons];
                newButtons[i] = { ...newButtons[i], text: e.target.value };
                setFormData({ ...formData, dm_buttons: newButtons });
              }}
            />
            <input
              type="url"
              className="px-4 py-2.5 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-lg text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 dark:focus:ring-white transition-all"
              placeholder="https://..."
              value={button.url}
              onChange={(e) => {
                const newButtons = [...formData.dm_buttons];
                newButtons[i] = { ...newButtons[i], url: e.target.value };
                setFormData({ ...formData, dm_buttons: newButtons });
              }}
            />
          </div>
        ))}
      </div>
    </div>
  </div>
);

// ─── Step 5: Review ───────────────────────────────────────────────────────────
const Step5 = ({ formData, posts }: any) => {
  const selectedPosts = posts.filter((p: Post) => formData.target_posts.includes(p.id));

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-neutral-900 dark:text-white mb-2">Review & Update</h2>
        <p className="text-neutral-600 dark:text-neutral-400">Review your automation settings before saving changes</p>
      </div>

      <div className="space-y-4">
        <div className="p-4 bg-neutral-50 dark:bg-neutral-800/50 rounded-xl">
          <div className="text-sm font-medium text-neutral-500 mb-1">Name</div>
          <div className="text-neutral-900 dark:text-white">{formData.name}</div>
        </div>

        <div className="p-4 bg-neutral-50 dark:bg-neutral-800/50 rounded-xl">
          <div className="text-sm font-medium text-neutral-500 mb-2">Trigger Keywords</div>
          <div className="flex flex-wrap gap-2">
            {formData.trigger_keywords.filter((k: string) => k.trim()).map((keyword: string, i: number) => (
              <span key={i} className="px-3 py-1 bg-neutral-200 dark:bg-neutral-700 text-neutral-900 dark:text-white rounded-full text-sm">
                {keyword}
              </span>
            ))}
          </div>
        </div>

        <div className="p-4 bg-neutral-50 dark:bg-neutral-800/50 rounded-xl">
          <div className="text-sm font-medium text-neutral-500 mb-2">Target Posts</div>
          {selectedPosts.length === 0 ? (
            <p className="text-sm text-neutral-600 dark:text-neutral-400">
              {formData.target_posts.length === 0
                ? 'All posts (no specific post selected)'
                : `${formData.target_posts.length} post IDs saved (posts not loaded for preview)`}
            </p>
          ) : (
            <div className="flex gap-2 flex-wrap">
              {selectedPosts.map((p: Post) => (
                <div key={p.id} className="flex items-center gap-2 px-3 py-1.5 bg-purple-100 dark:bg-purple-900/30 rounded-lg text-sm text-purple-700 dark:text-purple-300">
                  {p.thumbnail_url && (
                    <img src={p.thumbnail_url} alt="" className="w-5 h-5 rounded object-cover" />
                  )}
                  <span className="truncate max-w-[120px]">{p.caption || 'Post'}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {formData.enable_comment_reply && (
          <div className="p-4 bg-neutral-50 dark:bg-neutral-800/50 rounded-xl">
            <div className="text-sm font-medium text-neutral-500 mb-1">Comment Reply</div>
            <div className="text-neutral-900 dark:text-white">{formData.comment_reply_message}</div>
          </div>
        )}

        <div className="p-4 bg-neutral-50 dark:bg-neutral-800/50 rounded-xl">
          <div className="text-sm font-medium text-neutral-500 mb-1">DM Message</div>
          <div className="text-neutral-900 dark:text-white whitespace-pre-wrap">{formData.DmMessage}</div>
        </div>
      </div>
    </div>
  );
};
