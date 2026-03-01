import React, { useState, useEffect } from 'react';
import { MessageSquare, Star, Send, Clock, CheckCircle2, AlertCircle, ArrowLeft } from 'lucide-react';
import { api } from '../utils/api';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';

const CATEGORIES = [
    { value: 'bug', label: 'Bug Report', icon: '🐛' },
    { value: 'feature', label: 'Feature Request', icon: '✨' },
    { value: 'general', label: 'General Feedback', icon: '💬' },
    { value: 'ux', label: 'UX / Design', icon: '🎨' },
    { value: 'performance', label: 'Performance', icon: '⚡' },
    { value: 'other', label: 'Other', icon: '📝' },
];

const STATUS_COLORS: Record<string, string> = {
    open: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
    in_review: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400',
    planned: 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400',
    resolved: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
    closed: 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400',
};

export const FeedbackPage: React.FC = () => {
    const [category, setCategory] = useState('general');
    const [title, setTitle] = useState('');
    const [message, setMessage] = useState('');
    const [rating, setRating] = useState(0);
    const [hoverRating, setHoverRating] = useState(0);
    const [loading, setLoading] = useState(false);
    const [myFeedback, setMyFeedback] = useState<any[]>([]);
    const [feedbackLoading, setFeedbackLoading] = useState(true);
    const [showForm, setShowForm] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        loadMyFeedback();
    }, []);

    const loadMyFeedback = async () => {
        try {
            const data = await api.getMyFeedback();
            setMyFeedback(data.results || data || []);
        } catch (error) {
            console.error('Failed to load feedback:', error);
        } finally {
            setFeedbackLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            await api.submitFeedback({
                category,
                title,
                message,
                rating: rating > 0 ? rating : undefined,
                page_url: window.location.href,
            });
            toast.success('Thank you for your feedback!');
            setTitle('');
            setMessage('');
            setRating(0);
            setCategory('general');
            loadMyFeedback();
        } catch (error: any) {
            toast.error(error.response?.data?.error || 'Failed to submit feedback');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-8 animate-fade-in">
            {/* Header */}
            <div>
                <button
                    onClick={() => navigate(-1)}
                    className="inline-flex items-center gap-2 text-sm text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200 mb-4 transition-colors"
                >
                    <ArrowLeft className="w-4 h-4" />
                    Back
                </button>
                <h1 className="text-3xl font-semibold text-neutral-900 dark:text-white">Feedback</h1>
                <p className="text-neutral-600 dark:text-neutral-400 mt-1">
                    Help us improve by sharing your thoughts, reporting bugs, or suggesting features
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Submit Form */}
                <div className="bg-white dark:bg-neutral-900 rounded-2xl p-8 border border-neutral-200 dark:border-neutral-800">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-2.5 rounded-xl bg-purple-100 dark:bg-purple-900/30">
                            <MessageSquare className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                        </div>
                        <h2 className="text-xl font-semibold text-neutral-900 dark:text-white">
                            Submit Feedback
                        </h2>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-5">
                        {/* Category */}
                        <div>
                            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                                Category
                            </label>
                            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                                {CATEGORIES.map((cat) => (
                                    <button
                                        key={cat.value}
                                        type="button"
                                        onClick={() => setCategory(cat.value)}
                                        className={`flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${category === cat.value
                                            ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 border-2 border-purple-300 dark:border-purple-800 scale-[1.02]'
                                            : 'bg-neutral-50 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 border-2 border-transparent hover:bg-neutral-100 dark:hover:bg-neutral-700'
                                            }`}
                                    >
                                        <span>{cat.icon}</span>
                                        <span className="truncate">{cat.label}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Title */}
                        <div>
                            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                                Title
                            </label>
                            <input
                                type="text"
                                className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent transition-all"
                                placeholder="Brief summary of your feedback"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                required
                                minLength={3}
                            />
                        </div>

                        {/* Message */}
                        <div>
                            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                                Message
                            </label>
                            <textarea
                                className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl text-neutral-900 dark:text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent transition-all resize-none"
                                placeholder="Describe your feedback in detail..."
                                rows={5}
                                value={message}
                                onChange={(e) => setMessage(e.target.value)}
                                required
                                minLength={10}
                            />
                        </div>

                        {/* Rating */}
                        <div>
                            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                                Rating (optional)
                            </label>
                            <div className="flex gap-1">
                                {[1, 2, 3, 4, 5].map((star) => (
                                    <button
                                        key={star}
                                        type="button"
                                        onClick={() => setRating(star === rating ? 0 : star)}
                                        onMouseEnter={() => setHoverRating(star)}
                                        onMouseLeave={() => setHoverRating(0)}
                                        className="p-1 transition-transform hover:scale-110"
                                    >
                                        <Star
                                            className={`w-7 h-7 transition-colors ${star <= (hoverRating || rating)
                                                ? 'text-amber-400 fill-amber-400'
                                                : 'text-neutral-300 dark:text-neutral-600'
                                                }`}
                                        />
                                    </button>
                                ))}
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full flex items-center justify-center gap-2 px-6 py-3.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-xl font-medium shadow-lg shadow-purple-500/30 transition-all disabled:opacity-50 hover:scale-[1.02] active:scale-[0.98]"
                        >
                            <Send className="w-4 h-4" />
                            {loading ? 'Submitting...' : 'Submit Feedback'}
                        </button>
                    </form>
                </div>

                {/* Past Feedback */}
                <div className="bg-white dark:bg-neutral-900 rounded-2xl p-8 border border-neutral-200 dark:border-neutral-800">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-2.5 rounded-xl bg-blue-100 dark:bg-blue-900/30">
                            <Clock className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                        </div>
                        <h2 className="text-xl font-semibold text-neutral-900 dark:text-white">
                            My Submissions
                        </h2>
                    </div>

                    {feedbackLoading ? (
                        <div className="animate-pulse space-y-3">
                            {[...Array(3)].map((_, i) => (
                                <div key={i} className="h-16 bg-neutral-200 dark:bg-neutral-800 rounded-xl"></div>
                            ))}
                        </div>
                    ) : myFeedback.length === 0 ? (
                        <div className="text-center py-12">
                            <MessageSquare className="w-12 h-12 text-neutral-300 dark:text-neutral-700 mx-auto mb-3" />
                            <p className="text-neutral-500 dark:text-neutral-400">No feedback submitted yet</p>
                        </div>
                    ) : (
                        <div className="space-y-3 max-h-[500px] overflow-y-auto">
                            {myFeedback.map((item: any) => (
                                <div
                                    key={item.id}
                                    className="p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 hover:border-neutral-300 dark:hover:border-neutral-700 transition-colors"
                                >
                                    <div className="flex items-start justify-between gap-3 mb-2">
                                        <h4 className="font-medium text-neutral-900 dark:text-white text-sm line-clamp-1">
                                            {item.title}
                                        </h4>
                                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider whitespace-nowrap ${STATUS_COLORS[item.status] || STATUS_COLORS.open}`}>
                                            {item.status?.replace('_', ' ')}
                                        </span>
                                    </div>
                                    <p className="text-xs text-neutral-500 dark:text-neutral-400 line-clamp-2 mb-2">
                                        {item.message}
                                    </p>
                                    <div className="flex items-center gap-3 text-xs text-neutral-400">
                                        <span>{CATEGORIES.find((c) => c.value === item.category)?.icon} {CATEGORIES.find((c) => c.value === item.category)?.label}</span>
                                        <span>•</span>
                                        <span>{new Date(item.created_at).toLocaleDateString()}</span>
                                        {item.rating && (
                                            <>
                                                <span>•</span>
                                                <span className="flex items-center gap-0.5">
                                                    <Star className="w-3 h-3 text-amber-400 fill-amber-400" />
                                                    {item.rating}
                                                </span>
                                            </>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
