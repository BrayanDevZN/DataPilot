ALTER TABLE users ADD COLUMN IF NOT EXISTS public_id UUID DEFAULT gen_random_uuid();
ALTER TABLE users ALTER COLUMN public_id SET DEFAULT gen_random_uuid();
UPDATE users SET public_id = gen_random_uuid() WHERE public_id IS NULL;
ALTER TABLE users ALTER COLUMN public_id SET NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS users_public_id_unique ON users (public_id);

ALTER TABLE dashboards ADD COLUMN IF NOT EXISTS public_id UUID DEFAULT gen_random_uuid();
ALTER TABLE dashboards ALTER COLUMN public_id SET DEFAULT gen_random_uuid();
UPDATE dashboards SET public_id = gen_random_uuid() WHERE public_id IS NULL;
ALTER TABLE dashboards ALTER COLUMN public_id SET NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS dashboards_public_id_unique ON dashboards (public_id);
