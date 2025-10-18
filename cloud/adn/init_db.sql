-- =====================================================
-- 🏥 ADN EMERGENCY MEDICAL SYSTEM DATABASE INIT SCRIPT
-- PostgreSQL 15 - Google Cloud SQL
-- Version simplifiée :
--   - urgency_level = INTEGER (1=P0, 2=P1, 3=P2, 4=P3)
--   - regulator_id uniquement dans emergency_interventions
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- =====================================================
-- ENUMERATIONS
-- =====================================================

-- Intervention statuses
DO $$ BEGIN
    CREATE TYPE intervention_status AS ENUM ('new', 'processing', 'dispatched', 'completed', 'cancelled');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Patient statuses
DO $$ BEGIN
    CREATE TYPE patient_status AS ENUM ('new', 'in_progress', 'transported', 'hospitalized', 'closed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Current handler types
DO $$ BEGIN
    CREATE TYPE handler_type AS ENUM ('waiting', 'pompiers', 'samu', 'ambulance_private', 'emergency_doctor', 'hospital_ward');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- User roles
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('admin', 'regulator', 'arm_operator', 'emergency_doctor', 'hospital_staff', 'smur_member', 'firefighter');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- =====================================================
-- TABLES
-- =====================================================

-- 🔐 USERS
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    role user_role NOT NULL DEFAULT 'arm_operator',
    is_active BOOLEAN DEFAULT TRUE
);

-- Regulators
CREATE TABLE IF NOT EXISTS regulators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE
);

-- ARM Operators
CREATE TABLE IF NOT EXISTS arm_operators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE
);

-- Hospitals
CREATE TABLE IF NOT EXISTS hospitals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255),
    address VARCHAR(500),
    phone VARCHAR(50)
);

-- Emergency Doctors
CREATE TABLE IF NOT EXISTS emergency_doctors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255),
    specialization VARCHAR(255)
);

-- Fire Stations
CREATE TABLE IF NOT EXISTS fire_stations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    address VARCHAR(500),
    phone VARCHAR(50),
    gps_latitude DECIMAL(10,8),
    gps_longitude DECIMAL(11,8)
);

-- SMUR Units
CREATE TABLE IF NOT EXISTS smur_units (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    hospital_id UUID REFERENCES hospitals(id) ON DELETE SET NULL,
    phone VARCHAR(50),
    vehicle_number VARCHAR(50),
    is_available BOOLEAN DEFAULT TRUE
);

-- Emergency Interventions
CREATE TABLE IF NOT EXISTS emergency_interventions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_datetime TIMESTAMP NOT NULL,
    caller_phone VARCHAR(20),
    transcript TEXT,
    audio_url VARCHAR(500),
    urgency_level INTEGER CHECK (urgency_level BETWEEN 1 AND 4),
    status intervention_status DEFAULT 'new',
    location_address VARCHAR(500),
    gps_latitude DECIMAL(10,8),
    gps_longitude DECIMAL(11,8),
    regulator_id UUID REFERENCES regulators(id) ON DELETE SET NULL,
    arm_operator_id UUID REFERENCES arm_operators(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Emergency Patients
CREATE TABLE IF NOT EXISTS emergency_patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    intervention_id UUID UNIQUE REFERENCES emergency_interventions(id) ON DELETE CASCADE,
    description TEXT,
    urgency_level INTEGER CHECK (urgency_level BETWEEN 1 AND 4),
    status patient_status DEFAULT 'new',
    current_location VARCHAR(500),
    current_handler handler_type DEFAULT 'waiting',
    handler_details JSON,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- INDEXES
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_patients_handler ON emergency_patients(current_handler);
CREATE INDEX IF NOT EXISTS idx_patients_status ON emergency_patients(status);
CREATE INDEX IF NOT EXISTS idx_interventions_regulator ON emergency_interventions(regulator_id);

-- =====================================================
-- END OF SCRIPT
-- =====================================================
