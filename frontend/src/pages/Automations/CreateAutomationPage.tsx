import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Check, Sparkles } from 'lucide-react';
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
    comment_reply_message: '✅ Sent! Check your DM',
    dm_message: '',
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
          instagram_account: 'default', // Replace with actual account ID
          trigger_type: 'comment',
          target_posts: [],
        })
      ).unwrap();

      toast.success('Automation created successfully!');
      navigate('/automations');
    } catch (error: any) {
      toast.error(error.message || 'Failed to create automation');
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    { number: 1, title: 'Basic Info', description: 'Name and trigger keywords' },
    { number: 2, title: 'Comment Reply', description: 'Public response settings' },
    { number: 3, title: 'DM Message', description: 'Private message content' },
    { number: 4, title: 'AI Enhancement', description: 'Optional AI personalization' },
    { number: 5, title: 'Review', description: 'Review and activate' },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6 slide-in-up">
      {/* Header */}
      <div>
        <button
          onClick={() => navigate('/automations')}
          className="inline-flex items-center gap-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Automations
        </button>
        <h1 className="text-3xl font-bold text-[var(--text-primary)]">
          Create New Automation
        </h1>
        <p className="text-[var(--text-secondary)] mt-1">
          Set up automated responses for Instagram comments
        </p>
      </div>

      {/* Progress Steps */}
      <div className="card">
        <div className="flex items-center justify-between">
          {steps.map((s, i) => (
            <div key={s.number} className="flex items-center flex-1">
              <div className="flex flex-col items-center">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                    step > s.number
                      ? 'bg-[var(--accent-primary)] text-white'
                      : step === s.number
                      ? 'bg-[var(--accent-light)] text-[var(--accent-primary)] ring-4 ring-[var(--accent-light)]'
                      : 'bg-[var(--bg-secondary)] text-[var(--text-tertiary)]'
                  }`}
                >
                  {step > s.number ? <Check className="w-5 h-5" /> : s.number}
                </div>
                <div className="text-center mt-2">
                  <div className="text-sm font-medium text-[var(--text-primary)] hidden md:block">
                    {s.title}
                  </div>
                  <div className="text-xs text-[var(--text-tertiary)] hidden lg:block">
                    {s.description}
                  </div>
                </div>
              </div>
              {i < steps.length - 1 && (
                <div
                  className={`flex-1 h-0.5 mx-4 ${
                    step > s.number ? 'bg-[var(--accent-primary)]' : 'bg-[var(--border-primary)]'
                  }`}
                ></div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Form Steps */}
      <div className="card">
        {step === 1 && <Step1 formData={formData} setFormData={setFormData} />}
        {step === 2 && <Step2 formData={formData} setFormData={setFormData} />}
        {step === 3 && <Step3 formData={formData} setFormData={setFormData} />}
        {step === 4 && <Step4 formData={formData} setFormData={setFormData} />}
        {step === 5 && <Step5 formData={formData} />}
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          onClick={() => setStep(Math.max(1, step - 1))}
          disabled={step === 1}
          className="btn btn-secondary"
        >
          <ArrowLeft className="w-4 h-4" />
          Previous
        </button>
        {step < 5 ? (
          <button
            onClick={() => setStep(Math.min(5, step + 1))}
            className="btn btn-primary"
          >
            Next
            <ArrowRight className="w-4 h-4" />
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="btn btn-primary"
          >
            {loading ? (
              <>
                <div className="spinner" />
                Creating...
              </>
            ) : (
              <>
                <Check className="w-4 h-4" />
                Create Automation
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
};

// Form Step Components
const Step1 = ({ formData, setFormData }: any) => (
  <div className="space-y-6">
    <div>
      <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-4">
        Basic Information
      </h2>
      <div className="space-y-4">
        <div>
          <label className="label">Automation Name *</label>
          <input
            type="text"
            className="input"
            placeholder="e.g., Link Please Automation"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
        </div>

        <div>
          <label className="label">Trigger Keywords *</label>
          {formData.trigger_keywords.map((keyword: string, i: number) => (
            <div key={i} className="flex gap-2 mb-2">
              <input
                type="text"
                className="input flex-1"
                placeholder="e.g., link please"
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
                  className="btn btn-secondary"
                >
                  +
                </button>
              )}
            </div>
          ))}
        </div>

        <div>
          <label className="label">Match Type</label>
          <select
            className="input"
            value={formData.trigger_match_type}
            onChange={(e) =>
              setFormData({ ...formData, trigger_match_type: e.target.value })
            }
          >
            <option value="contains">Contains keyword</option>
            <option value="exact">Exact match</option>
            <option value="any">Any comment</option>
          </select>
        </div>
      </div>
    </div>
  </div>
);

const Step2 = ({ formData, setFormData }: any) => (
  <div className="space-y-6">
    <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-4">
      Comment Reply (Public)
    </h2>
    <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-4">
      <p className="text-sm text-blue-900 dark:text-blue-100">
        💡 This message will be posted publicly as a reply to the comment
      </p>
    </div>

    <div>
      <label className="flex items-center gap-2 mb-4">
        <input
          type="checkbox"
          checked={formData.enable_comment_reply}
          onChange={(e) =>
            setFormData({ ...formData, enable_comment_reply: e.target.checked })
          }
        />
        <span className="text-[var(--text-primary)]">Enable comment replies</span>
      </label>
    </div>

    {formData.enable_comment_reply && (
      <div>
        <label className="label">Reply Message *</label>
        <input
          type="text"
          className="input"
          placeholder="e.g., ✅ Sent! Check your DM"
          value={formData.comment_reply_message}
          onChange={(e) =>
            setFormData({ ...formData, comment_reply_message: e.target.value })
          }
          maxLength={200}
        />
        <p className="text-xs text-[var(--text-tertiary)] mt-1">
          {formData.comment_reply_message.length}/200 characters
        </p>
      </div>
    )}
  </div>
);

const Step3 = ({ formData, setFormData }: any) => (
  <div className="space-y-6">
    <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-4">
      DM Message (Private)
    </h2>
    <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4 mb-4">
      <p className="text-sm text-purple-900 dark:text-purple-100">
        💬 This message will be sent privately via Instagram DM
      </p>
    </div>

    <div>
      <label className="label">Message Text *</label>
      <textarea
        className="input min-h-[120px]"
        placeholder="Thanks for your interest! Here's the link: https://yoursite.com"
        value={formData.dm_message}
        onChange={(e) => setFormData({ ...formData, dm_message: e.target.value })}
        required
      />
    </div>

    <div>
      <label className="label">Buttons (Optional)</label>
      {formData.dm_buttons.map((button: any, i: number) => (
        <div key={i} className="grid grid-cols-2 gap-2 mb-2">
          <input
            type="text"
            className="input"
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
            className="input"
            placeholder="URL"
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
);

const Step4 = ({ formData, setFormData }: any) => (
  <div className="space-y-6">
    <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-4">
      AI Enhancement
    </h2>

    <div>
      <label className="flex items-center gap-2 mb-4">
        <input
          type="checkbox"
          checked={formData.use_ai_enhancement}
          onChange={(e) =>
            setFormData({ ...formData, use_ai_enhancement: e.target.checked })
          }
        />
        <span className="flex items-center gap-2 text-[var(--text-primary)]">
          <Sparkles className="w-4 h-4 text-[var(--accent-primary)]" />
          Enable AI-powered message personalization
        </span>
      </label>
    </div>

    {formData.use_ai_enhancement && (
      <div>
        <label className="label">Business Context</label>
        <textarea
          className="input min-h-[120px]"
          placeholder="Describe your business/product to help AI personalize messages..."
          value={formData.ai_context}
          onChange={(e) => setFormData({ ...formData, ai_context: e.target.value })}
        />
      </div>
    )}
  </div>
);

const Step5 = ({ formData }: any) => (
  <div className="space-y-6">
    <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-4">
      Review & Create
    </h2>

    <div className="space-y-4">
      <div className="p-4 rounded-lg bg-[var(--bg-secondary)]">
        <h3 className="font-medium text-[var(--text-primary)] mb-2">Name</h3>
        <p className="text-[var(--text-secondary)]">{formData.name}</p>
      </div>

      <div className="p-4 rounded-lg bg-[var(--bg-secondary)]">
        <h3 className="font-medium text-[var(--text-primary)] mb-2">Trigger Keywords</h3>
        <div className="flex flex-wrap gap-2">
          {formData.trigger_keywords
            .filter((k: string) => k.trim())
            .map((keyword: string, i: number) => (
              <span
                key={i}
                className="px-3 py-1 rounded-full bg-[var(--accent-light)] text-[var(--accent-primary)] text-sm"
              >
                {keyword}
              </span>
            ))}
        </div>
      </div>

      {formData.enable_comment_reply && (
        <div className="p-4 rounded-lg bg-[var(--bg-secondary)]">
          <h3 className="font-medium text-[var(--text-primary)] mb-2">
            Comment Reply
          </h3>
          <p className="text-[var(--text-secondary)]">
            {formData.comment_reply_message}
          </p>
        </div>
      )}

      <div className="p-4 rounded-lg bg-[var(--bg-secondary)]">
        <h3 className="font-medium text-[var(--text-primary)] mb-2">DM Message</h3>
        <p className="text-[var(--text-secondary)]">{formData.dm_message}</p>
      </div>

      {formData.use_ai_enhancement && (
        <div className="p-4 rounded-lg bg-[var(--accent-light)]">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-4 h-4 text-[var(--accent-primary)]" />
            <h3 className="font-medium text-[var(--accent-primary)]">
              AI Enhancement Enabled
            </h3>
          </div>
          <p className="text-sm text-[var(--accent-primary)]">
            Messages will be personalized using Claude AI
          </p>
        </div>
      )}
    </div>
  </div>
);

// EditAutomationPage would be similar structure...
export const EditAutomationPage = () => {
  // Similar to CreateAutomationPage but with pre-filled data
  return <div>Edit Automation Page (similar to create)</div>;
};


