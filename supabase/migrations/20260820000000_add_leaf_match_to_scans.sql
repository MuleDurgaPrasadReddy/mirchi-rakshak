ALTER TABLE public.scans
  ADD COLUMN IF NOT EXISTS is_chili_leaf BOOLEAN NOT NULL DEFAULT true,
  ADD COLUMN IF NOT EXISTS invalid_reason TEXT;

COMMENT ON COLUMN public.scans.is_chili_leaf IS 'Whether the uploaded image matches a chili leaf or fruit.';
COMMENT ON COLUMN public.scans.invalid_reason IS 'Why an uploaded image was rejected as not matching a chili crop.';