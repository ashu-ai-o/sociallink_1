import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Zap,
  Send,
  TrendingUp,
  Instagram,
  Sparkles,
  Target,
  Clock,
  DollarSign,
  ChevronRight,
  ChevronLeft,
  Check,
} from 'lucide-react';
import { api } from '../../utils/api';
import toast from 'react-hot-toast';

interface OnboardingSlide {
  title: string;
  description: string;
  icon: React.ReactNode;
  gradient: string;
  features: { icon: React.ReactNode; text: string }[];
}

const slides: OnboardingSlide[] = [
  {
    title: 'Welcome to DmMe',
    description: 'Transform your Instagram engagement into real business growth with AI-powered automation',
    icon: <Sparkles className="w-16 h-16" />,
    gradient: 'from-purple-500 to-pink-500',
    features: [
      { icon: <Zap className="w-5 h-5" />, text: 'Instant automated responses to comments' },
      { icon: <Send className="w-5 h-5" />, text: 'AI-personalized DMs that convert' },
      { icon: <TrendingUp className="w-5 h-5" />, text: 'Track and optimize performance' },
    ],
  },
  {
    title: 'Turn Comments Into Customers',
    description: 'Automatically engage with every comment on your posts and convert interest into sales',
    icon: <Target className="w-16 h-16" />,
    gradient: 'from-blue-500 to-cyan-500',
    features: [
      { icon: <Clock className="w-5 h-5" />, text: 'Respond within seconds, 24/7' },
      { icon: <Sparkles className="w-5 h-5" />, text: 'AI crafts personalized messages' },
      { icon: <DollarSign className="w-5 h-5" />, text: 'Never miss a potential sale' },
    ],
  },
  {
    title: 'Setup in 3 Simple Steps',
    description: 'Get started in less than 5 minutes and watch your engagement soar',
    icon: <Instagram className="w-16 h-16" />,
    gradient: 'from-orange-500 to-red-500',
    features: [
      { icon: <Check className="w-5 h-5" />, text: '1. Connect your Instagram Business account' },
      { icon: <Check className="w-5 h-5" />, text: '2. Create your first automation workflow' },
      { icon: <Check className="w-5 h-5" />, text: '3. Watch automations work while you sleep' },
    ],
  },
];

export const OnboardingFlow = () => {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [completing, setCompleting] = useState(false);
  const navigate = useNavigate();

  const handleNext = () => {
    if (currentSlide < slides.length - 1) {
      setCurrentSlide(currentSlide + 1);
    } else {
      handleComplete();
    }
  };

  const handlePrev = () => {
    if (currentSlide > 0) {
      setCurrentSlide(currentSlide - 1);
    }
  };

  const handleSkip = async () => {
    await handleComplete();
  };

  const handleComplete = async () => {
    try {
      setCompleting(true);
      await api.completeOnboarding();
      localStorage.setItem('onboarding_completed', 'true');
      toast.success('Welcome to DmMe!');
      navigate('/dashboard');
    } catch (error) {
      console.error('Failed to complete onboarding:', error);
      toast.error('Failed to save progress');
      // Still allow navigation even if API fails
      localStorage.setItem('onboarding_completed', 'true');
      navigate('/dashboard');
    }
  };

  const slide = slides[currentSlide];
  const progress = ((currentSlide + 1) / slides.length) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Step {currentSlide + 1} of {slides.length}
            </span>
            <button
              onClick={handleSkip}
              className="text-sm font-medium text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
            >
              Skip
            </button>
          </div>
          <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Main Content Card */}
        <div className="bg-white dark:bg-gray-800 rounded-3xl shadow-2xl overflow-hidden">
          {/* Gradient Header */}
          <div className={`bg-gradient-to-r ${slide.gradient} p-12 text-white relative overflow-hidden`}>
            <div className="absolute inset-0 opacity-10">
              <div className="absolute -top-24 -right-24 w-96 h-96 bg-white rounded-full blur-3xl" />
              <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-white rounded-full blur-3xl" />
            </div>

            <div className="relative z-10 text-center">
              <div className="inline-flex items-center justify-center mb-6 animate-float">
                {slide.icon}
              </div>
              <h1 className="text-4xl font-bold mb-4 animate-fade-in">
                {slide.title}
              </h1>
              <p className="text-xl text-white/90 max-w-2xl mx-auto animate-fade-in-delayed">
                {slide.description}
              </p>
            </div>
          </div>

          {/* Features List */}
          <div className="p-12">
            <div className="space-y-6 max-w-2xl mx-auto">
              {slide.features.map((feature, index) => (
                <div
                  key={index}
                  className="flex items-start gap-4 p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50 hover-lift cursor-default border border-transparent hover:border-gray-200 dark:hover:border-gray-600"
                  style={{
                    animation: `slideInFromLeft 0.5s ease-out ${index * 0.1}s both`,
                  }}
                >
                  <div className={`p-3 rounded-lg bg-gradient-to-r ${slide.gradient} text-white flex-shrink-0 transition-transform duration-300 hover:scale-110`}>
                    {feature.icon}
                  </div>
                  <p className="text-lg text-gray-700 dark:text-gray-300 flex-1 pt-2">
                    {feature.text}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Navigation */}
          <div className="px-12 pb-12">
            <div className="flex items-center justify-between gap-4">
              <button
                onClick={handlePrev}
                disabled={currentSlide === 0}
                className={`flex items-center gap-2 px-6 py-3 rounded-xl font-semibold transition-all ${
                  currentSlide === 0
                    ? 'text-gray-400 dark:text-gray-600 cursor-not-allowed'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                <ChevronLeft className="w-5 h-5" />
                Previous
              </button>

              <div className="flex gap-2">
                {slides.map((_, index) => (
                  <div
                    key={index}
                    className={`h-2 rounded-full transition-all duration-300 ${
                      index === currentSlide
                        ? 'w-8 bg-gradient-to-r from-purple-500 to-pink-500'
                        : 'w-2 bg-gray-300 dark:bg-gray-600'
                    }`}
                  />
                ))}
              </div>

              <button
                onClick={handleNext}
                disabled={completing}
                className="flex items-center gap-2 px-8 py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 shadow-lg hover:shadow-xl transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {completing ? (
                  'Completing...'
                ) : currentSlide === slides.length - 1 ? (
                  <>
                    Get Started
                    <Check className="w-5 h-5" />
                  </>
                ) : (
                  <>
                    Next
                    <ChevronRight className="w-5 h-5" />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Additional Info */}
        <div className="mt-8 text-center">
          <div className="flex items-center justify-center gap-6 text-sm text-gray-600 dark:text-gray-400">
            <div className="flex items-center gap-2 animate-fade-in">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
              <span>Secure & Private</span>
            </div>
            <div className="w-px h-4 bg-gray-300 dark:bg-gray-600"></div>
            <div className="flex items-center gap-2 animate-fade-in-delayed">
              <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" style={{ animationDelay: '0.5s' }}></div>
              <span>No credit card required</span>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes slideInFromLeft {
          from {
            opacity: 0;
            transform: translateX(-20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes float {
          0%, 100% {
            transform: translateY(0px);
          }
          50% {
            transform: translateY(-10px);
          }
        }

        @keyframes shimmer {
          0% {
            background-position: -1000px 0;
          }
          100% {
            background-position: 1000px 0;
          }
        }

        .animate-fade-in {
          animation: fadeIn 0.6s ease-out;
        }

        .animate-fade-in-delayed {
          animation: fadeIn 0.6s ease-out 0.2s both;
        }

        .animate-float {
          animation: float 3s ease-in-out infinite;
        }

        .hover-lift {
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .hover-lift:hover {
          transform: translateY(-4px);
          box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }
      `}</style>
    </div>
  );
};
