// ============================================================================
// CREATE AUTOMATION PAGE - Clean step-by-step wizard with ZapDM-inspired design
// ============================================================================

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Sparkles,
  MessageSquare,
  Plus,
  X,
  Zap,
  Send,
  Brain,
} from 'lucide-react';
import { useAppDispatch } from '../../hooks';
import { createAutomation } from '../../store/slices/automationsSlice';
import toast from 'react-hot-toast';

export const CreateAutomationPage = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    trigger_keywords: [''],
    trigger_match_type: 'contains' as 'exact' | 'contains' | 'any',
    enable_comment_reply: true,
    comment_reply_message: 'Sent! Check your DM',
    DmMessage: '',
    dm_buttons: [{ text: '', url: '' }],
    use_ai_enhancement: false,
    ai_context: '',
  });

  const handleSubmit = async () => {
    setLoading(true);
    try {
      await dispatch(
        createAutomation({
          ...formData,
          trigger_keywords: formData.trigger_keywords.filter((k) => k.trim()),
          dm_buttons: formData.dm_buttons.filter((b) => b.text && b.url),
          instagram_account: 'default',
          trigger_type: 'comment',
          target_posts: [],
        })
      ).unwrap();

      toast.success('Automation created successfully');
      navigate('/automations');
    } catch (error: any) {
      toast.error(error.message || 'Failed to create automation');
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    { number: 1, title: 'Name & Triggers' },
    { number: 2, title: 'Comment Reply' },
    { number: 3, title: 'DM Message' },
    { number: 4, title: 'Review' },
  ];

  const canProgress = () => {
    switch (step) {
      case 1:
        return formData.name.trim() && formData.trigger_keywords.some((k) => k.trim());
      case 2:
        return !formData.enable_comment_reply || formData.comment_reply_message.trim();
      case 3:
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
        <h1 className="text-3xl font-semibold text-neutral-900 dark:text-white mb-2">
          Create New Automation
        </h1>
        <p className="text-neutral-600 dark:text-neutral-400">
          Set up automated responses for Instagram comments
        </p>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center justify-between mb-8">
        {steps.map((s, i) => (
          <div key={s.number} className="flex items-center flex-1">
            <div className="flex flex-col items-center flex-1">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-medium text-sm transition-all ${
                  step > s.number
                    ? 'bg-neutral-900 dark:bg-white text-white dark:text-neutral-900'
                    : step === s.number
                    ? 'bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 ring-4 ring-neutral-200 dark:ring-neutral-800'
                    : 'bg-neutral-200 dark:bg-neutral-800 text-neutral-500 dark:text-neutral-500'
                }`}
              >
                {step > s.number ? <Check className="w-5 h-5" /> : s.number}
              </div>
              <div className="text-xs font-medium text-neutral-600 dark:text-neutral-400 mt-2 text-center hidden sm:block">
                {s.title}
              </div>
            </div>
            {i < steps.length - 1 && (
              <div
                className={`h-0.5 flex-1 mx-2 transition-colors ${
                  step > s.number
                    ? 'bg-neutral-900 dark:bg-white'
                    : 'bg-neutral-200 dark:bg-neutral-800'
                }`}
              ></div>
            )}
          </div>
        ))}
      </div>

      {/* Form Card */}
      <div className="bg-white dark:bg-neutral-900 rounded-2xl p-8 border border-neutral-200 dark:border-neutral-800 mb-8">
        {step === 1 && <Step1 formData={formData} setFormData={setFormData} />}
        {step === 2 && <Step2 formData={formData} setFormData={setFormData} />}
        {step === 3 && <Step3 formData={formData} setFormData={setFormData} />}
        {step === 4 && <Step4 formData={formData} />}
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

        {step < 4 ? (
          <button
            onClick={() => setStep(Math.min(4, step + 1))}
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
            className="inline-flex items-center gap-2 px-6 py-3 bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 rounded-lg font-medium hover:bg-neutral-800 dark:hover:bg-neutral-100 transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:scale-[1.02] active:scale-[0.98]"
          >
            {loading ? (
              <>Creating...</>
            ) : (
              <>
                <Check className="w-5 h-5" />
                Create Automation
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
};

// Step 1: Basic Info
const Step1 = ({ formData, setFormData }: any) => (
  <div className="space-y-6">
    <div>
      <h2 className="text-2xl font-semibold text-neutral-900 dark:text-white mb-2">
        Name & Triggers
      </h2>
      <p className="text-neutral-600 dark:text-neutral-400">
        Give your automation a name and set up keywords that will trigger it
      </p>
    </div>

    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
          Automation Name
        </label>
        <input
          type="text"
          className="w-full px-4 py-3 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 dark:focus:ring-white transition-all"
          placeholder="e.g., Product Link Bot"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
        />
        <p className="text-xs text-neutral-500 mt-2">
          Choose a descriptive name like "Product Link DMs" or "Discount Code Bot"
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
          Trigger Keywords
        </label>
        <p className="text-xs text-neutral-600 dark:text-neutral-400 mb-3">
          When someone comments with these keywords, your automation will activate
        </p>
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
                    setFormData({
                      ...formData,
                      trigger_keywords: [...formData.trigger_keywords, ''],
                    })
                  }
                  className="px-3 py-2.5 bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors"
                  title="Add keyword"
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
                  title="Remove"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          ))}
        </div>
        <p className="text-xs text-neutral-500 mt-2">
          Examples: "send link", "dm me", "interested", "link please"
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
          Match Type
        </label>
        <select
          className="w-full px-4 py-3 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-neutral-900 dark:focus:ring-white transition-all"
          value={formData.trigger_match_type}
          onChange={(e) =>
            setFormData({ ...formData, trigger_match_type: e.target.value })
          }
        >
          <option value="contains">Contains keyword (Recommended)</option>
          <option value="exact">Exact match only</option>
          <option value="any">Any comment</option>
        </select>
      </div>
    </div>
  </div>
);

// Step 2: Comment Reply
const Step2 = ({ formData, setFormData }: any) => (
  <div className="space-y-6">
    <div>
      <h2 className="text-2xl font-semibold text-neutral-900 dark:text-white mb-2">
        Public Comment Reply
      </h2>
      <p className="text-neutral-600 dark:text-neutral-400">
        Respond publicly to let users know you received their comment
      </p>
    </div>

    <div className="bg-blue-50 dark:bg-blue-950/30 rounded-xl p-4 border border-blue-200 dark:border-blue-900">
      <p className="text-sm text-blue-900 dark:text-blue-100">
        This reply is visible to everyone. Keep it professional and friendly!
      </p>
    </div>

    <div className="space-y-4">
      <label className="flex items-center gap-3 cursor-pointer">
        <input
          type="checkbox"
          checked={formData.enable_comment_reply}
          onChange={(e) =>
            setFormData({ ...formData, enable_comment_reply: e.target.checked })
          }
          className="w-5 h-5 rounded border-neutral-300 dark:border-neutral-700"
        />
        <span className="text-sm font-medium text-neutral-900 dark:text-white">
          Enable public comment reply
        </span>
      </label>

      {formData.enable_comment_reply && (
        <div>
          <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
            Reply Message
          </label>
          <input
            type="text"
            className="w-full px-4 py-3 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 dark:focus:ring-white transition-all"
            placeholder="e.g., Sent! Check your DM"
            value={formData.comment_reply_message}
            onChange={(e) =>
              setFormData({ ...formData, comment_reply_message: e.target.value })
            }
          />
          <p className="text-xs text-neutral-500 mt-2">
            Keep it short and friendly
          </p>
        </div>
      )}
    </div>
  </div>
);

// Step 3: DM Message
const Step3 = ({ formData, setFormData }: any) => (
  <div className="space-y-6">
    <div>
      <h2 className="text-2xl font-semibold text-neutral-900 dark:text-white mb-2">
        Direct Message
      </h2>
      <p className="text-neutral-600 dark:text-neutral-400">
        Craft the private message that will be sent automatically
      </p>
    </div>

    <div>
      <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
        Message Content
      </label>
      <textarea
        rows={6}
        className="w-full px-4 py-3 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 dark:focus:ring-white transition-all resize-none"
        placeholder="Hey! Thanks for your interest. Here's the link you requested..."
        value={formData.DmMessage}
        onChange={(e) => setFormData({ ...formData, DmMessage: e.target.value })}
      />
      <p className="text-xs text-neutral-500 mt-2">
        Be personal and helpful. Avoid spam-like language.
      </p>
    </div>

    <div>
      <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
        Optional: Add Button (Instagram feature)
      </label>
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
                newButtons[i].text = e.target.value;
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
                newButtons[i].url = e.target.value;
                setFormData({ ...formData, dm_buttons: newButtons });
              }}
            />
          </div>
        ))}
      </div>
    </div>
  </div>
);

// Step 4: Review
const Step4 = ({ formData }: any) => (
  <div className="space-y-6">
    <div>
      <h2 className="text-2xl font-semibold text-neutral-900 dark:text-white mb-2">
        Review & Create
      </h2>
      <p className="text-neutral-600 dark:text-neutral-400">
        Review your automation settings before creating
      </p>
    </div>

    <div className="space-y-4">
      <div className="p-4 bg-neutral-50 dark:bg-neutral-800/50 rounded-xl">
        <div className="text-sm font-medium text-neutral-500 mb-1">Name</div>
        <div className="text-neutral-900 dark:text-white">{formData.name}</div>
      </div>

      <div className="p-4 bg-neutral-50 dark:bg-neutral-800/50 rounded-xl">
        <div className="text-sm font-medium text-neutral-500 mb-1">Trigger Keywords</div>
        <div className="flex flex-wrap gap-2 mt-2">
          {formData.trigger_keywords
            .filter((k: string) => k.trim())
            .map((keyword: string, i: number) => (
              <span
                key={i}
                className="px-3 py-1 bg-neutral-200 dark:bg-neutral-700 text-neutral-900 dark:text-white rounded-full text-sm"
              >
                {keyword}
              </span>
            ))}
        </div>
      </div>

      {formData.enable_comment_reply && (
        <div className="p-4 bg-neutral-50 dark:bg-neutral-800/50 rounded-xl">
          <div className="text-sm font-medium text-neutral-500 mb-1">Comment Reply</div>
          <div className="text-neutral-900 dark:text-white">
            {formData.comment_reply_message}
          </div>
        </div>
      )}

      <div className="p-4 bg-neutral-50 dark:bg-neutral-800/50 rounded-xl">
        <div className="text-sm font-medium text-neutral-500 mb-1">DM Message</div>
        <div className="text-neutral-900 dark:text-white whitespace-pre-wrap">
          {formData.DmMessage}
        </div>
      </div>
    </div>
  </div>
);
