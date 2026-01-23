import { useState, useEffect, useCallback, useRef } from 'react';

// Web Speech API types
interface SpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message: string;
}

interface SpeechRecognitionType extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onstart: ((this: SpeechRecognitionType, ev: Event) => void) | null;
  onend: ((this: SpeechRecognitionType, ev: Event) => void) | null;
  onresult: ((this: SpeechRecognitionType, ev: SpeechRecognitionEvent) => void) | null;
  onerror: ((this: SpeechRecognitionType, ev: SpeechRecognitionErrorEvent) => void) | null;
}

interface SpeechRecognitionConstructor {
  new(): SpeechRecognitionType;
}

interface UseSpeechRecognitionOptions {
  continuous?: boolean;
  interimResults?: boolean;
  language?: string;
  onResult?: (transcript: string, isFinal: boolean) => void;
  onError?: (error: string) => void;
}

interface SpeechRecognitionResult {
  isListening: boolean;
  transcript: string;
  interimTranscript: string;
  error: string | null;
  isSupported: boolean;
  startListening: () => void;
  stopListening: () => void;
  resetTranscript: () => void;
}

export function useSpeechRecognition(options: UseSpeechRecognitionOptions = {}): SpeechRecognitionResult {
  const {
    continuous = true,
    interimResults = true,
    language = 'en-US',
    onResult,
    onError,
  } = options;

  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);

  const recognitionRef = useRef<SpeechRecognitionType | null>(null);
  const isSupported = typeof window !== 'undefined' && 
    ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);

  useEffect(() => {
    if (!isSupported) return;

    const SpeechRecognitionAPI = (window.SpeechRecognition || window.webkitSpeechRecognition) as SpeechRecognitionConstructor;
    recognitionRef.current = new SpeechRecognitionAPI();
    recognitionRef.current = new SpeechRecognitionAPI();
    
    const recognition = recognitionRef.current;
    recognition.continuous = continuous;
    recognition.interimResults = interimResults;
    recognition.lang = language;

    recognition.onstart = () => {
      setIsListening(true);
      setError(null);
    };

    recognition.onend = () => {
      setIsListening(false);
      // Auto-restart if continuous mode
      if (continuous && recognitionRef.current) {
        try {
          recognitionRef.current.start();
        } catch (e) {
          // Already started or other error
        }
      }
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let finalTranscript = '';
      let interimText = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript;
        } else {
          interimText += result[0].transcript;
        }
      }

      if (finalTranscript) {
        setTranscript(prev => prev + ' ' + finalTranscript);
        onResult?.(finalTranscript.trim(), true);
      }
      
      setInterimTranscript(interimText);
      if (interimText) {
        onResult?.(interimText, false);
      }
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      const errorMessage = event.error === 'no-speech' 
        ? 'No speech detected' 
        : event.error === 'not-allowed'
        ? 'Microphone access denied'
        : `Speech recognition error: ${event.error}`;
      
      setError(errorMessage);
      onError?.(errorMessage);
      
      // Don't stop on no-speech errors in continuous mode
      if (event.error !== 'no-speech') {
        setIsListening(false);
      }
    };

    return () => {
      recognition.stop();
    };
  }, [continuous, interimResults, language, onResult, onError, isSupported]);

  const startListening = useCallback(() => {
    if (!recognitionRef.current || !isSupported) {
      setError('Speech recognition not supported');
      return;
    }
    
    try {
      recognitionRef.current.start();
    } catch (e) {
      // Already started
    }
  }, [isSupported]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  }, []);

  const resetTranscript = useCallback(() => {
    setTranscript('');
    setInterimTranscript('');
  }, []);

  return {
    isListening,
    transcript,
    interimTranscript,
    error,
    isSupported,
    startListening,
    stopListening,
    resetTranscript,
  };
}

// Extend Window interface for TypeScript
declare global {
  interface Window {
    SpeechRecognition: SpeechRecognitionConstructor;
    webkitSpeechRecognition: SpeechRecognitionConstructor;
  }
}
