import { Mail, Star, Trash2, Reply, Clock, User } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Email } from '@/hooks/useEmails';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { format } from 'date-fns';

interface EmailViewerProps {
  email: Email | null;
  onToggleStar: (emailId: string) => void;
  onDelete: (emailId: string) => void;
  onReply: () => void;
}

export function EmailViewer({ email, onToggleStar, onDelete, onReply }: EmailViewerProps) {
  if (!email) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex flex-col items-center gap-4 text-muted-foreground">
          <div className="w-20 h-20 rounded-full bg-muted flex items-center justify-center">
            <Mail className="w-10 h-10" />
          </div>
          <div className="text-center">
            <p className="text-lg font-medium">Select an email to read</p>
            <p className="text-sm mt-1">Say "read email 1" to open the first email</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b bg-card">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <h2 className="text-xl font-semibold text-foreground leading-tight">
              {email.subject}
            </h2>
            <div className="flex items-center gap-2 mt-2 text-sm text-muted-foreground">
              <User className="w-4 h-4" />
              <span className="font-medium text-foreground">{email.sender}</span>
              {email.sender_email && (
                <span className="text-xs">({email.sender_email})</span>
              )}
            </div>
            <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
              <Clock className="w-3 h-3" />
              <span>{format(new Date(email.received_at), 'PPpp')}</span>
            </div>
          </div>
          
          {/* Actions */}
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => onToggleStar(email.id)}
              className="hover:bg-accent/20"
            >
              <Star className={cn(
                "w-5 h-5",
                email.is_starred ? "fill-accent text-accent" : "text-muted-foreground"
              )} />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={onReply}
              className="hover:bg-primary/10 text-primary"
            >
              <Reply className="w-5 h-5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => onDelete(email.id)}
              className="hover:bg-destructive/10 text-destructive"
            >
              <Trash2 className="w-5 h-5" />
            </Button>
          </div>
        </div>
      </div>

      <Separator />

      {/* Body */}
      <ScrollArea className="flex-1 p-6">
        <div className="prose prose-sm max-w-none">
          {email.body.split('\n').map((paragraph, idx) => (
            <p key={idx} className="text-foreground leading-relaxed mb-4">
              {paragraph}
            </p>
          ))}
        </div>
      </ScrollArea>

      {/* Footer Actions */}
      <div className="p-4 border-t bg-muted/30">
        <p className="text-sm text-muted-foreground text-center">
          💡 Say <span className="font-mono bg-muted px-1 rounded">"reply"</span> to respond, 
          <span className="font-mono bg-muted px-1 rounded ml-1">"summarize"</span> for a summary, or 
          <span className="font-mono bg-muted px-1 rounded ml-1">"delete"</span> to remove
        </p>
      </div>
    </div>
  );
}
