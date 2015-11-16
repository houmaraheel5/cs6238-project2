CREATE TABLE document (
      id text PRIMARY KEY NOT NULL,
      integrity_flag integer(1) DEFAULT(0),
      confidentiality_flag integer(1) DEFAULT(0),
      owner_uid text(128) NOT NULL
);

CREATE TABLE document_access (
      uid text(128) NOT NULL,
      document_id text(128) NOT NULL,
      until datetime(128),
      read integer(1) NOT NULL DEFAULT(0),
      write integer(1) NOT NULL DEFAULT(0),
      PRIMARY KEY(uid, document_id)
);

CREATE TABLE document_owner (
      uid text(128) NOT NULL,
      document_id text(128) NOT NULL,
      until datetime(128),
      PRIMARY KEY(uid, document_id)
);

CREATE TABLE users (
      uid text PRIMARY KEY NOT NULL
);
