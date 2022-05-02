-- Dumped from database version 9.6.3
-- Dumped by pg_dump version 9.6.3

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

CREATE USER TPFINAL WITH PASSWORD 'TPFINAL';
CREATE DATABASE TPFINAL;
GRANT ALL PRIVILEGES ON DATABASE TPFINAL TO TPFINAL;
     
CREATE DATABASE TPFINAL;
 
\connect TPFINAL

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

CREATE SCHEMA "tp_final";
ALTER SCHEMA "tp_final" OWNER TO TPFINAL;
