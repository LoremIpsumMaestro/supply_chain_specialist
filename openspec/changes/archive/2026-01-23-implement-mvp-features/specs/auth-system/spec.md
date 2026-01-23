# auth-system Specification

## Purpose
Provide complete user authentication and authorization system with JWT tokens, replacing the current mock authentication. Enable secure user registration, login, token refresh, and password management for production deployment.

## ADDED Requirements

### Requirement: User Registration
The system SHALL allow new users to create accounts with email and password.

#### Scenario: User registers with valid credentials
- **WHEN** a user submits POST /auth/register with:
  - `email`: "user@example.com"
  - `password`: "SecurePass123!"
  - `full_name`: "John Doe"
- **THEN** the email is validated (proper format, not already registered)
- **AND** the password is validated (min 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char)
- **AND** the password is hashed using bcrypt (cost factor 12)
- **AND** a user record is created in the users table
- **AND** the response includes:
  - `user`: {id, email, full_name, created_at}
  - `access_token`: JWT (15 min expiry)
  - `refresh_token`: JWT (7 days expiry)
- **AND** the HTTP status is 201 Created

#### Scenario: User registers with existing email
- **WHEN** a user attempts to register with an email already in the database
- **THEN** the request is rejected with 409 Conflict
- **AND** the error message is: "Un compte existe déjà avec cet email"
- **AND** no user record is created

#### Scenario: User registers with weak password
- **WHEN** a user submits a password like "password" (no uppercase, no digit, no special char)
- **THEN** the request is rejected with 422 Unprocessable Entity
- **AND** the error message explains password requirements
- **AND** no user record is created

#### Scenario: User registers with invalid email
- **WHEN** a user submits an invalid email format (e.g., "notanemail")
- **THEN** the request is rejected with 422 Unprocessable Entity
- **AND** the error message is: "Format d'email invalide"

### Requirement: User Login
The system SHALL authenticate users and issue JWT tokens for session management.

#### Scenario: User logs in with correct credentials
- **WHEN** a user submits POST /auth/login with:
  - `email`: "user@example.com"
  - `password`: "SecurePass123!"
- **THEN** the email is looked up in the users table
- **AND** the provided password is verified against the hashed password using bcrypt
- **AND** if credentials match, the response includes:
  - `user`: {id, email, full_name}
  - `access_token`: JWT (15 min expiry)
  - `refresh_token`: JWT (7 days expiry)
- **AND** the HTTP status is 200 OK

#### Scenario: User logs in with incorrect password
- **WHEN** a user submits correct email but wrong password
- **THEN** the request is rejected with 401 Unauthorized
- **AND** the error message is: "Email ou mot de passe incorrect" (generic for security)
- **AND** a failed login attempt is logged

#### Scenario: User logs in with non-existent email
- **WHEN** a user submits an email not in the database
- **THEN** the request is rejected with 401 Unauthorized
- **AND** the error message is: "Email ou mot de passe incorrect" (same as wrong password)
- **AND** a failed login attempt is logged

#### Scenario: User account is disabled
- **WHEN** a user's account has `is_active` = false
- **AND** the user attempts to log in
- **THEN** the request is rejected with 403 Forbidden
- **AND** the error message is: "Ce compte a été désactivé"

### Requirement: Token Management
The system SHALL issue JWT access and refresh tokens with appropriate expiry times.

#### Scenario: Access token contains user claims
- **WHEN** an access token is issued
- **THEN** the JWT payload includes:
  - `sub`: user_id (UUID)
  - `email`: user email
  - `exp`: expiration timestamp (15 minutes from issuance)
  - `type`: "access"
- **AND** the token is signed with a secret key (from environment variable)

#### Scenario: Refresh token contains minimal claims
- **WHEN** a refresh token is issued
- **THEN** the JWT payload includes:
  - `sub`: user_id (UUID)
  - `exp`: expiration timestamp (7 days from issuance)
  - `type`: "refresh"
- **AND** the token is signed with the same secret key

#### Scenario: Access token used to authenticate API requests
- **WHEN** a user makes a request to a protected endpoint (e.g., GET /api/conversations)
- **AND** includes `Authorization: Bearer <access_token>` header
- **THEN** the token is validated (signature, expiration)
- **AND** the user_id is extracted from the `sub` claim
- **AND** the request proceeds with user context

#### Scenario: Expired access token rejected
- **WHEN** a user makes a request with an expired access token (> 15 min old)
- **THEN** the request is rejected with 401 Unauthorized
- **AND** the error message is: "Token expiré"
- **AND** the response includes `WWW-Authenticate: Bearer error="invalid_token"`

#### Scenario: Invalid token signature rejected
- **WHEN** a user makes a request with a tampered token
- **THEN** the request is rejected with 401 Unauthorized
- **AND** the error message is: "Token invalide"

### Requirement: Token Refresh
The system SHALL allow users to obtain new access tokens using refresh tokens without re-entering credentials.

#### Scenario: User refreshes access token
- **WHEN** a user submits POST /auth/refresh with:
  - `refresh_token`: valid refresh token
- **THEN** the refresh token is validated (signature, expiration, type="refresh")
- **AND** a new access token is issued with fresh 15-minute expiry
- **AND** the response includes:
  - `access_token`: new JWT
  - `token_type`: "bearer"
- **AND** the HTTP status is 200 OK
- **AND** the refresh token remains valid (not rotated in MVP)

#### Scenario: Expired refresh token rejected
- **WHEN** a user submits an expired refresh token (> 7 days old)
- **THEN** the request is rejected with 401 Unauthorized
- **AND** the error message is: "Refresh token expiré - veuillez vous reconnecter"
- **AND** the user must log in again to obtain new tokens

#### Scenario: Access token used as refresh token
- **WHEN** a user mistakenly submits an access token to /auth/refresh
- **THEN** the request is rejected with 400 Bad Request
- **AND** the error message is: "Token de type invalide - refresh token requis"

### Requirement: Password Security
The system SHALL enforce strong password policies and use industry-standard hashing.

#### Scenario: Password hashed with bcrypt
- **WHEN** a user registers or changes password
- **THEN** the password is hashed using bcrypt with cost factor 12
- **AND** the plaintext password is never stored in the database
- **AND** each password has a unique salt (bcrypt automatic)

#### Scenario: Password complexity validation
- **WHEN** a password is submitted during registration or change
- **THEN** it is validated for:
  - Minimum 8 characters
  - At least 1 uppercase letter
  - At least 1 lowercase letter
  - At least 1 digit
  - At least 1 special character (!@#$%^&*(),.?":{}|<>)
- **AND** if validation fails, detailed requirements are returned

#### Scenario: Common password rejected
- **WHEN** a user submits a password like "Password123!"
- **THEN** it passes complexity validation (MVP)
- **AND** (V1 enhancement) the password is checked against a common password list and rejected if found

### Requirement: Rate Limiting for Authentication
The system SHALL prevent brute-force attacks by limiting login attempts.

#### Scenario: User within login rate limit
- **WHEN** a user attempts 4 logins within 1 minute
- **THEN** all attempts are processed normally

#### Scenario: User exceeds login rate limit
- **WHEN** a user attempts 6 logins within 1 minute
- **THEN** the 6th attempt is rejected with 429 Too Many Requests
- **AND** the error message is: "Trop de tentatives de connexion - réessayez dans 60 secondes"
- **AND** the response includes `Retry-After: 60` header

#### Scenario: Rate limit resets after time window
- **WHEN** 60 seconds have elapsed since the first login attempt
- **THEN** the rate limit counter resets
- **AND** the user can attempt login again

#### Scenario: Rate limit per IP address
- **WHEN** multiple users attempt login from the same IP
- **THEN** the rate limit is applied per IP address (not per email)
- **AND** this prevents account enumeration attacks

### Requirement: User Session Management
The system SHALL allow users to log out and invalidate tokens (token blacklist for V1, client-side deletion for MVP).

#### Scenario: User logs out (MVP - client-side)
- **WHEN** a user clicks logout in the UI
- **THEN** the access_token and refresh_token are deleted from client storage (localStorage)
- **AND** the user is redirected to the login page
- **AND** subsequent API requests fail with 401 (no token)
- **AND** (MVP) tokens remain valid server-side until expiry

#### Scenario: User logs out (V1 - server-side invalidation)
- **WHEN** a user submits POST /auth/logout with refresh_token
- **THEN** the refresh_token is added to a blacklist (Redis)
- **AND** future attempts to use that token return 401
- **AND** the access_token expires naturally after 15 min

### Requirement: Protected Route Middleware
The system SHALL provide middleware to protect API endpoints requiring authentication.

#### Scenario: Protected endpoint requires valid token
- **WHEN** an endpoint is decorated with @require_auth middleware
- **AND** a request is made without Authorization header
- **THEN** the request is rejected with 401 Unauthorized
- **AND** the error message is: "Authentication requise"

#### Scenario: Endpoint extracts user_id from token
- **WHEN** a protected endpoint is accessed with valid token
- **THEN** the user_id is extracted from the token and available in the request context
- **AND** the endpoint can use user_id for database queries (e.g., filtering conversations)

#### Scenario: Optional authentication middleware
- **WHEN** an endpoint is decorated with @optional_auth
- **AND** a request is made without Authorization header
- **THEN** the request proceeds with user_id = None
- **AND** the endpoint can provide different behavior for authenticated vs anonymous users

### Requirement: Frontend Authentication Flow
The system SHALL provide React components and store logic for authentication UI.

#### Scenario: User visits login page
- **WHEN** a user navigates to /login
- **THEN** a login form is displayed with fields:
  - Email (text input)
  - Password (password input)
  - "Se connecter" button
  - "Créer un compte" link (redirects to /register)

#### Scenario: User submits login form
- **WHEN** a user enters email and password and clicks "Se connecter"
- **THEN** a POST request is made to /auth/login
- **AND** if successful, access_token and refresh_token are stored in localStorage
- **AND** user info is stored in authStore (Zustand)
- **AND** user is redirected to /chat

#### Scenario: User visits register page
- **WHEN** a user navigates to /register
- **THEN** a registration form is displayed with fields:
  - Email
  - Password
  - Confirm Password
  - Full Name (optional)
  - "Créer un compte" button
  - "Déjà un compte? Se connecter" link

#### Scenario: Token auto-refresh on expiry
- **WHEN** an API request returns 401 with error "Token expiré"
- **THEN** the frontend automatically calls /auth/refresh with refresh_token
- **AND** if successful, the new access_token is stored
- **AND** the original API request is retried with the new token
- **AND** this is handled by an Axios interceptor

#### Scenario: Refresh token expired - force re-login
- **WHEN** /auth/refresh returns 401 (refresh token expired)
- **THEN** the user is logged out (tokens deleted)
- **AND** user is redirected to /login
- **AND** a message is displayed: "Votre session a expiré - veuillez vous reconnecter"

### Requirement: User Profile Management (V1 Preview)
The system SHALL allow users to view and update their profile information in future versions.

#### Scenario: User views profile (V1)
- **WHEN** a user navigates to /profile
- **THEN** their email, full_name, and created_at are displayed
- **AND** an "Edit" button allows profile updates

#### Scenario: User changes password (V1)
- **WHEN** a user submits POST /auth/change-password with:
  - `current_password`
  - `new_password`
- **THEN** current password is verified
- **AND** new password is validated and hashed
- **AND** password is updated in the database
- **AND** all existing refresh tokens are invalidated (force re-login on all devices)
