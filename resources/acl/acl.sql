/* Access Request Object - What is requesting access */
CREATE TABLE IF NOT EXISTS acl_aro (
	name TEXT NOT NULL,
	type VARCHAR(10) NOT NULL, /* user, group */

	PRIMARY KEY (name)
);

/* User hostmasks - acl_aro <1:N> acl_user_hostmasks */
CREATE TABLE IF NOT EXISTS acl_user_hostmasks (
	aro_name INTEGER CONSTRAINT fk_aro_name REFERENCES acl_aro(name) ON DELETE CASCADE,
	hostmask TEXT,

	PRIMARY KEY (aro_name, hostmask)
);

/* Group memberships - acl_aro <N:N> acl_aro */
CREATE TABLE IF NOT EXISTS acl_memberships (
	aro_name_1 INTEGER CONSTRAINT fk_aro_name_1 REFERENCES acl_aro(name) ON DELETE CASCADE,
	aro_name_2 INTEGER CONSTRAINT fk_aro_name_2 REFERENCES acl_aro(name) ON DELETE CASCADE,

	PRIMARY KEY (aro_name_1, aro_name_2)
);

/* Access Control Objects - What we request access to */
CREATE TABLE IF NOT EXISTS acl_aco (
	name TEXT NOT NULL,

	PRIMARY KEY (name)
);

CREATE TABLE IF NOT EXISTS acl_access (
	aro_name INTEGER CONSTRAINT fk_aro_name REFERENCES acl_aro(name) ON DELETE CASCADE,
	aco_name INTEGER CONSTRAINT fk_aco_name REFERENCES acl_aco(name) ON DELETE CASCADE,
	access INTEGER NOT NULL, /* 1 = allow, 0 = deny */

	PRIMARY KEY (aro_name, aco_name)
);

/* Views */
CREATE VIEW IF NOT EXISTS list_access AS
SELECT acl_aro.name as aro_name, acl_memberships.aro_name_1 as username, acl_memberships.aro_name_2 as groupname, acl_access.aco_name AS context,acl_user_hostmasks.hostmask AS hostmask FROM 
	acl_aro,
	acl_access,
	acl_user_hostmasks 
LEFT JOIN acl_memberships ON acl_memberships.aro_name_2 = acl_aro.name
WHERE 
	(
			(
				acl_access.aro_name = acl_aro.name AND acl_aro.type = 'group'
				AND (acl_user_hostmasks.aro_name = acl_memberships.aro_name_1)
			)
			OR 
			(
				acl_access.aro_name = acl_aro.name AND acl_aro.type = 'user'
				AND acl_user_hostmasks.aro_name = acl_aro.name 
				AND acl_access.aro_name = acl_user_hostmasks.aro_name
			)
	)
	GROUP BY acl_user_hostmasks.hostmask, acl_access.aco_name HAVING acl_access.access = 1
;

CREATE VIEW IF NOT EXISTS user_hostmasks AS
SELECT acl_aro.name as username, acl_user_hostmasks.hostmask as hostmask FROM acl_aro,acl_user_hostmasks WHERE type = 'user' AND acl_aro.name = acl_user_hostmasks.aro_name;

CREATE VIEW IF NOT EXISTS user_groups AS
SELECT acl_aro.name as username, acl_memberships.aro_name_2 as groupname FROM acl_aro,acl_memberships WHERE acl_aro.type = 'user' AND acl_aro.name = acl_memberships.aro_name_1;
