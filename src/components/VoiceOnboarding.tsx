import { useState, useEffect } from 'react';
import { Mic, Volume2, CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface VoiceOnboardingProps {
  onComplete: () => void;
  isSupported: boolean;
}

type OnboardingStep = 'intro' | 'microphone' | 'speaker' | 'complete';

export function VoiceOnboarding({ onComplete, isSupported }: VoiceOnboardingProps) {
  const [step, setStep] = useState<OnboardingStep>('intro');
  const [micPermission, setMicPermission] = useState<'pending' | 'granted' | 'denied'>('pending');
  const [speakerTest, setSpeakerTest] = useState<'pending' | 'testing' | 'done'>('pending');

  const requestMicPermission = async () => {
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
      setMicPermission('granted');
      setTimeout(() => setStep('speaker'), 1000);
    } catch (error) {
      setMicPermission('denied');
    }
  };

  const testSpeaker = () => {
    setSpeakerTest('testing');
    const utterance = new SpeechSynthesisUtterance('Welcome to VoiceMail! I am Swar, your voice assistant.');
    utterance.onend = () => {
      setSpeakerTest('done');
      setTimeout(() => setStep('complete'), 1000);
    };
    window.speechSynthesis.speak(utterance);
  };

  useEffect(() => {
    if (step === 'complete') {
      const timer = setTimeout(onComplete, 2000);
      return () => clearTimeout(timer);
    }
  }, [step, onComplete]);

  if (!isSupported) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="w-16 h-16 mx-auto rounded-full bg-destructive/10 flex items-center justify-center mb-4">
              <XCircle className="w-8 h-8 text-destructive" />
            </div>
            <CardTitle>Browser Not Supported</CardTitle>
            <CardDescription>
              Your browser doesn't support the Web Speech API required for voice control.
              Please use Chrome, Edge, or Safari.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5 flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-2xl">
        <CardHeader className="text-center pb-2">
          <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-primary to-accent flex items-center justify-center mb-4 shadow-lg">
            {step === 'complete' ? (
              <CheckCircle2 className="w-10 h-10 text-white animate-fade-in" />
            ) : step === 'speaker' ? (
              <Volume2 className="w-10 h-10 text-white animate-pulse" />
            ) : (
              <Mic className="w-10 h-10 text-white" />
            )}
          </div>
          <CardTitle className="text-2xl">
            {step === 'intro' && 'Welcome to VoiceMail'}
            {step === 'microphone' && 'Enable Microphone'}
            {step === 'speaker' && 'Test Speakers'}
            {step === 'complete' && 'All Set!'}
          </CardTitle>
          <CardDescription className="text-base">
            {step === 'intro' && 'Hands-free email assistant powered by voice'}
            {step === 'microphone' && 'We need access to your microphone for voice commands'}
            {step === 'speaker' && 'Let\'s make sure you can hear the assistant'}
            {step === 'complete' && 'You\'re ready to use voice commands'}
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          {step === 'intro' && (
            <>
              <div className="bg-muted/50 rounded-lg p-4 space-y-3">
                <p className="text-sm text-muted-foreground">
                  🎤 Control your email entirely with your voice
                </p>
                <p className="text-sm text-muted-foreground">
                  📧 Read, reply, and manage emails hands-free
                </p>
                <p className="text-sm text-muted-foreground">
                  🔊 Assistant speaks all content aloud
                </p>
              </div>
              <Button 
                className="w-full" 
                size="lg"
                onClick={() => setStep('microphone')}
              >
                Get Started
              </Button>
            </>
          )}

          {step === 'microphone' && (
            <>
              <div className="text-center py-4">
                {micPermission === 'pending' && (
                  <Button 
                    size="lg" 
                    className="w-full"
                    onClick={requestMicPermission}
                  >
                    <Mic className="w-5 h-5 mr-2" />
                    Allow Microphone Access
                  </Button>
                )}
                {micPermission === 'granted' && (
                  <div className="flex items-center justify-center gap-2 text-success">
                    <CheckCircle2 className="w-6 h-6" />
                    <span className="font-medium">Microphone enabled!</span>
                  </div>
                )}
                {micPermission === 'denied' && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-center gap-2 text-destructive">
                      <XCircle className="w-6 h-6" />
                      <span className="font-medium">Permission denied</span>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Please enable microphone access in your browser settings and refresh.
                    </p>
                  </div>
                )}
              </div>
            </>
          )}

          {step === 'speaker' && (
            <>
              <div className="text-center py-4">
                {speakerTest === 'pending' && (
                  <Button 
                    size="lg" 
                    className="w-full"
                    onClick={testSpeaker}
                  >
                    <Volume2 className="w-5 h-5 mr-2" />
                    Test Speakers
                  </Button>
                )}
                {speakerTest === 'testing' && (
                  <div className="flex items-center justify-center gap-2 text-accent">
                    <Loader2 className="w-6 h-6 animate-spin" />
                    <span className="font-medium">Playing audio...</span>
                  </div>
                )}
                {speakerTest === 'done' && (
                  <div className="flex items-center justify-center gap-2 text-success">
                    <CheckCircle2 className="w-6 h-6" />
                    <span className="font-medium">Speakers working!</span>
                  </div>
                )}
              </div>
            </>
          )}

          {step === 'complete' && (
            <div className="text-center py-4">
              <div className="flex items-center justify-center gap-2 text-success mb-4">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span className="text-sm">Launching assistant...</span>
              </div>
              <p className="text-sm text-muted-foreground">
                Say <span className="font-mono bg-muted px-1 rounded">"help"</span> anytime to see available commands
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
