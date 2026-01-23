import { useCallback, useEffect, useRef } from 'react';
import { useSpeechRecognition } from './useSpeechRecognition';
import { useSpeechSynthesis } from './useSpeechSynthesis';

export type VoiceCommand = {
  patterns: string[];
  action: (match: string, params?: string[]) => void;
  description: string;
};

interface UseVoiceCommandsOptions {
  commands: VoiceCommand[];
  onUnrecognized?: (transcript: string) => void;
  autoStart?: boolean;
  confirmationRequired?: boolean;
}

interface UseVoiceCommandsResult {
  isListening: boolean;
  isSpeaking: boolean;
  lastCommand: string | null;
  lastTranscript: string;
  error: string | null;
  isSupported: boolean;
  startListening: () => void;
  stopListening: () => void;
  speak: (text: string) => void;
  cancelSpeech: () => void;
}

// Normalize spoken digits to numbers
function normalizeSpokenNumbers(text: string): string {
  const numberMap: Record<string, string> = {
    'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
    'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
    'ten': '10', 'eleven': '11', 'twelve': '12', 'thirteen': '13',
    'fourteen': '14', 'fifteen': '15', 'sixteen': '16', 'seventeen': '17',
    'eighteen': '18', 'nineteen': '19', 'twenty': '20',
  };

  let normalized = text.toLowerCase();
  Object.entries(numberMap).forEach(([word, digit]) => {
    normalized = normalized.replace(new RegExp(`\\b${word}\\b`, 'gi'), digit);
  });
  
  return normalized;
}

// Normalize email addresses spoken aloud
export function normalizeSpokenEmail(text: string): string {
  return text
    .toLowerCase()
    .replace(/\s+at\s+/g, '@')
    .replace(/\s+dot\s+/g, '.')
    .replace(/\s+/g, '')
    .trim();
}

export function useVoiceCommands(options: UseVoiceCommandsOptions): UseVoiceCommandsResult {
  const { commands, onUnrecognized, autoStart = false } = options;
  
  const lastCommandRef = useRef<string | null>(null);
  const lastTranscriptRef = useRef<string>('');

  const handleResult = useCallback((transcript: string, isFinal: boolean) => {
    if (!isFinal) {
      lastTranscriptRef.current = transcript;
      return;
    }

    const normalizedText = normalizeSpokenNumbers(transcript.toLowerCase().trim());
    lastTranscriptRef.current = normalizedText;

    // Try to match a command
    for (const command of commands) {
      for (const pattern of command.patterns) {
        const regex = new RegExp(pattern, 'i');
        const match = normalizedText.match(regex);
        
        if (match) {
          lastCommandRef.current = pattern;
          command.action(normalizedText, match.slice(1));
          return;
        }
      }
    }

    // No command matched
    onUnrecognized?.(normalizedText);
  }, [commands, onUnrecognized]);

  const {
    isListening,
    error,
    isSupported: sttSupported,
    startListening,
    stopListening,
  } = useSpeechRecognition({
    continuous: true,
    interimResults: true,
    onResult: handleResult,
  });

  const {
    isSpeaking,
    isSupported: ttsSupported,
    speak,
    cancel: cancelSpeech,
  } = useSpeechSynthesis({
    rate: 1.0,
    pitch: 1.0,
  });

  // Auto-start if requested
  useEffect(() => {
    if (autoStart && sttSupported) {
      startListening();
    }
  }, [autoStart, sttSupported, startListening]);

  return {
    isListening,
    isSpeaking,
    lastCommand: lastCommandRef.current,
    lastTranscript: lastTranscriptRef.current,
    error,
    isSupported: sttSupported && ttsSupported,
    startListening,
    stopListening,
    speak,
    cancelSpeech,
  };
}
