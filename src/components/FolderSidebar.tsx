import { Inbox, Send, FileEdit, Trash2, Star, Mail } from 'lucide-react';
import { cn } from '@/lib/utils';
import { EmailFolder } from '@/hooks/useEmails';
import { Badge } from '@/components/ui/badge';

interface FolderSidebarProps {
  currentFolder: EmailFolder;
  unreadCount: number;
  onFolderChange: (folder: EmailFolder) => void;
}

const folders: { id: EmailFolder; label: string; icon: React.ElementType; voiceCommand: string }[] = [
  { id: 'inbox', label: 'Inbox', icon: Inbox, voiceCommand: '"open inbox"' },
  { id: 'sent', label: 'Sent', icon: Send, voiceCommand: '"open sent"' },
  { id: 'drafts', label: 'Drafts', icon: FileEdit, voiceCommand: '"open drafts"' },
  { id: 'starred', label: 'Starred', icon: Star, voiceCommand: '"open starred"' },
  { id: 'trash', label: 'Trash', icon: Trash2, voiceCommand: '"open trash"' },
];

export function FolderSidebar({ currentFolder, unreadCount, onFolderChange }: FolderSidebarProps) {
  return (
    <div className="flex flex-col h-full bg-sidebar text-sidebar-foreground">
      {/* Logo */}
      <div className="p-4 border-b border-sidebar-border">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center">
            <Mail className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-lg">VoiceMail</h1>
            <p className="text-xs text-sidebar-foreground/60">Hands-free email</p>
          </div>
        </div>
      </div>

      {/* Folders */}
      <nav className="flex-1 p-3 space-y-1">
        {folders.map((folder) => {
          const Icon = folder.icon;
          const isActive = currentFolder === folder.id;
          
          return (
            <button
              key={folder.id}
              onClick={() => onFolderChange(folder.id)}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200",
                "hover:bg-sidebar-accent focus:outline-none focus:ring-2 focus:ring-sidebar-ring",
                isActive && "bg-sidebar-primary text-sidebar-primary-foreground"
              )}
            >
              <Icon className={cn(
                "w-5 h-5",
                isActive ? "text-sidebar-primary-foreground" : "text-sidebar-foreground/70"
              )} />
              <span className={cn(
                "font-medium flex-1 text-left",
                isActive ? "text-sidebar-primary-foreground" : "text-sidebar-foreground"
              )}>
                {folder.label}
              </span>
              {folder.id === 'inbox' && unreadCount > 0 && (
                <Badge 
                  variant="secondary" 
                  className={cn(
                    "text-xs",
                    isActive ? "bg-white/20 text-white" : "bg-primary/10 text-primary"
                  )}
                >
                  {unreadCount}
                </Badge>
              )}
            </button>
          );
        })}
      </nav>

      {/* Voice Commands Help */}
      <div className="p-4 border-t border-sidebar-border">
        <p className="text-xs text-sidebar-foreground/50 mb-2">Voice Commands:</p>
        <div className="space-y-1">
          {folders.slice(0, 3).map((folder) => (
            <p key={folder.id} className="text-xs text-sidebar-foreground/70 font-mono">
              {folder.voiceCommand}
            </p>
          ))}
        </div>
      </div>
    </div>
  );
}
