--
-- PostgreSQL database dump
--

\restrict bvIJxhztQSq4kg28kubUWlioNpunh7DPoAnz3a2yhXw1VUwQkQ4wGgDwpqWzhJY

-- Dumped from database version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: budgets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.budgets (
    id uuid NOT NULL,
    period_type character varying(7) NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    limit_amount numeric(12,2) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    user_id uuid NOT NULL,
    category_id uuid NOT NULL,
    CONSTRAINT budget_end_not_before_start CHECK ((end_date >= start_date)),
    CONSTRAINT budget_limit_positive CHECK ((limit_amount > (0)::numeric)),
    CONSTRAINT budget_period_valid CHECK (((period_type)::text = ANY ((ARRAY['weekly'::character varying, 'monthly'::character varying, 'custom'::character varying])::text[])))
);


--
-- Name: categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.categories (
    id uuid NOT NULL,
    name character varying(80) NOT NULL,
    kind character varying(7) NOT NULL,
    is_archived boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    user_id uuid,
    CONSTRAINT category_kind_valid CHECK (((kind)::text = ANY ((ARRAY['income'::character varying, 'expense'::character varying, 'both'::character varying])::text[])))
);


--
-- Name: goal_contributions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.goal_contributions (
    id uuid NOT NULL,
    amount numeric(12,2) NOT NULL,
    contribution_date date NOT NULL,
    note text,
    created_at timestamp with time zone NOT NULL,
    user_id uuid NOT NULL,
    goal_id uuid NOT NULL,
    CONSTRAINT contribution_amount_positive CHECK ((amount > (0)::numeric))
);


--
-- Name: savings_goals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.savings_goals (
    id uuid NOT NULL,
    name character varying(120) NOT NULL,
    target_amount numeric(12,2) NOT NULL,
    target_date date,
    status character varying(9) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    user_id uuid NOT NULL,
    CONSTRAINT goal_status_valid CHECK (((status)::text = ANY ((ARRAY['active'::character varying, 'paused'::character varying, 'completed'::character varying, 'archived'::character varying])::text[]))),
    CONSTRAINT goal_target_positive CHECK ((target_amount > (0)::numeric))
);


--
-- Name: transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transactions (
    id uuid NOT NULL,
    type character varying(7) NOT NULL,
    amount numeric(12,2) NOT NULL,
    transaction_date date NOT NULL,
    note text,
    created_at timestamp with time zone NOT NULL,
    category_id uuid NOT NULL,
    user_id uuid NOT NULL,
    CONSTRAINT transaction_amount_positive CHECK ((amount > (0)::numeric)),
    CONSTRAINT transaction_type_valid CHECK (((type)::text = ANY ((ARRAY['income'::character varying, 'expense'::character varying])::text[])))
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    password character varying(128) NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean NOT NULL,
    id uuid NOT NULL,
    email character varying(254) NOT NULL,
    full_name character varying(150) NOT NULL,
    currency character varying(3) NOT NULL,
    is_active boolean NOT NULL,
    is_staff boolean NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: budgets budget_no_overlap; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budgets
    ADD CONSTRAINT budget_no_overlap EXCLUDE USING gist (user_id WITH =, category_id WITH =, daterange(start_date, end_date, '[]'::text) WITH &&);


--
-- Name: budgets budgets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budgets
    ADD CONSTRAINT budgets_pkey PRIMARY KEY (id);


--
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (id);


--
-- Name: goal_contributions goal_contributions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.goal_contributions
    ADD CONSTRAINT goal_contributions_pkey PRIMARY KEY (id);


--
-- Name: savings_goals savings_goals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.savings_goals
    ADD CONSTRAINT savings_goals_pkey PRIMARY KEY (id);


--
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (id);


--
-- Name: savings_goals uniq_goal_id_user; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.savings_goals
    ADD CONSTRAINT uniq_goal_id_user UNIQUE (id, user_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: budgets_category_id_328a159f; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX budgets_category_id_328a159f ON public.budgets USING btree (category_id);


--
-- Name: budgets_user_id_d4bb9f71; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX budgets_user_id_d4bb9f71 ON public.budgets USING btree (user_id);


--
-- Name: categories_user_id_4315f8c7; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX categories_user_id_4315f8c7 ON public.categories USING btree (user_id);


--
-- Name: goal_contributions_goal_id_778ade21; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX goal_contributions_goal_id_778ade21 ON public.goal_contributions USING btree (goal_id);


--
-- Name: goal_contributions_user_id_f55b51fd; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX goal_contributions_user_id_f55b51fd ON public.goal_contributions USING btree (user_id);


--
-- Name: idx_budget_user_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_budget_user_period ON public.budgets USING btree (user_id, start_date, end_date);


--
-- Name: idx_category_user_kind; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_category_user_kind ON public.categories USING btree (user_id, kind);


--
-- Name: idx_contrib_goal_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_contrib_goal_date ON public.goal_contributions USING btree (goal_id, contribution_date);


--
-- Name: idx_contrib_user_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_contrib_user_date ON public.goal_contributions USING btree (user_id, contribution_date);


--
-- Name: idx_goal_user_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_goal_user_status ON public.savings_goals USING btree (user_id, status);


--
-- Name: idx_txn_user_cat_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_txn_user_cat_date ON public.transactions USING btree (user_id, category_id, transaction_date);


--
-- Name: idx_txn_user_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_txn_user_date ON public.transactions USING btree (user_id, transaction_date DESC);


--
-- Name: idx_txn_user_type_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_txn_user_type_date ON public.transactions USING btree (user_id, type, transaction_date);


--
-- Name: savings_goals_user_id_709c52cc; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX savings_goals_user_id_709c52cc ON public.savings_goals USING btree (user_id);


--
-- Name: transactions_category_id_65740af9; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX transactions_category_id_65740af9 ON public.transactions USING btree (category_id);


--
-- Name: transactions_user_id_766cc893; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX transactions_user_id_766cc893 ON public.transactions USING btree (user_id);


--
-- Name: uniq_category_system_name_kind; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uniq_category_system_name_kind ON public.categories USING btree (lower((name)::text), kind) WHERE (user_id IS NULL);


--
-- Name: uniq_category_user_name_kind; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uniq_category_user_name_kind ON public.categories USING btree (lower((name)::text), kind, user_id) WHERE (user_id IS NOT NULL);


--
-- Name: uniq_user_email_ci; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uniq_user_email_ci ON public.users USING btree (lower((email)::text));


--
-- Name: users_email_0ea73cca_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX users_email_0ea73cca_like ON public.users USING btree (email varchar_pattern_ops);


--
-- Name: budgets budgets_category_id_328a159f_fk_categories_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budgets
    ADD CONSTRAINT budgets_category_id_328a159f_fk_categories_id FOREIGN KEY (category_id) REFERENCES public.categories(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: budgets budgets_user_id_d4bb9f71_fk_users_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budgets
    ADD CONSTRAINT budgets_user_id_d4bb9f71_fk_users_id FOREIGN KEY (user_id) REFERENCES public.users(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: categories categories_user_id_4315f8c7_fk_users_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_user_id_4315f8c7_fk_users_id FOREIGN KEY (user_id) REFERENCES public.users(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: goal_contributions fk_contribution_goal_same_owner; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.goal_contributions
    ADD CONSTRAINT fk_contribution_goal_same_owner FOREIGN KEY (goal_id, user_id) REFERENCES public.savings_goals(id, user_id) ON DELETE CASCADE;


--
-- Name: goal_contributions goal_contributions_goal_id_778ade21_fk_savings_goals_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.goal_contributions
    ADD CONSTRAINT goal_contributions_goal_id_778ade21_fk_savings_goals_id FOREIGN KEY (goal_id) REFERENCES public.savings_goals(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: goal_contributions goal_contributions_user_id_f55b51fd_fk_users_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.goal_contributions
    ADD CONSTRAINT goal_contributions_user_id_f55b51fd_fk_users_id FOREIGN KEY (user_id) REFERENCES public.users(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: savings_goals savings_goals_user_id_709c52cc_fk_users_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.savings_goals
    ADD CONSTRAINT savings_goals_user_id_709c52cc_fk_users_id FOREIGN KEY (user_id) REFERENCES public.users(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: transactions transactions_category_id_65740af9_fk_categories_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_category_id_65740af9_fk_categories_id FOREIGN KEY (category_id) REFERENCES public.categories(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: transactions transactions_user_id_766cc893_fk_users_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_user_id_766cc893_fk_users_id FOREIGN KEY (user_id) REFERENCES public.users(id) DEFERRABLE INITIALLY DEFERRED;


--
-- PostgreSQL database dump complete
--

\unrestrict bvIJxhztQSq4kg28kubUWlioNpunh7DPoAnz3a2yhXw1VUwQkQ4wGgDwpqWzhJY

