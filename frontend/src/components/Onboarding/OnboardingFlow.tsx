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
import { HoudiniBackground } from './HoudiniBackground';

interface OnboardingSlide {
  title: string;
  description: string;
  icon: React.ReactNode;
  gradient: string;
  accent: string;
  features: { icon: React.ReactNode; text: string }[];
}

const slides: OnboardingSlide[] = [
  {
    title: 'Welcome to DmMe',
    description: 'Transform your Instagram engagement into real business growth with AI-powered automation.',
    icon: <Sparkles className="w-16 h-16" />,
    gradient: 'from-purple-500/20 to-pink-500/20',
    accent: 'purple',
    features: [
      { icon: <Zap className="w-5 h-5" />, text: 'Instant automated responses to comments' },
      { icon: <Send className="w-5 h-5" />, text: 'AI-personalized DMs that convert' },
      { icon: <TrendingUp className="w-5 h-5" />, text: 'Track and optimize performance' },
    ],
  },
  {
    title: 'Turn Comments Into Customers',
    description: 'Automatically engage with every comment on your posts and convert interest into sales.',
    icon: <Target className="w-16 h-16" />,
    gradient: 'from-blue-500/20 to-cyan-500/20',
    accent: 'blue',
    features: [
      { icon: <Clock className="w-5 h-5" />, text: 'Respond within seconds, 24/7' },
      { icon: <Sparkles className="w-5 h-5" />, text: 'AI crafts personalized messages' },
      { icon: <DollarSign className="w-5 h-5" />, text: 'Never miss a potential sale' },
    ],
  },
  {
    title: 'Setup in 3 Simple Steps',
    description: 'Get started in less than 5 minutes and watch your engagement soar.',
    icon: <Instagram className="w-16 h-16" />,
    gradient: 'from-orange-500/20 to-red-500/20',
    accent: 'orange',
    features: [
      { icon: <Check className="w-5 h-5" />, text: 'Connect your Instagram account' },
      { icon: <Check className="w-5 h-5" />, text: 'Create your first automation' },
      { icon: <Check className="w-5 h-5" />, text: 'Watch automations work for you' },
    ],
  },
];

export const OnboardingFlow = () => {
  const initialStep = parseInt(localStorage.getItem('onboarding_step') || '0', 10);
  const [currentSlide, setCurrentSlide] = useState(initialStep < slides.length ? initialStep : 0);
  const [completing, setCompleting] = useState(false);
  const navigate = useNavigate();

  const handleNext = async () => {
    if (currentSlide < slides.length - 1) {
      const nextSlide = currentSlide + 1;
      setCurrentSlide(nextSlide);
      try {
        await api.saveOnboardingStep(nextSlide);
        localStorage.setItem('onboarding_step', String(nextSlide));
      } catch (err) {
        console.error('Failed to save onboarding step', err);
      }
    } else {
      handleComplete();
    }
  };

  const handlePrev = async () => {
    if (currentSlide > 0) {
      const prevSlide = currentSlide - 1;
      setCurrentSlide(prevSlide);
      try {
        await api.saveOnboardingStep(prevSlide);
        localStorage.setItem('onboarding_step', String(prevSlide));
      } catch (err) {
        console.error('Failed to save onboarding step', err);
      }
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
      localStorage.setItem('onboarding_step', String(slides.length));
      await api.getUserProfile();
      toast.success('Welcome to DmMe!');
      navigate('/dashboard');
    } catch (error) {
      console.error('Failed to complete onboarding:', error);
      localStorage.setItem('onboarding_completed', 'true');
      localStorage.setItem('onboarding_step', String(slides.length));
      navigate('/dashboard');
    }
  };

  const slide = slides[currentSlide];
  const progress = ((currentSlide + 1) / slides.length) * 100;

  const accentColor = slide.accent === 'purple' ? 'purple' : slide.accent === 'blue' ? 'blue' : 'orange';
  const progressGradient = slide.accent === 'purple' 
    ? 'from-purple-500 to-pink-500' 
    : slide.accent === 'blue' 
    ? 'from-blue-500 to-cyan-500' 
    : 'from-orange-500 to-red-600';

  return (
    <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center p-6 relative overflow-hidden">
      <HoudiniBackground />

      <div className="max-w-4xl w-full relative z-10">
        {/* Progress System */}
        <header className="mb-12 animate-fade-in">
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm font-bold tracking-widest uppercase text-neutral-500">
              Onboarding <span className="text-white ml-2">Step {currentSlide + 1} / {slides.length}</span>
            </span>
            <button
              onClick={handleSkip}
              className="text-sm font-medium text-neutral-400 hover:text-white transition-all flex items-center gap-1 group"
            >
              Skip Introduction
              <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
          <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden blur-[0.5px]">
            <div
              className={`h-full bg-gradient-to-r ${progressGradient} transition-all duration-700 ease-out shadow-[0_0_20px_rgba(168,85,247,0.4)]`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </header>

        {/* Glassmorphism Card */}
        <main className="relative group">
          {/* Subtle Glow Background */}
          <div className={`absolute -inset-1 bg-gradient-to-r ${progressGradient} rounded-[2rem] blur-2xl opacity-10 group-hover:opacity-20 transition-opacity duration-500`}></div>
          
          <div className="relative bg-neutral-900/40 backdrop-blur-3xl rounded-[2rem] border border-white/10 shadow-2xl overflow-hidden min-h-[500px] flex flex-col">
            <div className="grid md:grid-cols-2 flex-1">
              {/* Visual Side */}
              <div className={`p-12 flex flex-col items-center justify-center text-center relative overflow-hidden bg-gradient-to-br ${slide.gradient}`}>
                <div className="absolute inset-0 bg-neutral-900/20 backdrop-blur-[2px]"></div>
                
                <div className="relative z-10 space-y-8">
                  <div className="inline-flex items-center justify-center p-6 bg-white/5 rounded-3xl border border-white/10 backdrop-blur-md animate-float shadow-2xl">
                    <div className={`text-${accentColor}-400`}>
                      {slide.icon}
                    </div>
                  </div>
                  <div className="space-y-4">
                    <h1 className="text-4xl font-extrabold text-white tracking-tight leading-tight">
                      {slide.title}
                    </h1>
                    <p className="text-lg text-neutral-400 font-medium max-w-xs mx-auto">
                      {slide.description}
                    </p>
                  </div>
                </div>
              </div>

              {/* Content Side */}
              <div className="p-12 flex flex-col justify-between bg-neutral-900/40">
                <div className="space-y-6">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-neutral-500 mb-8">
                    Key Features
                  </h3>
                  <div className="space-y-4">
                    {slide.features.map((feature, index) => (
                      <div
                        key={index}
                        className="flex items-center gap-4 p-4 rounded-2xl bg-white/5 border border-white/5 hover:border-white/10 hover:bg-white/10 transition-all duration-300 group/item"
                        style={{
                          animation: `slideInUp 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) ${index * 0.1}s both`,
                        }}
                      >
                        <div className={`p-2.5 rounded-xl bg-neutral-800 text-${accentColor}-400 group-hover/item:scale-110 transition-transform duration-300`}>
                          {feature.icon}
                        </div>
                        <span className="text-neutral-300 font-medium tracking-tight">
                          {feature.text}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Navigation Controls */}
                <div className="pt-12 flex items-center justify-between">
                  <button
                    onClick={handlePrev}
                    disabled={currentSlide === 0}
                    className={`p-3 rounded-xl border border-white/10 transition-all ${currentSlide === 0
                      ? 'text-neutral-700 border-neutral-800 cursor-not-allowed'
                      : 'text-neutral-400 hover:text-white hover:bg-white/5'
                      }`}
                  >
                    <ChevronLeft className="w-6 h-6" />
                  </button>

                  <div className="flex gap-1.5">
                    {slides.map((_, index) => (
                      <div
                        key={index}
                        className={`h-1.5 rounded-full transition-all duration-500 ${index === currentSlide
                          ? `w-8 bg-gradient-to-r ${progressGradient}`
                          : 'w-1.5 bg-neutral-800'
                          }`}
                      />
                    ))}
                  </div>

                  <button
                    onClick={handleNext}
                    disabled={completing}
                    className={`group relative flex items-center gap-2 px-8 py-3.5 rounded-xl font-bold text-white overflow-hidden transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50`}
                  >
                    <div className={`absolute inset-0 bg-gradient-to-r ${progressGradient} opacity-90 group-hover:opacity-100 transition-opacity`}></div>
                    <span className="relative z-10 flex items-center gap-2">
                      {completing ? (
                        'Saving...'
                      ) : currentSlide === slides.length - 1 ? (
                        <>
                          Launch App
                          <Sparkles className="w-5 h-5" />
                        </>
                      ) : (
                        <>
                          Continue
                          <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                        </>
                      )}
                    </span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </main>

        <footer className="mt-12 flex items-center justify-center gap-8 text-neutral-500 font-medium text-xs tracking-widest uppercase">
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
            Enterprise Grade Security
          </div>
          <div className="w-1 h-1 rounded-full bg-neutral-800"></div>
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]"></div>
            Powered by Meta AI
          </div>
        </footer>
      </div>

      <style>{`
        @keyframes slideInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        @keyframes float {
          0%, 100% {
            transform: translateY(0px) rotate(0deg);
          }
          50% {
            transform: translateY(-20px) rotate(2deg);
          }
        }

        .animate-fade-in {
          animation: fadeIn 0.8s ease-out;
        }

        .animate-float {
          animation: float 6s ease-in-out infinite;
        }

        .text-purple-400 { color: #c084fc; }
        .text-blue-400 { color: #60a5fa; }
        .text-orange-400 { color: #fb923c; }
        
        body {
          background-color: #0a0a0a;
        }
      `}</style>
    </div>
  );
};

