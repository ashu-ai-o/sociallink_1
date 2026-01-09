import { useState } from 'react';
import { Mail, Phone, MapPin, Send } from 'lucide-react';
import toast from 'react-hot-toast';

export const ContactUsPage = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: '',
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    // Simulate API call
    setTimeout(() => {
      toast.success('Message sent! We\'ll get back to you within 24 hours.');
      setFormData({ name: '', email: '', subject: '', message: '' });
      setLoading(false);
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-[var(--bg-secondary)]">
      {/* Header */}
      <div className="border-b border-[var(--border-primary)] bg-[var(--bg-primary)]">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-[var(--text-primary)] mb-4">
            Get in Touch
          </h1>
          <p className="text-xl text-[var(--text-secondary)]">
            Have questions? We'd love to hear from you.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Contact Info */}
          <div className="space-y-6">
            <div className="card">
              <div className="inline-flex p-3 rounded-xl bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 mb-4">
                <Mail className="w-6 h-6" />
              </div>
              <h3 className="font-semibold text-[var(--text-primary)] mb-2">
                Email Us
              </h3>
              <p className="text-[var(--text-secondary)] text-sm mb-2">
                For general inquiries and support
              </p>
              <a
                href="mailto:support@linkplease.co"
                className="text-[var(--accent-primary)] hover:underline"
              >
                support@linkplease.co
              </a>
            </div>

            <div className="card">
              <div className="inline-flex p-3 rounded-xl bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 mb-4">
                <Phone className="w-6 h-6" />
              </div>
              <h3 className="font-semibold text-[var(--text-primary)] mb-2">
                Call Us
              </h3>
              <p className="text-[var(--text-secondary)] text-sm mb-2">
                Monday - Friday, 9am - 6pm EST
              </p>
              <a
                href="tel:+15551234567"
                className="text-[var(--accent-primary)] hover:underline"
              >
                +1 (555) 123-4567
              </a>
            </div>

            <div className="card">
              <div className="inline-flex p-3 rounded-xl bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 mb-4">
                <MapPin className="w-6 h-6" />
              </div>
              <h3 className="font-semibold text-[var(--text-primary)] mb-2">
                Visit Us
              </h3>
              <p className="text-[var(--text-secondary)] text-sm">
                123 Innovation Street
                <br />
                San Francisco, CA 94103
                <br />
                United States
              </p>
            </div>
          </div>

          {/* Contact Form */}
          <div className="lg:col-span-2">
            <form onSubmit={handleSubmit} className="card">
              <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-6">
                Send us a Message
              </h2>

              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="label">Name *</label>
                    <input
                      type="text"
                      className="input"
                      placeholder="John Doe"
                      value={formData.name}
                      onChange={(e) =>
                        setFormData({ ...formData, name: e.target.value })
                      }
                      required
                    />
                  </div>
                  <div>
                    <label className="label">Email *</label>
                    <input
                      type="email"
                      className="input"
                      placeholder="john@example.com"
                      value={formData.email}
                      onChange={(e) =>
                        setFormData({ ...formData, email: e.target.value })
                      }
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="label">Subject *</label>
                  <input
                    type="text"
                    className="input"
                    placeholder="How can we help?"
                    value={formData.subject}
                    onChange={(e) =>
                      setFormData({ ...formData, subject: e.target.value })
                    }
                    required
                  />
                </div>

                <div>
                  <label className="label">Message *</label>
                  <textarea
                    className="input min-h-[150px]"
                    placeholder="Tell us more about your inquiry..."
                    value={formData.message}
                    onChange={(e) =>
                      setFormData({ ...formData, message: e.target.value })
                    }
                    required
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="btn btn-primary w-full justify-center"
                >
                  {loading ? (
                    <>
                      <div className="spinner" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      Send Message
                    </>
                  )}
                </button>

                <p className="text-sm text-[var(--text-tertiary)] text-center">
                  We typically respond within 24 hours
                </p>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};


