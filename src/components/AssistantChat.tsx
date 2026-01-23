import { useRef, useEffect } from 'react';
import { Bot, User, Mic, Volume2, Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}

interface AssistantChatProps {
  messages: ChatMessage[];
  isListening: boolean;
  isSpeaking: boolean;
  currentTranscript: string;
}

export function AssistantChat({ messages, isListening, isSpeaking, currentTranscript }: AssistantChatProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, currentTranscript]);

  return (
    <div className="flex flex-col h-full bg-card rounded-xl border overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b bg-gradient-to-r from-primary/5 to-accent/5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center">
            <Bot className="w-5 h-5 text-primary-foreground" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground">Swar</h3>
            <p className="text-xs text-muted-foreground">Voice Assistant</p>
          </div>
          <div className={cn(
            "ml-auto flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium",
            isListening && "bg-success/10 text-success",
            isSpeaking && "bg-accent/10 text-accent",
            !isListening && !isSpeaking && "bg-muted text-muted-foreground"
          )}>
            {isSpeaking ? (
              <>
                <Volume2 className="w-3 h-3 animate-pulse" />
                Speaking
              </>
            ) : isListening ? (
              <>
                <Mic className="w-3 h-3" />
                Listening
              </>
            ) : (
              'Ready'
            )}
          </div>
        </div>
      </div>

      <Separator />

      {/* Messages */}
      <ScrollArea className="flex-1" ref={scrollRef}>
        <div className="p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-8">
              <Info className="w-10 h-10 mx-auto text-muted-foreground mb-3" />
              <p className="text-sm text-muted-foreground">
                Start speaking to interact with your emails.
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                Try saying "help" for available commands
              </p>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex gap-3 animate-fade-in",
                message.role === 'user' && "flex-row-reverse"
              )}
            >
              <div className={cn(
                "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
                message.role === 'user' ? "bg-primary" : "bg-accent",
                message.role === 'system' && "bg-muted"
              )}>
                {message.role === 'user' ? (
                  <User className="w-4 h-4 text-primary-foreground" />
                ) : message.role === 'system' ? (
                  <Info className="w-4 h-4 text-muted-foreground" />
                ) : (
                  <Bot className="w-4 h-4 text-accent-foreground" />
                )}
              </div>
              
              <div className={cn(
                "flex-1 max-w-[85%] p-3 rounded-lg",
                message.role === 'user' 
                  ? "bg-primary text-primary-foreground" 
                  : message.role === 'system'
                  ? "bg-muted text-muted-foreground text-sm"
                  : "bg-secondary text-secondary-foreground"
              )}>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">
                  {message.content}
                </p>
                <span className="text-xs opacity-60 mt-1 block">
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            </div>
          ))}

          {/* Current transcript preview */}
          {currentTranscript && (
            <div className="flex gap-3 flex-row-reverse opacity-60 animate-fade-in">
              <div className="w-8 h-8 rounded-full bg-primary/50 flex items-center justify-center">
                <Mic className="w-4 h-4 text-primary-foreground animate-pulse" />
              </div>
              <div className="flex-1 max-w-[85%] p-3 rounded-lg bg-primary/10 border border-primary/20">
                <p className="text-sm text-foreground italic">
                  {currentTranscript}...
                </p>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Voice Input Status */}
      <div className="p-3 border-t bg-muted/30">
        <div className="flex items-center justify-center gap-2">
          {[0, 1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className={cn(
                "w-1 rounded-full transition-all duration-150",
                isListening ? "bg-success voice-wave" : "bg-muted-foreground/30 h-2"
              )}
              style={{
                height: isListening ? `${Math.random() * 16 + 8}px` : '8px',
                animationDelay: `${i * 0.1}s`,
              }}
            />
          ))}
          <span className="text-xs text-muted-foreground ml-2">
            {isListening ? 'Speak now...' : 'Say a command'}
          </span>
        </div>
      </div>
    </div>
  );
}
