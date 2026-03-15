-- ============================================================
-- Trip Planner — Schema SQL para Supabase
-- Ejecutar en Supabase SQL Editor (Dashboard > SQL Editor)
-- ============================================================

-- Enums
CREATE TYPE trip_status AS ENUM ('en_planificacion', 'confirmado', 'en_curso', 'completado');
CREATE TYPE item_status AS ENUM ('confirmado', 'pendiente', 'sugerido');
CREATE TYPE item_type AS ENUM ('actividad', 'traslado', 'alojamiento', 'comida', 'vuelo', 'extra');
CREATE TYPE budget_category AS ENUM ('vuelos', 'alojamiento', 'actividades', 'comidas', 'transporte_local', 'extras');

-- Users (extiende auth.users de Supabase)
CREATE TABLE public.users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT UNIQUE NOT NULL,
  email TEXT NOT NULL,
  name TEXT NOT NULL DEFAULT '',
  picture TEXT DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_login TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_users_email ON public.users(email);
CREATE INDEX idx_users_user_id ON public.users(user_id);

-- Profiles
CREATE TABLE public.profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
  accommodation_types TEXT[] DEFAULT '{}',
  food_restrictions TEXT[] DEFAULT '{}',
  allergies TEXT DEFAULT '',
  travel_styles TEXT[] DEFAULT '{}',
  daily_budget NUMERIC(10,2) DEFAULT 0.0,
  preferred_airlines TEXT DEFAULT '',
  preferred_hotel_chains TEXT DEFAULT '',
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_profiles_user UNIQUE (user_id)
);

-- Trips
CREATE TABLE public.trips (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  destination TEXT NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  status trip_status NOT NULL DEFAULT 'en_planificacion',
  budget_total NUMERIC(12,2) DEFAULT 0.0,
  notes TEXT DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_dates CHECK (end_date >= start_date)
);
CREATE INDEX idx_trips_user_id ON public.trips(user_id);
CREATE INDEX idx_trips_status ON public.trips(status);

-- Itinerary Items
CREATE TABLE public.itinerary_items (
  id TEXT PRIMARY KEY,
  trip_id TEXT NOT NULL REFERENCES public.trips(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  item_type item_type NOT NULL DEFAULT 'actividad',
  day INTEGER NOT NULL CHECK (day >= 1),
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  status item_status NOT NULL DEFAULT 'pendiente',
  location TEXT DEFAULT '',
  address TEXT DEFAULT '',
  notes TEXT DEFAULT '',
  cost_estimated NUMERIC(10,2) DEFAULT 0.0,
  cost_real NUMERIC(10,2) DEFAULT 0.0,
  booking_url TEXT DEFAULT '',
  provider TEXT DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_items_trip_id ON public.itinerary_items(trip_id);
CREATE INDEX idx_items_day ON public.itinerary_items(trip_id, day);

-- Chats
CREATE TABLE public.chats (
  chat_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
  trip_id TEXT REFERENCES public.trips(id) ON DELETE SET NULL,
  title TEXT NOT NULL DEFAULT 'Nueva conversacion',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_activity_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_chats_user_id ON public.chats(user_id);

-- Chat Messages
CREATE TABLE public.chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chat_id TEXT NOT NULL REFERENCES public.chats(chat_id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  msg_type TEXT NOT NULL DEFAULT 'text',
  content JSONB NOT NULL,
  processed BOOLEAN DEFAULT FALSE,
  result TEXT DEFAULT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  sort_order INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_messages_chat_id ON public.chat_messages(chat_id);

-- Feedbacks
CREATE TABLE public.feedbacks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trip_id TEXT NOT NULL REFERENCES public.trips(id) ON DELETE CASCADE,
  overall_rating INTEGER NOT NULL CHECK (overall_rating BETWEEN 0 AND 5),
  comment TEXT DEFAULT '',
  item_feedbacks JSONB DEFAULT '[]',
  skipped BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_feedback_trip UNIQUE (trip_id)
);

-- Trigger: recalcular budget_total al modificar items
CREATE OR REPLACE FUNCTION recalculate_trip_budget()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE public.trips
  SET budget_total = COALESCE((
    SELECT SUM(cost_estimated)
    FROM public.itinerary_items
    WHERE trip_id = COALESCE(NEW.trip_id, OLD.trip_id)
      AND status != 'sugerido'
  ), 0),
  updated_at = now()
  WHERE id = COALESCE(NEW.trip_id, OLD.trip_id);
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER trg_recalc_budget
  AFTER INSERT OR UPDATE OR DELETE ON public.itinerary_items
  FOR EACH ROW
  EXECUTE FUNCTION recalculate_trip_budget();

-- RLS (habilitado, con politicas permisivas para service_role)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trips ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.itinerary_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.feedbacks ENABLE ROW LEVEL SECURITY;

-- Politicas permisivas (service_role bypasea RLS por defecto,
-- estas politicas son para acceso con anon key si se necesita en el futuro)
CREATE POLICY users_self ON public.users FOR ALL USING (true);
CREATE POLICY profiles_self ON public.profiles FOR ALL USING (true);
CREATE POLICY trips_self ON public.trips FOR ALL USING (true);
CREATE POLICY items_self ON public.itinerary_items FOR ALL USING (true);
CREATE POLICY chats_self ON public.chats FOR ALL USING (true);
CREATE POLICY messages_self ON public.chat_messages FOR ALL USING (true);
CREATE POLICY feedbacks_self ON public.feedbacks FOR ALL USING (true);
