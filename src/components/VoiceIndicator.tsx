import { Mic, MicOff, Volume2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface VoiceIndicatorProps {
  isListening: boolean;
  isSpeaking: boolean;
  className?: string;
}

export function VoiceIndicator({ isListening, isSpeaking, className }: VoiceIndicatorProps) {
  return (
    <div className={cn(
      "flex items-center gap-3 px-4 py-2 rounded-full transition-all duration-300",
      isListening && "bg-success/10 listening-glow",
      isSpeaking && "bg-accent/10 speaking-glow",
      !isListening && !isSpeaking && "bg-muted",
      className
    )}>
      {/* Voice Wave Animation */}
      <div className="flex items-center gap-0.5 h-6">
        {[0, 1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className={cn(
              "w-1 bg-current rounded-full transition-all duration-150",
              isListening && "bg-success voice-wave",
              isSpeaking && "bg-accent voice-wave",
              !isListening && !isSpeaking && "bg-muted-foreground h-2"
            )}
            style={{
              height: isListening || isSpeaking ? `${Math.random() * 16 + 8}px` : '8px',
              animationDelay: `${i * 0.1}s`,
            }}
          />
        ))}
      </div>

      {/* Status Icon */}
      {isSpeaking ? (
        <Volume2 className="w-5 h-5 text-accent animate-pulse" />
      ) : isListening ? (
        <Mic className="w-5 h-5 text-success" />
      ) : (
        <MicOff className="w-5 h-5 text-muted-foreground" />
      )}

      {/* Status Text */}
      <span className={cn(
        "text-sm font-medium",
        isListening && "text-success",
        isSpeaking && "text-accent",
        !isListening && !isSpeaking && "text-muted-foreground"
      )}>
        {isSpeaking ? 'Speaking...' : isListening ? 'Listening...' : 'Inactive'}
      </span>
    </div>
  );
}
