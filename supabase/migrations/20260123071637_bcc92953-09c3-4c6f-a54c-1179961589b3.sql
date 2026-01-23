-- Create table for user profiles with voice PIN
CREATE TABLE public.profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL UNIQUE,
  full_name TEXT,
  email TEXT,
  voice_pin_hash TEXT,
  face_encoding TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

-- Enable RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Users can view their own profile
CREATE POLICY "Users can view own profile"
ON public.profiles FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile"
ON public.profiles FOR UPDATE
TO authenticated
USING (auth.uid() = user_id);

-- Users can insert their own profile
CREATE POLICY "Users can insert own profile"
ON public.profiles FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

-- Create email cache table for demo emails
CREATE TABLE public.emails (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  folder TEXT NOT NULL DEFAULT 'inbox',
  sender TEXT NOT NULL,
  sender_email TEXT,
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  snippet TEXT,
  is_read BOOLEAN DEFAULT false,
  is_starred BOOLEAN DEFAULT false,
  received_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

-- Enable RLS on emails
ALTER TABLE public.emails ENABLE ROW LEVEL SECURITY;

-- Users can view their own emails
CREATE POLICY "Users can view own emails"
ON public.emails FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- Users can update their own emails
CREATE POLICY "Users can update own emails"
ON public.emails FOR UPDATE
TO authenticated
USING (auth.uid() = user_id);

-- Users can insert their own emails
CREATE POLICY "Users can insert own emails"
ON public.emails FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

-- Users can delete their own emails
CREATE POLICY "Users can delete own emails"
ON public.emails FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

-- Create function to update timestamps
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = public;

-- Create trigger for profiles
CREATE TRIGGER update_profiles_updated_at
BEFORE UPDATE ON public.profiles
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at_column();

-- Create indexes for better performance
CREATE INDEX idx_emails_user_folder ON public.emails(user_id, folder);
CREATE INDEX idx_emails_is_read ON public.emails(user_id, is_read);