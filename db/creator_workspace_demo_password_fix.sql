SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Fix demo account password for existing local databases.
-- The backend auth helper stores "$2b$12$" + first 40 chars of sha256(password).
-- This value matches password: secret

UPDATE user_account
   SET password_hash = '$2b$12$2bb80d537b1da3e38bd30361aa855686bde0eacd',
       account_status = 'active'
 WHERE username = 'demo';
