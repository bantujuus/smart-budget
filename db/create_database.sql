-- Run once as a PostgreSQL superuser:  psql -U postgres -f db/create_database.sql
-- Change the password first, and put the same value in .env (DB_PASSWORD).
CREATE ROLE smartbudget_app LOGIN PASSWORD 'qwerty@123' CREATEDB;
CREATE DATABASE smartbudget OWNER smartbudget_app ENCODING 'UTF8';
\c smartbudget
CREATE EXTENSION IF NOT EXISTS btree_gist;  -- needed for the budget overlap constraint
