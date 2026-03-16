-- Migracion REQ-CF-002: Soporte para items multi-dia
-- Ejecutar en Supabase SQL Editor ANTES de desplegar el codigo

ALTER TABLE public.itinerary_items
ADD COLUMN end_day INTEGER NULL;

ALTER TABLE public.itinerary_items
ADD CONSTRAINT chk_end_day CHECK (end_day IS NULL OR end_day >= day);

-- Verificar
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'itinerary_items' AND column_name = 'end_day';
