import { Star, Mail, MailOpen } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Email } from '@/hooks/useEmails';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { formatDistanceToNow } from 'date-fns';

interface EmailListProps {
  emails: Email[];
  selectedEmail: Email | null;
  onSelectEmail: (email: Email) => void;
  onToggleStar: (emailId: string) => void;
  isLoading: boolean;
}

export function EmailList({ emails, selectedEmail, onSelectEmail, onToggleStar, isLoading }: EmailListProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-muted-foreground">Loading emails...</p>
        </div>
      </div>
    );
  }

  if (emails.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <Mail className="w-12 h-12" />
          <p className="text-sm">No emails in this folder</p>
          <p className="text-xs">Say "open inbox" to check your inbox</p>
        </div>
      </div>
    );
  }

  return (
    <ScrollArea className="h-full">
      <div className="space-y-1 p-2">
        {emails.map((email, index) => (
          <div
            key={email.id}
            role="button"
            tabIndex={0}
            onClick={() => onSelectEmail(email)}
            onKeyDown={(e) => e.key === 'Enter' && onSelectEmail(email)}
            className={cn(
              "group flex items-start gap-3 p-4 rounded-lg cursor-pointer transition-all duration-200",
              "hover:bg-secondary/80 focus:outline-none focus:ring-2 focus:ring-primary/50",
              selectedEmail?.id === email.id && "bg-primary/5 border-l-4 border-primary",
              !email.is_read && "bg-primary/5"
            )}
          >
            {/* Email Number */}
            <div className={cn(
              "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold",
              !email.is_read ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
            )}>
              {index + 1}
            </div>

            {/* Email Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <span className={cn(
                  "text-sm truncate",
                  !email.is_read && "font-semibold"
                )}>
                  {email.sender}
                </span>
                <span className="text-xs text-muted-foreground flex-shrink-0">
                  {formatDistanceToNow(new Date(email.received_at), { addSuffix: true })}
                </span>
              </div>
              
              <p className={cn(
                "text-sm truncate mt-1",
                !email.is_read ? "font-medium text-foreground" : "text-muted-foreground"
              )}>
                {email.subject}
              </p>
              
              <p className="text-xs text-muted-foreground truncate mt-1">
                {email.snippet || email.body.substring(0, 80)}...
              </p>
            </div>

            {/* Actions */}
            <div className="flex flex-col items-center gap-2 flex-shrink-0">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onToggleStar(email.id);
                }}
                className="p-1 rounded hover:bg-accent/20 transition-colors"
              >
                <Star className={cn(
                  "w-4 h-4",
                  email.is_starred ? "fill-accent text-accent" : "text-muted-foreground"
                )} />
              </button>
              
              {!email.is_read ? (
                <Badge variant="secondary" className="text-xs px-1.5">New</Badge>
              ) : (
                <MailOpen className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
              )}
            </div>
          </div>
        ))}
      </div>
    </ScrollArea>
  );
}
