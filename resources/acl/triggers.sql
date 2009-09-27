-- Foreign Key Preventing insert
CREATE TRIGGER IF NOT EXISTS fki_acl_user_hostmasks_aro_name_acl_aro_name
BEFORE INSERT ON [acl_user_hostmasks]
FOR EACH ROW BEGIN
  SELECT RAISE(ROLLBACK, 'insert on table "acl_user_hostmasks" violates foreign key constraint "fki_acl_user_hostmasks_aro_name_acl_aro_name"')
  WHERE NEW.aro_name IS NOT NULL AND (SELECT name FROM acl_aro WHERE name = NEW.aro_name) IS NULL;
END;

-- Foreign key preventing update
CREATE TRIGGER IF NOT EXISTS fku_acl_user_hostmasks_aro_name_acl_aro_name
BEFORE UPDATE ON [acl_user_hostmasks]
FOR EACH ROW BEGIN
    SELECT RAISE(ROLLBACK, 'update on table "acl_user_hostmasks" violates foreign key constraint "fku_acl_user_hostmasks_aro_name_acl_aro_name"')
      WHERE NEW.aro_name IS NOT NULL AND (SELECT name FROM acl_aro WHERE name = NEW.aro_name) IS NULL;
END;

-- Cascading Delete
CREATE TRIGGER IF NOT EXISTS fkdc_acl_user_hostmasks_aro_name_acl_aro_name
BEFORE DELETE ON acl_aro
FOR EACH ROW BEGIN
    DELETE FROM acl_user_hostmasks WHERE acl_user_hostmasks.aro_name = OLD.name;
END;

-- Foreign Key Preventing insert
CREATE TRIGGER IF NOT EXISTS fki_acl_memberships_aro_name_1_acl_aro_name
BEFORE INSERT ON [acl_memberships]
FOR EACH ROW BEGIN
  SELECT RAISE(ROLLBACK, 'insert on table "acl_memberships" violates foreign key constraint "fki_acl_memberships_aro_name_1_acl_aro_name"')
  WHERE NEW.aro_name_1 IS NOT NULL AND (SELECT name FROM acl_aro WHERE name = NEW.aro_name_1) IS NULL;
END;

-- Foreign key preventing update
CREATE TRIGGER IF NOT EXISTS fku_acl_memberships_aro_name_1_acl_aro_name
BEFORE UPDATE ON [acl_memberships]
FOR EACH ROW BEGIN
    SELECT RAISE(ROLLBACK, 'update on table "acl_memberships" violates foreign key constraint "fku_acl_memberships_aro_name_1_acl_aro_name"')
      WHERE NEW.aro_name_1 IS NOT NULL AND (SELECT name FROM acl_aro WHERE name = NEW.aro_name_1) IS NULL;
END;

-- Cascading Delete
CREATE TRIGGER IF NOT EXISTS fkdc_acl_memberships_aro_name_1_acl_aro_name
BEFORE DELETE ON acl_aro
FOR EACH ROW BEGIN
    DELETE FROM acl_memberships WHERE acl_memberships.aro_name_1 = OLD.name;
END;

-- Foreign Key Preventing insert
CREATE TRIGGER IF NOT EXISTS fki_acl_memberships_aro_name_2_acl_aro_name
BEFORE INSERT ON [acl_memberships]
FOR EACH ROW BEGIN
  SELECT RAISE(ROLLBACK, 'insert on table "acl_memberships" violates foreign key constraint "fki_acl_memberships_aro_name_2_acl_aro_name"')
  WHERE NEW.aro_name_2 IS NOT NULL AND (SELECT name FROM acl_aro WHERE name = NEW.aro_name_2) IS NULL;
END;

-- Foreign key preventing update
CREATE TRIGGER IF NOT EXISTS fku_acl_memberships_aro_name_2_acl_aro_name
BEFORE UPDATE ON [acl_memberships]
FOR EACH ROW BEGIN
    SELECT RAISE(ROLLBACK, 'update on table "acl_memberships" violates foreign key constraint "fku_acl_memberships_aro_name_2_acl_aro_name"')
      WHERE NEW.aro_name_2 IS NOT NULL AND (SELECT name FROM acl_aro WHERE name = NEW.aro_name_2) IS NULL;
END;

-- Cascading Delete
CREATE TRIGGER IF NOT EXISTS fkdc_acl_memberships_aro_name_2_acl_aro_name
BEFORE DELETE ON acl_aro
FOR EACH ROW BEGIN
    DELETE FROM acl_memberships WHERE acl_memberships.aro_name_2 = OLD.name;
END;

-- Foreign Key Preventing insert
CREATE TRIGGER IF NOT EXISTS fki_acl_access_aro_name_acl_aro_name
BEFORE INSERT ON [acl_access]
FOR EACH ROW BEGIN
  SELECT RAISE(ROLLBACK, 'insert on table "acl_access" violates foreign key constraint "fki_acl_access_aro_name_acl_aro_name"')
  WHERE NEW.aro_name IS NOT NULL AND (SELECT name FROM acl_aro WHERE name = NEW.aro_name) IS NULL;
END;

-- Foreign key preventing update
CREATE TRIGGER IF NOT EXISTS fku_acl_access_aro_name_acl_aro_name
BEFORE UPDATE ON [acl_access]
FOR EACH ROW BEGIN
    SELECT RAISE(ROLLBACK, 'update on table "acl_access" violates foreign key constraint "fku_acl_access_aro_name_acl_aro_name"')
      WHERE NEW.aro_name IS NOT NULL AND (SELECT name FROM acl_aro WHERE name = NEW.aro_name) IS NULL;
END;

-- Cascading Delete
CREATE TRIGGER IF NOT EXISTS fkdc_acl_access_aro_name_acl_aro_name
BEFORE DELETE ON acl_aro
FOR EACH ROW BEGIN
    DELETE FROM acl_access WHERE acl_access.aro_name = OLD.name;
END;

-- Foreign Key Preventing insert
CREATE TRIGGER IF NOT EXISTS fki_acl_access_aco_name_acl_aco_name
BEFORE INSERT ON [acl_access]
FOR EACH ROW BEGIN
  SELECT RAISE(ROLLBACK, 'insert on table "acl_access" violates foreign key constraint "fki_acl_access_aco_name_acl_aco_name"')
  WHERE NEW.aco_name IS NOT NULL AND (SELECT name FROM acl_aco WHERE name = NEW.aco_name) IS NULL;
END;

-- Foreign key preventing update
CREATE TRIGGER IF NOT EXISTS fku_acl_access_aco_name_acl_aco_name
BEFORE UPDATE ON [acl_access]
FOR EACH ROW BEGIN
    SELECT RAISE(ROLLBACK, 'update on table "acl_access" violates foreign key constraint "fku_acl_access_aco_name_acl_aco_name"')
      WHERE NEW.aco_name IS NOT NULL AND (SELECT name FROM acl_aco WHERE name = NEW.aco_name) IS NULL;
END;

-- Cascading Delete
CREATE TRIGGER IF NOT EXISTS fkdc_acl_access_aco_name_acl_aco_name
BEFORE DELETE ON acl_aco
FOR EACH ROW BEGIN
    DELETE FROM acl_access WHERE acl_access.aco_name = OLD.name;
END;
