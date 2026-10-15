-- Default system categories (user_id NULL). Also available via: python manage.py seed_defaults
INSERT INTO categories (id,user_id,name,kind,is_archived,created_at) VALUES (gen_random_uuid(),NULL,'Airtime & Data','expense',false,now());
INSERT INTO categories (id,user_id,name,kind,is_archived,created_at) VALUES (gen_random_uuid(),NULL,'Clothing','expense',false,now());
INSERT INTO categories (id,user_id,name,kind,is_archived,created_at) VALUES (gen_random_uuid(),NULL,'Education','expense',false,now());
INSERT INTO categories (id,user_id,name,kind,is_archived,created_at) VALUES (gen_random_uuid(),NULL,'Entertainment','expense',false,now());
INSERT INTO categories (id,user_id,name,kind,is_archived,created_at) VALUES (gen_random_uuid(),NULL,'Food','expense',false,now());
INSERT INTO categories (id,user_id,name,kind,is_archived,created_at) VALUES (gen_random_uuid(),NULL,'Health','expense',false,now());
INSERT INTO categories (id,user_id,name,kind,is_archived,created_at) VALUES (gen_random_uuid(),NULL,'Other expense','expense',false,now());
INSERT INTO categories (id,user_id,name,kind,is_archived,created_at) VALUES (gen_random_uuid(),NULL,'Rent','expense',false,now());
INSERT INTO categories (id,user_id,name,kind,is_archived,created_at) VALUES (gen_random_uuid(),NULL,'Savings','expense',false,now());
INSERT INTO categories (id,user_id,name,kind,is_archived,created_at) VALUES (gen_random_uuid(),NULL,'Transport','expense',false,now());
INSERT INTO categories (id,user_id,name,kind,is_archived,created_at) VALUES (gen_random_uuid(),NULL,'Utilities','expense',false,now());
INSERT INTO categories (id,user_id,name,kind,is_archived,created_at) VALUES (gen_random_uuid(),NULL,'Allowance','income',false,now());
INSERT INTO categories (id,user_id,name,kind,is_archived,created_at) VALUES (gen_random_uuid(),NULL,'Business','income',false,now());
INSERT INTO categories (id,user_id,name,kind,is_archived,created_at) VALUES (gen_random_uuid(),NULL,'Gifts','income',false,now());
INSERT INTO categories (id,user_id,name,kind,is_archived,created_at) VALUES (gen_random_uuid(),NULL,'Other income','income',false,now());
INSERT INTO categories (id,user_id,name,kind,is_archived,created_at) VALUES (gen_random_uuid(),NULL,'Salary','income',false,now());
